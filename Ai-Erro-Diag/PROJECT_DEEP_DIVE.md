# PROJECT DEEP DIVE — AI Error Diagnosis System

> **Complete technical reference for developers maintaining and extending this codebase.**
> Generated: 2026-06-14 | Repository: `/home/hvt/Documents/ai-error-diagnosis`

---

## TABLE OF CONTENTS

1. [Project Overview](#1-project-overview)
2. [Complete Tech Stack](#2-complete-tech-stack)
3. [Folder Structure Breakdown](#3-folder-structure-breakdown)
4. [File-by-File Analysis](#4-file-by-file-analysis)
5. [Function Reference](#5-function-reference)
6. [Request Flow Analysis](#6-request-flow-analysis)
7. [Gemini Integration](#7-gemini-integration)
8. [RAG System Deep Dive](#8-rag-system-deep-dive)
9. [PDF Generation System](#9-pdf-generation-system)
10. [API Documentation](#10-api-documentation)
11. [Frontend Analysis](#11-frontend-analysis)
12. [Testing Analysis](#12-testing-analysis)
13. [Security Analysis](#13-security-analysis)
14. [Performance Analysis](#14-performance-analysis)
15. [Maintenance Guide](#15-maintenance-guide)
16. [Learning Guide](#16-learning-guide)
17. [Future Improvements](#17-future-improvements)

---

## 1. PROJECT OVERVIEW

### What Problem This Application Solves

Developers routinely encounter cryptic error messages in terminals, IDEs, browsers, and CI/CD logs. Diagnosing the root cause requires:
1. Understanding the error type
2. Knowing the language/framework context
3. Researching similar past issues
4. Synthesising a fix

This application **automates all four steps** using AI. A developer takes a screenshot of the error, uploads it, and receives a structured diagnosis with root cause, step-by-step fix, prevention tips, and a downloadable PDF report — in under 30 seconds.

### Business Use Case

| Use Case | Description |
|---|---|
| Developer productivity | Reduce time-to-fix from hours to seconds |
| Team knowledge sharing | PDF reports can be shared with teammates |
| Onboarding | Junior devs get expert-level diagnoses for errors they have never seen |
| Documentation | Archived PDF reports build institutional debugging knowledge |
| Code review | Attach diagnosis reports to PRs as evidence of error investigation |

### User Workflow

```
1. Developer encounters a software error in any tool (IDE, terminal, browser, Docker)
2. Takes a screenshot (PNG/JPG/JPEG/WEBP, max 10 MB)
3. Visits http://localhost:8000
4. Drags & drops the screenshot onto the upload zone
5. Clicks "Analyse Error"
6. Waits ~15-25 seconds while the AI pipeline runs
7. Views the Results page with:
   - Error summary
   - Root cause
   - Confidence score (0–100%)
   - Recommended fix
   - Step-by-step solution
   - Prevention tips
   - Related errors
   - Knowledge base matches
8. Downloads the PDF report
```

### System Workflow

```
Screenshot Upload
      │
      ▼
validate_upload()          ← Extension + content-type + size checks
      │
      ▼
save_upload()              ← UUID filename, saved to uploads/
      │
      ▼
GeminiVisionService        ← PIL opens image → Gemini Vision API
.analyse_screenshot()         → Extracts: error_title, error_message,
                                language, framework, environment,
                                raw_stacktrace → VisionAnalysisResult
      │
      ▼
EmbeddingService           ← SentenceTransformer all-MiniLM-L6-v2
.embed(query)                 → 384-dim float32 numpy vector
      │
      ▼
FAISSService               ← Flat L2 index search
.search(vector, top_k=5)      → Top-5 similar error records
                                + similarity_score per record
      │
      ▼
RetrievalService           ← Wraps above into RetrievedError schemas
.retrieve(query)
      │
      ▼
build_diagnosis_prompt()   ← Combines VisionAnalysisResult + retrieved
                              errors into a structured prompt
      │
      ▼
GeminiDiagnosisService     ← Gemini text generation API
.generate_diagnosis()         → DiagnosisResult (root_cause,
                                confidence_score, step_by_step_solution,
                                prevention_tips, related_errors)
      │
      ▼
PDFGenerator               ← ReportLab builds A4 PDF with all sections
.generate()                   → Saved to reports/<report_id>.pdf
      │
      ▼
DiagnoseResponse           ← JSON: report_id, vision_analysis,
                              retrieved_errors, diagnosis, pdf_url
      │
      ▼
Frontend (results.js)      ← Reads sessionStorage → renders all cards
                              + confidence bar + KB entries + PDF link
```

### Why Gemini Vision Was Chosen

- **Multimodal capability**: natively understands image + text in a single API call
- **OCR + semantic understanding**: does not just OCR text — it contextualises the error within the visible IDE/terminal theme
- **Free tier availability**: `gemini-1.5-flash` is available at no cost with generous rate limits
- **JSON-mode compatible**: responds with structured JSON when instructed, enabling schema validation
- **Context window**: 1M token context enables long stack traces in the prompt

### Why RAG Was Used

Without RAG, Gemini would rely solely on its training data. RAG solves three problems:
1. **Domain-specific knowledge**: the knowledge base contains curated solutions for known error patterns that may differ from generic web answers
2. **Confidence grounding**: retrieved similar errors give Gemini concrete examples to reason from, improving accuracy
3. **Hallucination reduction**: anchoring the diagnosis to retrieved facts reduces fabricated solutions
4. **Updatable without retraining**: adding new error records and rebuilding the FAISS index updates the system instantly

### Why FAISS Was Used

- **Speed**: FAISS searches 23 records (or 1M+) in microseconds using optimised C++ under the hood
- **Exact nearest-neighbour**: `IndexFlatL2` guarantees the true top-K results, important for correctness
- **Zero infrastructure**: no database server needed — the index is a single binary file on disk
- **Python-native**: `faiss-cpu` installs via pip with no compilation required
- **Persistence**: `faiss.write_index` / `faiss.read_index` handles serialisation transparently

### Why Sentence Transformers Were Used

- **`all-MiniLM-L6-v2`**: 22M parameter model producing 384-dim embeddings — extremely fast, small (~80 MB), high-quality
- **Semantic similarity**: unlike keyword search, embeddings capture *meaning*. "module not installed" and "package missing" map to similar vectors
- **Local inference**: runs entirely on CPU, no external API call needed during retrieval
- **HuggingFace ecosystem**: widely supported, well-documented, stable API

### Why FastAPI Was Chosen

- **Async-first**: `async def` endpoints are idiomatic; integrates naturally with Python's asyncio ecosystem
- **Auto-documentation**: Swagger UI at `/docs` and ReDoc at `/redoc` are generated automatically from Pydantic schemas — zero manual effort
- **Pydantic integration**: request/response validation, serialisation, and documentation all come from a single model definition
- **Type safety**: full Python type hints throughout, enabling IDE autocompletion and static analysis
- **ASGI standard**: runs on Uvicorn/Hypercorn for production-grade concurrency
- **Dependency injection**: `Depends()` enables clean service wiring and easy test overrides

---

## 2. COMPLETE TECH STACK

| Technology | Version | Purpose | Where Used | Benefits | Alternatives |
|---|---|---|---|---|---|
| **FastAPI** | 0.115.6 | Web framework, API routing, DI | `app/main.py`, `app/api/router.py` | Auto-docs, async, Pydantic integration | Flask, Django, Litestar |
| **Uvicorn** | 0.32.1 | ASGI server | Entry point: `uvicorn app.main:app` | High-performance, ASGI-compliant | Hypercorn, Daphne |
| **Python-multipart** | 0.0.20 | Multipart form data parsing | File uploads in FastAPI | Required for `UploadFile` | Built into Flask |
| **Pydantic** | 2.10.4 | Data validation & serialisation | `app/schemas/diagnosis.py` | Type enforcement, JSON schema generation | Marshmallow, attrs |
| **Pydantic-settings** | 2.7.0 | Environment variable loading | `app/core/config.py` | `.env` file + env var merging | python-dotenv + manual |
| **Google GenerativeAI** | 0.8.3 | Gemini Vision + Diagnosis API | `app/services/gemini_*.py` | Multimodal, free tier, large context | OpenAI GPT-4V, Claude Vision |
| **Sentence Transformers** | 3.3.1 | Text embedding generation | `app/rag/embedding_service.py` | Semantic similarity, local inference | OpenAI embeddings, Cohere |
| **FAISS-CPU** | 1.9.0 | Vector similarity search | `app/rag/faiss_service.py` | Microsecond search, no server | ChromaDB, Pinecone, Qdrant |
| **ReportLab** | 4.2.5 | PDF generation | `app/pdf/report_generator.py` | Full layout control, table/image support | WeasyPrint, fpdf2 |
| **Pillow** | 11.1.0 | Image I/O for Gemini + PDF | `gemini_vision.py`, `report_generator.py` | PIL compatibility, format support | imageio, OpenCV |
| **Python-dotenv** | 1.0.1 | `.env` file parsing | Loaded by pydantic-settings | Simple key=value env files | direnv |
| **HTTPX** | 0.28.1 | Async HTTP client | Test client backbone | Async-native, FastAPI TestClient compatible | requests, aiohttp |
| **Aiofiles** | 24.1.0 | Async file I/O | Available for async file ops | Non-blocking file writes | sync I/O in thread |
| **Jinja2** | 3.1.5 | HTML template rendering | `app/main.py` for serving HTML pages | FastAPI `TemplatingResponse` integration | Mako, Chameleon |
| **HTML5** | — | Page structure | `app/templates/*.html` | Semantic elements, accessibility | — |
| **Vanilla CSS** | — | Styling | `app/static/css/*.css` | No build step, glassmorphism design | Tailwind, Bootstrap |
| **Vanilla JavaScript** | — | Frontend logic | `app/static/js/*.js` | No framework dependency | React, Vue |
| **pytest** | 8.3.4 | Test runner | `tests/` | Fixtures, parametrize, plugins | unittest, nose |
| **pytest-asyncio** | 0.25.0 | Async test support | `tests/test_services.py`, etc. | `@pytest.mark.asyncio` decorator | anyio |
| **pytest-cov** | 6.0.0 | Code coverage reporting | All tests via `pytest.ini` addopts | `--cov-fail-under=80` threshold | coverage.py |
| **Python logging** | stdlib | Structured logging | `app/core/logging.py` | Emoji prefixes, level control | structlog, loguru |
| **python-dotenv / .env** | — | Secrets management | `.env` file, never committed | No hardcoded secrets | Vault, AWS Secrets Manager |


---

## 3. FOLDER STRUCTURE BREAKDOWN

```
ai-error-diagnosis/
├── .env                    ← Runtime secrets (gitignored)
├── .env.example            ← Template for new developers
├── requirements.txt        ← All pinned Python dependencies
├── pytest.ini              ← pytest + coverage configuration
├── README.md               ← Project documentation
├── agent-state.md          ← Build phase tracker (AI agent state)
├── project.md              ← Original project specification (COSTAR)
├── skills.md               ← Engineering principles enforced
├── app/                    ← Main Python package
│   ├── __init__.py
│   ├── main.py             ← FastAPI app factory + lifespan
│   ├── api/                ← HTTP layer (routing only)
│   │   └── router.py
│   ├── core/               ← Cross-cutting concerns
│   │   ├── config.py       ← Environment settings
│   │   ├── logging.py      ← Structured logging
│   │   └── dependencies.py ← FastAPI DI providers
│   ├── models/             ← Reserved for ORM models (empty)
│   ├── schemas/            ← Pydantic I/O contracts
│   │   └── diagnosis.py
│   ├── services/           ← External AI integrations
│   │   ├── gemini_vision.py
│   │   └── gemini_diagnosis.py
│   ├── rag/                ← Retrieval-Augmented Generation
│   │   ├── embedding_service.py
│   │   ├── faiss_service.py
│   │   ├── retrieval_service.py
│   │   └── index_builder.py
│   ├── prompts/            ← Prompt engineering layer
│   │   └── templates.py
│   ├── pdf/                ← Report generation
│   │   └── report_generator.py
│   ├── utils/              ← Shared utilities
│   │   └── file_handler.py
│   ├── templates/          ← Jinja2 HTML templates
│   │   ├── index.html
│   │   └── results.html
│   └── static/             ← Browser-served assets
│       ├── css/main.css
│       ├── css/results.css
│       ├── js/upload.js
│       └── js/results.js
├── data/errors/            ← Knowledge base JSON files
│   ├── python_errors.json      (8 records)
│   ├── fastapi_errors.json     (5 records)
│   ├── javascript_errors.json  (5 records)
│   └── database_errors.json    (5 records)
├── faiss_index/            ← Built at runtime by index_builder
│   ├── errors.index        ← FAISS binary index (384-dim, 23 vectors)
│   └── metadata.json       ← Parallel metadata for each vector
├── reports/                ← Generated PDF files (runtime)
├── uploads/                ← Uploaded screenshots (runtime)
└── tests/
    ├── conftest.py         ← Shared fixtures
    ├── test_api.py         ← Endpoint tests
    ├── test_rag.py         ← RAG pipeline tests
    ├── test_services.py    ← Gemini service tests
    ├── test_pdf.py         ← PDFGenerator tests
    └── test_validation.py  ← File handler tests
```

### Folder Responsibilities

| Folder | Purpose | Depends On | Used By |
|---|---|---|---|
| `app/core/` | App-wide config, logging, DI wiring | `pydantic-settings`, stdlib logging | Every module |
| `app/api/` | HTTP endpoints only — no business logic | `app/core/`, `app/schemas/`, `app/services/`, `app/rag/`, `app/pdf/`, `app/utils/` | `app/main.py` |
| `app/schemas/` | Pydantic models — the single source of truth for data shapes | `pydantic` | `app/api/`, `app/services/`, `app/rag/`, `app/pdf/`, `app/prompts/` |
| `app/services/` | Gemini API calls — external I/O isolation | `app/schemas/`, `app/prompts/`, `google-generativeai`, `PIL` | `app/api/router.py` |
| `app/rag/` | Embedding + vector search pipeline | `sentence-transformers`, `faiss-cpu`, `app/schemas/` | `app/api/router.py`, `app/core/dependencies.py` |
| `app/prompts/` | All prompt strings — separated for maintainability | `app/schemas/` | `app/services/gemini_*.py` |
| `app/pdf/` | ReportLab PDF generation | `reportlab`, `app/schemas/` | `app/api/router.py` |
| `app/utils/` | Upload I/O utilities | `fastapi.UploadFile`, stdlib | `app/api/router.py` |
| `app/templates/` | Jinja2 HTML pages served by FastAPI | Static files | `app/main.py` |
| `app/static/` | CSS + JS assets | None | Browser |
| `data/errors/` | Knowledge base source of truth (human-editable JSON) | None | `app/rag/index_builder.py` |
| `faiss_index/` | Compiled vector index (binary artefact) | Built from `data/errors/` | `app/rag/faiss_service.py` |

---

## 4. FILE-BY-FILE ANALYSIS

---

### `app/main.py`

**Purpose:** FastAPI application factory. Wires together all layers on startup.

**Key Responsibilities:**
- Configures logging on module import
- Defines the `lifespan` async context manager (startup/shutdown hooks)
- Creates the `FastAPI()` instance with OpenAPI metadata
- Adds `CORSMiddleware` (permissive in dev, restrictive in prod)
- Mounts `/static` directory for CSS/JS assets
- Registers `Jinja2Templates` for HTML rendering
- Includes the API router at prefix `/api/v1`
- Registers two frontend routes: `GET /` and `GET /results`
- Registers a global exception handler that catches all unhandled exceptions and returns a sanitised 500 JSON response (prevents stack traces leaking to clients)

**Execution Flow:**
```
Module load → get_settings() → configure_logging()
                              → lifespan defined
App created → middleware added → static mounted → router included → routes added
On request → middleware → router → endpoint → response
```

**Design Decisions:**
- `lifespan` uses `asynccontextmanager` (new FastAPI pattern, replaces deprecated `startup`/`shutdown` events)
- CORS is `allow_origins=["*"]` in development but `[]` (deny all) in production — controlled by `APP_ENV` env var
- The global exception handler logs the full error server-side but only returns a generic message to the client (security)

---

### `app/core/config.py`

**Purpose:** Single source of truth for all application configuration. No settings are ever defined in more than one place.

**Class: `Settings(BaseSettings)`**

Uses `pydantic-settings` to load values from `.env` file and environment variables automatically.

| Field | Type | Default | Description |
|---|---|---|---|
| `gemini_api_key` | `str` | *required* | Google Gemini API key — must be set |
| `gemini_vision_model` | `str` | `gemini-1.5-flash` | Model for vision analysis |
| `gemini_diagnosis_model` | `str` | `gemini-1.5-flash` | Model for text diagnosis |
| `app_env` | `str` | `development` | Controls CORS and logging behaviour |
| `app_host` | `str` | `0.0.0.0` | Bind address |
| `app_port` | `int` | `8000` | Bind port |
| `log_level` | `str` | `INFO` | Logging verbosity |
| `max_upload_size_mb` | `int` | `10` | Maximum upload size in MB |
| `uploads_dir` | `Path` | `uploads` | Directory for saved uploads |
| `reports_dir` | `Path` | `reports` | Directory for generated PDFs |
| `faiss_index_path` | `Path` | `faiss_index/errors.index` | FAISS binary index file |
| `faiss_metadata_path` | `Path` | `faiss_index/metadata.json` | Vector metadata JSON |
| `embedding_model` | `str` | `all-MiniLM-L6-v2` | Sentence Transformer model |
| `top_k_results` | `int` | `5` | Number of FAISS search results |
| `knowledge_base_dir` | `Path` | `data/errors` | Knowledge base JSON directory |

**Properties:**
- `max_upload_size_bytes` → converts `max_upload_size_mb` to bytes

**Methods:**
- `ensure_directories()` → creates `uploads/`, `reports/`, `faiss_index/` at startup if missing

**`get_settings()` function:**
- Decorated with `@lru_cache(maxsize=1)` — the `Settings` object is instantiated exactly once and cached for the process lifetime
- `lru_cache` works here because `get_settings` takes no arguments (the Settings object itself is the singleton)

---

### `app/core/logging.py`

**Purpose:** Configures Python's standard `logging` module with a custom emoji-prefixed formatter for human-friendly console output.

**Class: `_PrefixFormatter`**

Custom `logging.Formatter` subclass that prepends emoji + module name to every log record:
- DEBUG → 🔍
- INFO → ℹ️
- WARNING → ⚠️
- ERROR → ❌
- CRITICAL → 🔥

**`configure_logging(level)`**
- Creates a single `StreamHandler` pointing to `stdout`
- Applies `_PrefixFormatter` with timestamp `%Y-%m-%d %H:%M:%S`
- Clears any existing handlers before adding the new one (prevents duplicate logs on hot-reload)
- Silences noisy third-party loggers: `httpx`, `httpcore`, `sentence_transformers`, `faiss` (set to WARNING)

**`get_logger(name)`**
- Simple wrapper: returns `logging.getLogger(name)`
- Called as `logger = get_logger(__name__)` in every module

---

### `app/core/dependencies.py`

**Purpose:** FastAPI dependency injection providers. Implements the Service Locator pattern via `Depends()`.

**Critical Design Decision — The Singleton Cache:**

`pydantic` `BaseSettings` objects are **unhashable** (they contain mutable fields and computed properties). If you use `@lru_cache` on a function that takes a `Settings` argument, Python raises `TypeError: unhashable type: 'Settings'`.

The solution implemented here uses **module-level singleton dictionaries** keyed by primitive string values:

```python
_embedding_cache: dict[str, EmbeddingService] = {}
_faiss_cache: dict[str, FAISSService] = {}
```

This guarantees exactly one `EmbeddingService` per model name and one `FAISSService` per index path, without needing `lru_cache`.

**Dependency Providers:**

| Function | Returns | Cached By |
|---|---|---|
| `get_embedding_service(settings)` | `EmbeddingService` | `_embedding_cache[model_name]` |
| `get_faiss_service(settings)` | `FAISSService` | `_faiss_cache[str(index_path)]` |
| `get_retrieval_service(embedding, faiss, settings)` | `RetrievalService` | Not cached (lightweight composition) |
| `get_vision_service(settings)` | `GeminiVisionService` | Not cached (stateless SDK wrapper) |
| `get_diagnosis_service(settings)` | `GeminiDiagnosisService` | Not cached (stateless SDK wrapper) |

**Why Not Cache Vision/Diagnosis Services?**

These services call `genai.configure(api_key=...)` and `genai.GenerativeModel(...)` on every construction. They hold no in-memory state (no model weights loaded locally), so caching provides no meaningful benefit. The SDK manages its own connection pooling.

---

### `app/schemas/diagnosis.py`

**Purpose:** Pydantic v2 data models that define the exact shape of all data flowing through the system. These models serve triple duty: validation, serialisation, and OpenAPI documentation.

**Models:**

**`VisionAnalysisResult`** — output from Gemini Vision:
```
error_title: str       — "ModuleNotFoundError: No module named 'fastapi'"
error_message: str     — Complete error text
language: str          — "Python"
framework: str         — "FastAPI"
environment: str       — "Linux terminal"
raw_stacktrace: str    — Full stack trace text
```

**`RetrievedError`** — a single result from FAISS knowledge base search:
```
error_name: str
description: str
root_cause: str
solution: str
troubleshooting_steps: list[str]
similarity_score: float  — ge=0.0, le=1.0 (Pydantic constraint)
```

**`DiagnosisResult`** — output from Gemini Diagnosis:
```
error_summary: str
root_cause: str
confidence_score: float  — ge=0.0, le=1.0
recommended_fix: str
step_by_step_solution: list[str]
prevention_tips: list[str]
related_errors: list[str]
```

**`DiagnoseResponse`** — the full JSON response from `POST /diagnose`:
```
report_id: str
vision_analysis: VisionAnalysisResult
retrieved_errors: list[RetrievedError]
diagnosis: DiagnosisResult
pdf_url: str
```

**`UploadResponse`** — response from `POST /upload`:
```
filename: str
image_path: str
message: str
```

**`HealthResponse`** — response from `GET /health`:
```
status: str
version: str
environment: str
```

**`ErrorResponse`** — standardised error body:
```
detail: str
error_code: str = "INTERNAL_ERROR"
```

---

### `app/api/router.py`

**Purpose:** Implements all four HTTP endpoints. This file contains **only routing logic** — no business logic, no direct model calls. Every action is delegated to injected services.

**Endpoints:**

1. `GET /api/v1/health` → returns `HealthResponse`
2. `POST /api/v1/upload` → validates + saves file → returns `UploadResponse`
3. `POST /api/v1/diagnose` → full AI pipeline → returns `DiagnoseResponse`
4. `GET /api/v1/report/{report_id}` → streams PDF file

**`diagnose_screenshot` Pipeline (the critical path):**
```python
# Step 1: Validate + save file
validate_upload(file, max_bytes)
image_path = await save_upload(file, uploads_dir, max_bytes)

# Step 2: Gemini Vision
vision_result = await vision_service.analyse_screenshot(image_path)

# Step 3: RAG retrieval
query = f"{vision_result.error_title} {vision_result.error_message}"
retrieved_errors = retrieval_service.retrieve(query)

# Step 4: Gemini Diagnosis (RAG-augmented)
diagnosis = await diagnosis_service.generate_diagnosis(vision_result, retrieved_errors)

# Step 5: PDF generation
report_id = uuid.uuid4().hex
pdf_path = pdf_gen.generate(report_id, image_path, vision_result, diagnosis)

# Step 6: Return full response
return DiagnoseResponse(report_id, vision_result, retrieved_errors, diagnosis, pdf_url)
```

**Path Traversal Protection in `download_report`:**
```python
safe_id = "".join(c for c in report_id if c.isalnum() or c in ("-", "_"))
```
This strips any `../` or filesystem-traversal characters before constructing the PDF path.

**Error Handling Strategy:**
- `FileNotFoundError`, `ValueError` from vision → HTTP 400
- `RuntimeError` from vision/diagnosis → HTTP 500
- PDF failure → logs error, sets `pdf_url = ""` (non-fatal, diagnosis still returned)

---

### `app/services/gemini_vision.py`

**Purpose:** Encapsulates all Gemini Vision API interactions. Takes an image file path, calls the API, parses the response.

**Class: `GeminiVisionService`**

```python
__init__(api_key, model_name="gemini-1.5-flash")
```
- Validates API key (raises `ValueError` if empty)
- Calls `genai.configure(api_key=...)` — this is a global SDK setting
- Creates `genai.GenerativeModel` with `VISION_SYSTEM_PROMPT` as system instruction

```python
async analyse_screenshot(image_path: Path) -> VisionAnalysisResult
```
- Validates file existence and extension
- Opens image with `PIL.Image.open()`
- Sends `[VISION_USER_PROMPT, image]` to `generate_content()` with `temperature=0.1` (low for deterministic extraction)
- Parses response with `_parse_vision_response()`

```python
_parse_vision_response(raw_text: str) -> VisionAnalysisResult
```
- Strips markdown code fences (` ```json ... ``` `) with regex
- Parses JSON with `json.loads()`
- Raises `ValueError` on invalid JSON
- Constructs `VisionAnalysisResult` with safe `.get()` defaults

**Why `temperature=0.1` for Vision?**

Extraction tasks require determinism — we want the model to reliably copy text from the image, not creatively interpret it. Low temperature forces the model to commit to the most probable tokens.

---

### `app/services/gemini_diagnosis.py`

**Purpose:** Generates expert diagnoses by combining extracted error info with RAG context.

**Class: `GeminiDiagnosisService`**

```python
async generate_diagnosis(
    vision_result: VisionAnalysisResult,
    retrieved_errors: list[RetrievedError]
) -> DiagnosisResult
```
- Calls `build_diagnosis_prompt()` to assemble the augmented prompt
- Sends to Gemini with `temperature=0.2`, `max_output_tokens=4096`
- Parses response with `_parse_diagnosis_response()`

**Why `temperature=0.2` for Diagnosis?**

Slightly higher than vision (0.1) to allow the model to synthesise creative but still grounded solutions. Too high (>0.5) risks hallucination; too low prevents adaptive reasoning.

**Confidence Score Clamping:**
```python
raw_score = float(data.get("confidence_score", 0.7))
confidence = max(0.0, min(1.0, raw_score))
```
Gemini sometimes returns values outside [0,1]. This clamp ensures the Pydantic schema constraint (`ge=0.0, le=1.0`) is never violated.

---

### `app/rag/embedding_service.py`

**Purpose:** Wraps SentenceTransformer to provide typed, validated embedding generation.

**Class: `EmbeddingService`**

```python
embed(text: str) -> np.ndarray  # shape: (384,)
embed_batch(texts: list[str]) -> np.ndarray  # shape: (N, 384)
dimension: int  # property → 384 for all-MiniLM-L6-v2
```

**Key Implementation Details:**
- `self._model = SentenceTransformer(model_name)` — loads model into RAM on init (~80 MB)
- `convert_to_numpy=True` ensures float32 numpy arrays (required by FAISS)
- `show_progress_bar=False` for batch embedding (suppress tqdm in production)
- Raises `ValueError` for empty/whitespace text — prevents silent zero-vector bugs

**The `all-MiniLM-L6-v2` Model:**
- Architecture: 6-layer MiniLM (distilled from BERT)
- Output: 384-dimensional dense vector
- Max sequence length: 256 tokens (~190 words)
- Speed: ~14k sentences/second on CPU
- Quality: 80%+ of BERT-large performance at 1/6 the size

---

### `app/rag/faiss_service.py`

**Purpose:** Manages the FAISS vector index lifecycle — build, persist, load, search.

**Class: `FAISSService`**

```python
__init__(index_path: Path, metadata_path: Path)
```
- Stores paths
- If both files exist → calls `_load_index()` automatically (lazy load on first request after boot)

```python
build_index(embeddings: np.ndarray, metadata: list[dict]) -> None
```
- Validates length parity between embeddings and metadata
- Converts to float32
- Creates `faiss.IndexFlatL2(dimension)` — exact L2 (Euclidean) distance index
- Adds all vectors: `self._index.add(embeddings_f32)`
- Persists to disk

```python
search(query_vector: np.ndarray, top_k: int = 5) -> list[dict]
```
- Reshapes query to `(1, dim)` for FAISS batch API
- Calls `self._index.search(query, k)` → returns `(distances, indices)` arrays
- Converts L2 distance to similarity score: `1.0 / (1.0 + distance)`
  - distance=0 → score=1.0 (identical)
  - distance=∞ → score→0 (completely different)
- Skips `idx == -1` (FAISS returns -1 for empty slots)

**`is_ready` property:**
```python
return self._index is not None and self._index.ntotal > 0
```
This allows `RetrievalService` to gracefully skip retrieval if the index hasn't been built yet.

---

### `app/rag/retrieval_service.py`

**Purpose:** Composes `EmbeddingService` and `FAISSService` into a single retrieval pipeline.

**Class: `RetrievalService`**

```python
retrieve(query: str) -> list[RetrievedError]
```
1. Checks `faiss_service.is_ready` — returns `[]` if not ready (graceful degradation)
2. Embeds the query string
3. Searches FAISS for top-K results
4. Maps raw dicts to `RetrievedError` Pydantic instances
5. Logs warnings for any record that fails schema validation

This is the only place in the codebase where raw FAISS dict results become typed Pydantic objects.

---

### `app/rag/index_builder.py`

**Purpose:** Standalone script that processes knowledge base JSON files and builds the FAISS index. Run once before first use.

**Functions:**

```python
_load_knowledge_base(knowledge_dir: Path) -> list[dict]
```
- Globs all `*.json` files in `data/errors/`
- Validates each file contains a JSON array (not an object)
- Returns flat list of all records

```python
_build_text_for_embedding(record: dict) -> str
```
- Concatenates: `error_name + description + root_cause + solution + troubleshooting_steps`
- This is the text that gets embedded — richer text = better embeddings
- Adding more fields to the concatenation improves retrieval quality

```python
build_index() -> None
```
- Full pipeline: load → embed → build

**Running:**
```bash
python -m app.rag.index_builder
```
The `sys.path.insert(0, ...)` at the top ensures the module can be run from the project root.

---

### `app/prompts/templates.py`

**Purpose:** All prompt strings are defined here as module-level constants and pure functions. This follows the principle that prompts should be **version-controlled, testable, and independently maintainable**.

**`VISION_SYSTEM_PROMPT`**
- Sets Gemini's persona as an "expert software error analyst"
- Lists languages, frameworks, databases, and tools it should recognise
- Gives CRITICAL INSTRUCTIONS: read all text, extract complete message, identify language/framework/environment
- Mandates pure JSON output (no markdown, no explanations)
- Provides the exact JSON schema with all six required keys

**`VISION_USER_PROMPT`**
- Shorter user-turn prompt that reinforces the JSON requirement
- Lists the six expected keys

**`DIAGNOSIS_SYSTEM_PROMPT`**
- Sets Gemini's persona as "Senior Software Engineer and debugging expert"
- Enforces: technically accurate, actionable, confidence-honest
- Provides the exact JSON schema for diagnosis output including `confidence_score` type annotation

**`build_diagnosis_prompt(vision_result, retrieved_errors) -> str`**

This is the most important function in the prompts module. It assembles the RAG-augmented prompt:

```
## ERROR INFORMATION (from screenshot analysis)
Error Title: ...
Error Message: ...
Language: ...
Framework: ...
Environment: ...
Stack Trace: ...

## RELEVANT KNOWLEDGE BASE CONTEXT
[Knowledge Base Entry 1] (similarity: 0.92)
Error: ModuleNotFoundError
Description: ...
Root Cause: ...
Solution: ...
Troubleshooting Steps:
  1. ...
  2. ...

## INSTRUCTIONS
1. Identify the precise root cause...
2. Determine confidence score (0.0–1.0)...
...
Respond ONLY with a valid JSON object...
```

The similarity score is included so Gemini can weight high-similarity retrieved errors more heavily than low-similarity ones.

---

### `app/pdf/report_generator.py`

**Purpose:** Generates professional A4 PDF reports using ReportLab's `Platypus` layout engine.

**Colour Palette (hex constants):**
- `DARK_BG = #1a1a2e` — dark navy (header bar)
- `ACCENT_BLUE = #0f3460` — deep blue (table headers, section headings)
- `HIGHLIGHT = #e94560` — crimson red (title underline, error names)
- `SUCCESS_GREEN = #27ae60` — confidence banner (high)
- `WARNING_AMBER = #f39c12` — confidence banner (medium)
- `ERROR_RED = #e74c3c` — confidence banner (low)

**Class: `PDFGenerator`**

```python
__init__(reports_dir: Path)
```
- Creates `reports_dir` if missing
- Pre-builds all `ParagraphStyle` objects via `_build_styles()`

```python
generate(report_id, image_path, vision_result, diagnosis) -> Path
```
- Creates `SimpleDocTemplate` with A4 pagesize and 20mm margins
- Calls `_build_story()` to assemble the list of ReportLab flowables
- Builds the PDF with `_add_header_footer` callback on every page

**PDF Sections (in order):**
1. Title header (main title + error title + report ID + date)
2. Error screenshot (embedded proportionally at 160×90mm max)
3. Error details table (Language, Framework, Environment, Error Message, Stack Trace)
4. Confidence banner (coloured badge: HIGH/MEDIUM/LOW)
5. Root Cause section
6. Error Summary section
7. Recommended Fix section
8. Step-by-Step Solution (bullet list)
9. Prevention Tips (bullet list)
10. Related Errors (bullet list)
11. Footer note with timestamp and report ID

**Header/Footer (`_add_header_footer`):**
- Drawn using raw `canvas` (ReportLab's low-level PDF primitive API)
- Header: dark navy bar with "AI Error Diagnosis System" + "Confidential — Internal Use Only"
- Footer: accent blue bar with "Page N" + generation date

---

### `app/utils/file_handler.py`

**Purpose:** Upload validation and storage. The only file in the codebase that directly writes user-supplied bytes to disk.

**Constants:**
```python
ALLOWED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
```

**`validate_upload(file, max_bytes) -> None`**
- Checks `file.filename` is not empty
- Checks extension is in `ALLOWED_EXTENSIONS`
- Checks `content_type` is in `ALLOWED_CONTENT_TYPES` (only if provided — header is optional)
- Does NOT check file size here (size is unknown until the body is read)

**`async save_upload(file, uploads_dir, max_bytes) -> Path`**
- Reads entire file body with `await file.read()`
- Validates length == 0 → HTTP 400
- Validates length > max_bytes → HTTP 413
- Generates UUID filename: `{uuid4().hex}{extension}`
- Writes bytes to disk synchronously (aiofiles available but not used — acceptable for current scale)
- Returns the `Path` to the saved file

---
