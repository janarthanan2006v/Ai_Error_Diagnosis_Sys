"""
FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload

The application starts up by:
1. Configuring structured logging.
2. Ensuring runtime directories exist.
3. Registering API routers.
4. Mounting static files and templates.
5. Setting up CORS middleware.
6. Registering global exception handlers.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.router import router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

# ── Bootstrap ─────────────────────────────────────────────────────────────────

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler — startup and shutdown hooks."""
    logger.info("Starting AI Error Diagnosis System (env=%s)", settings.app_env)
    settings.ensure_directories()

    faiss_ready = settings.faiss_index_path.exists()
    if not faiss_ready:
        logger.warning(
            "FAISS index not found at '%s'. "
            "Run: python -m app.rag.index_builder",
            settings.faiss_index_path,
        )
    else:
        logger.info("FAISS index found at '%s'", settings.faiss_index_path)

    yield

    logger.info("Shutting down AI Error Diagnosis System")


# ── App Factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Error Diagnosis System",
    description=(
        "Production-ready AI-powered error diagnosis system. "
        "Upload error screenshots and receive structured root cause analysis, "
        "fix recommendations, and downloadable PDF reports."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ── Static Files & Templates ──────────────────────────────────────────────────

_static_dir = Path(__file__).parent / "static"
_templates_dir = Path(__file__).parent / "templates"

if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

templates = Jinja2Templates(directory=str(_templates_dir))

# ── Include Routers ───────────────────────────────────────────────────────────

app.include_router(router)

# ── Frontend Routes ───────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request) -> HTMLResponse:
    """Serve the upload dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/results", response_class=HTMLResponse, include_in_schema=False)
async def results(request: Request) -> HTMLResponse:
    """Serve the results page."""
    return templates.TemplateResponse("results.html", {"request": request})


# ── Global Exception Handlers ─────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler that prevents stack traces leaking to clients."""
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error_code": "INTERNAL_ERROR"},
    )
