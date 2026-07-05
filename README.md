# AI Error Diagnosis System

> **Upload an error screenshot → Get a structured AI diagnosis + PDF report**

A production-ready, full-stack application that analyses software error screenshots using Google Gemini Vision, retrieves similar historical errors via a FAISS knowledge base, and generates expert troubleshooting recommendations with a downloadable PDF report.

---

## Architecture

```
User Browser
    │
    ▼ POST /api/v1/diagnose (multipart image)
FastAPI Backend (app/main.py)
    │
    ├─▶ validate_upload()          — Type / size validation
    ├─▶ GeminiVisionService        — OCR + structured error extraction
    ├─▶ EmbeddingService           — all-MiniLM-L6-v2 embedding
    ├─▶ FAISSService               — Top-K similarity retrieval
    ├─▶ GeminiDiagnosisService     — RAG-augmented diagnosis generation
    ├─▶ PDFGenerator               — ReportLab PDF report
    └─▶ DiagnoseResponse (JSON)    — Returned to frontend
```

---

## Features

| Feature | Detail |
|---------|--------|
| Screenshot upload | Drag & drop / file picker · PNG, JPG, JPEG, WEBP · max 10 MB |
| Gemini Vision | OCR, error title, message, language, framework, stack trace |
| RAG retrieval | FAISS flat L2 index · 23 knowledge base entries · top-5 results |
| AI diagnosis | Root cause · confidence score · step-by-step fix · prevention tips |
| PDF report | ReportLab · header/footer · screenshot embed · confidence banner |
| REST API | `/upload`, `/diagnose`, `/report/{id}`, `/health` |
| Frontend | Dark glassmorphism UI · drag-and-drop · results dashboard |
| Tests | pytest · >80% coverage target |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.115 · Uvicorn · Python 3.11+ |
| AI | Google Gemini 1.5 Flash |
| RAG | Sentence Transformers (all-MiniLM-L6-v2) · FAISS-CPU |
| PDF | ReportLab 4.2 |
| Frontend | HTML5 · Vanilla CSS · Vanilla JS · Jinja2 |
| Config | pydantic-settings · python-dotenv |
| Tests | pytest · pytest-asyncio · pytest-cov |

---

## Setup

### 1. Clone & Install

```bash
git clone <repo-url>
cd ai-error-diagnosis

# Create a virtual environment (Python 3.11+)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your Google Gemini API key:
nano .env
```

**Required `.env` variable:**

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

All other variables have sensible defaults (see `.env.example`).

### 3. Build the FAISS Knowledge Base Index

This must be run **once** before the first use. It encodes the knowledge base JSON files into a FAISS vector index.

```bash
python -m app.rag.index_builder
```

Expected output:
```
INFO | Starting FAISS index build
INFO | Loaded 23 error records from knowledge base
INFO | Embedding model loaded successfully
INFO | Building FAISS index with 23 vectors (dim=384)
INFO | FAISS index built and saved to faiss_index/errors.index
INFO | FAISS index build complete ✓
```

### 4. Run the Application

```bash
uvicorn app.main:app --reload
```

Open your browser at **http://localhost:8000**

- **UI:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | *(required)* | Google Gemini API key |
| `GEMINI_VISION_MODEL` | `gemini-1.5-flash` | Vision analysis model |
| `GEMINI_DIAGNOSIS_MODEL` | `gemini-1.5-flash` | Diagnosis generation model |
| `APP_ENV` | `development` | Environment (`development`/`production`) |
| `APP_HOST` | `0.0.0.0` | Server bind host |
| `APP_PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Log level (`DEBUG`/`INFO`/`WARNING`/`ERROR`) |
| `MAX_UPLOAD_SIZE_MB` | `10` | Maximum upload file size in MB |
| `UPLOADS_DIR` | `uploads` | Directory for uploaded screenshots |
| `REPORTS_DIR` | `reports` | Directory for generated PDF reports |
| `FAISS_INDEX_PATH` | `faiss_index/errors.index` | FAISS binary index file |
| `FAISS_METADATA_PATH` | `faiss_index/metadata.json` | FAISS metadata JSON |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence Transformer model |
| `TOP_K_RESULTS` | `5` | Number of similar errors to retrieve |
| `KNOWLEDGE_BASE_DIR` | `data/errors` | Knowledge base JSON directory |

---

## API Reference

### POST `/api/v1/upload`

Upload an error screenshot.

**Request:** `multipart/form-data` with `file` field (PNG/JPG/JPEG/WEBP, ≤10 MB)

**Response:**
```json
{
  "filename": "error_screenshot.png",
  "image_path": "uploads/abc123.png",
  "message": "File uploaded successfully. Use /diagnose to analyse the error."
}
```

---

### POST `/api/v1/diagnose`

Run the full AI diagnosis pipeline on an uploaded screenshot.

**Request:** `multipart/form-data` with `file` field

**Response:**
```json
{
  "report_id": "a1b2c3d4...",
  "vision_analysis": {
    "error_title": "ModuleNotFoundError: No module named 'fastapi'",
    "error_message": "...",
    "language": "Python",
    "framework": "FastAPI",
    "environment": "Linux terminal",
    "raw_stacktrace": "..."
  },
  "retrieved_errors": [...],
  "diagnosis": {
    "error_summary": "...",
    "root_cause": "...",
    "confidence_score": 0.92,
    "recommended_fix": "...",
    "step_by_step_solution": ["..."],
    "prevention_tips": ["..."],
    "related_errors": ["..."]
  },
  "pdf_url": "/api/v1/report/a1b2c3d4..."
}
```

---

### GET `/api/v1/report/{report_id}`

Download a previously generated PDF diagnosis report.

**Response:** `application/pdf` file download

---

### GET `/api/v1/health`

Health check endpoint.

**Response:**
```json
{"status": "ok", "version": "1.0.0", "environment": "development"}
```

---

## Project Structure

```
ai-error-diagnosis/
├── .env.example                  — Environment variable template
├── requirements.txt              — Python dependencies
├── pytest.ini                   — pytest + coverage configuration
├── README.md
├── agent-state.md               — Execution state tracker
├── app/
│   ├── main.py                  — FastAPI app factory + lifespan
│   ├── api/
│   │   └── router.py            — All API endpoints
│   ├── core/
│   │   ├── config.py            — pydantic-settings Settings
│   │   ├── logging.py           — Structured logging
│   │   └── dependencies.py      — FastAPI DI providers
│   ├── schemas/
│   │   └── diagnosis.py         — Pydantic request/response models
│   ├── services/
│   │   ├── gemini_vision.py     — Gemini Vision OCR + extraction
│   │   └── gemini_diagnosis.py  — Gemini RAG-augmented diagnosis
│   ├── rag/
│   │   ├── embedding_service.py — SentenceTransformer wrapper
│   │   ├── faiss_service.py     — FAISS index build/search/persist
│   │   ├── retrieval_service.py — Composed embedding + FAISS pipeline
│   │   └── index_builder.py    — Standalone index builder script
│   ├── prompts/
│   │   └── templates.py         — Vision + diagnosis prompt templates
│   ├── pdf/
│   │   └── report_generator.py  — ReportLab PDF generator
│   ├── utils/
│   │   └── file_handler.py      — Upload validation + save utility
│   ├── templates/
│   │   ├── index.html           — Upload dashboard
│   │   └── results.html         — Diagnosis results page
│   └── static/
│       ├── css/main.css         — Dark glassmorphism design
│       ├── css/results.css      — Results grid + confidence bar
│       ├── js/upload.js         — Drag-drop + /diagnose fetch
│       └── js/results.js        — Reads sessionStorage, populates UI
├── data/
│   └── errors/
│       ├── python_errors.json   — 8 Python error records
│       ├── fastapi_errors.json  — 5 FastAPI error records
│       ├── javascript_errors.json — 5 JS error records
│       └── database_errors.json — 5 DB error records
├── faiss_index/                  — Built by index_builder at runtime
├── reports/                      — Generated PDFs stored here
├── uploads/                      — Uploaded screenshots stored here
└── tests/
    ├── conftest.py              — Shared fixtures + test client
    ├── test_api.py              — API endpoint tests
    ├── test_rag.py              — EmbeddingService / FAISS / Retrieval tests
    ├── test_services.py         — GeminiVision + GeminiDiagnosis tests
    ├── test_pdf.py              — PDFGenerator tests
    └── test_validation.py       — file_handler validation tests
```

---

## Running Tests

```bash
# Full test suite with coverage
pytest

# Run only a specific test file
pytest tests/test_rag.py -v

# Skip coverage threshold (useful during development)
pytest --no-cov
```

> **Note:** Tests mock all Gemini API calls. No real `GEMINI_API_KEY` is required to run the test suite.

---

## Knowledge Base

The knowledge base lives in `data/errors/` as JSON files. Each record follows this schema:

```json
{
  "error_name": "ModuleNotFoundError",
  "description": "Python cannot find the requested module.",
  "root_cause": "Package is not installed in the active environment.",
  "solution": "pip install <package-name>",
  "troubleshooting_steps": [
    "Verify the virtual environment is active",
    "Run pip list to check installed packages",
    "Run pip install <package-name>"
  ]
}
```

To add new categories, create a new `<category>_errors.json` file in `data/errors/` and rebuild the index:

```bash
python -m app.rag.index_builder
```

---

## Known Limitations

| Issue | Notes |
|-------|-------|
| Gemini SDK is synchronous | `generate_content()` blocks the event loop. Under high concurrency, consider wrapping with `asyncio.to_thread()`. |
| No retry on Gemini rate limits | Rapid concurrent requests may return HTTP 500. Add `tenacity` retry in a future iteration. |
| No upload cleanup | Old screenshots accumulate in `uploads/`. Consider adding a cleanup task. |
| FAISS Flat L2 index | Suitable for the current 23-record knowledge base. For 100k+ records, switch to `IndexIVFFlat` or `IndexHNSWFlat`. |

---

## Getting a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **Get API Key**
4. Copy the key and set it in your `.env` file

The `gemini-1.5-flash` model used by default is available on the free tier with generous rate limits.
