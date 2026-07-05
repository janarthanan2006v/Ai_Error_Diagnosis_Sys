# AGENT_STATE.md
# AI Error Diagnosis System — Execution State

> **Control Files:** `skills.md` · `project.md` · `AGENT_STATE.md`
> **Entry Point:** `uvicorn app.main:app --reload`
> **Last Updated:** 2026-06-13 · Phase 12 (Final Validation — ready to run)

---

## Current Task

**Phase 12 — Final Validation**
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Build FAISS index (`python -m app.rag.index_builder`)
- [ ] Run test suite (`pytest --cov=app`)
- [ ] Verify app boots (`uvicorn app.main:app --reload`)

---

## Completed Tasks

### Phase 1 — Project Structure ✅
- Created all directories: `app/api`, `app/core`, `app/models`, `app/schemas`, `app/services`, `app/rag`, `app/prompts`, `app/pdf`, `app/utils`, `app/templates`, `app/static`, `data/errors`, `faiss_index`, `reports`, `uploads`, `tests`
- Created all `__init__.py` package files

### Phase 1 — Config & Dependencies ✅
- `.env.example` — all environment variables defined
- `requirements.txt` — all pinned dependencies

### Phase 2 — Core Layer ✅
- `app/core/config.py` — Pydantic-settings Settings class with `get_settings()`
- `app/core/logging.py` — Structured logging with emoji prefixes
- `app/core/dependencies.py` — FastAPI dependency injection providers (**B-001 fixed**)

### Phase 2 — Schemas ✅
- `app/schemas/diagnosis.py` — All Pydantic models:
  - `VisionAnalysisResult`, `RetrievedError`, `DiagnosisResult`
  - `DiagnoseRequest`, `DiagnoseResponse`, `UploadResponse`
  - `HealthResponse`, `ErrorResponse`

### Phase 3 — Knowledge Base ✅
- `data/errors/python_errors.json` — 8 Python error records
- `data/errors/fastapi_errors.json` — 5 FastAPI error records
- `data/errors/javascript_errors.json` — 5 JavaScript error records
- `data/errors/database_errors.json` — 5 Database error records

### Phase 4 — RAG Pipeline ✅
- `app/rag/embedding_service.py` — SentenceTransformer wrapper (embed + batch)
- `app/rag/faiss_service.py` — FAISS index build, search, persist, load
- `app/rag/retrieval_service.py` — Composed retrieval pipeline
- `app/rag/index_builder.py` — Standalone FAISS index builder script

### Phase 5 — Prompt Engineering ✅
- `app/prompts/templates.py` — Vision + Diagnosis system prompts, `build_diagnosis_prompt()`

### Phase 5 — Gemini Services ✅
- `app/services/gemini_vision.py` — `GeminiVisionService.analyse_screenshot()`
- `app/services/gemini_diagnosis.py` — `GeminiDiagnosisService.generate_diagnosis()`

### Phase 6 — Utilities ✅
- `app/utils/file_handler.py` — `validate_upload()` + `save_upload()` with size/type enforcement

### Phase 7 — Gemini Diagnosis ✅
- Integrated into `GeminiDiagnosisService` with RAG context from `build_diagnosis_prompt()`

### Phase 8 — PDF Generator ✅
- `app/pdf/report_generator.py` — `PDFGenerator.generate()` with full ReportLab layout:
  - Title header, screenshot embed, error details table, confidence banner
  - Root cause, summary, fix, step-by-step, prevention tips, related errors
  - Header/footer on every page

### Phase 9 — FastAPI App ✅
- `app/api/router.py` — All 4 endpoints: `POST /upload`, `POST /diagnose`, `GET /report/{id}`, `GET /health`
- `app/main.py` — App factory with lifespan, CORS, static files, Jinja2 templates, global exception handler

### Phase 9 — Frontend ✅
- `app/templates/index.html` — Upload page with drag-and-drop, preview, loading pipeline
- `app/templates/results.html` — Results page with all result cards + JSON modal
- `app/static/css/main.css` — Dark glassmorphism design, animations, responsive
- `app/static/css/results.css` — Results grid, confidence bar, KB entry cards
- `app/static/js/upload.js` — Drag-drop, validation, fetch to /diagnose, step animation
- `app/static/js/results.js` — Reads sessionStorage, populates all result UI sections

### Phase 10 — Tests ✅ (ALL COMPLETE)
- `tests/conftest.py` — Shared fixtures (settings, mock results, TestClient)
- `tests/test_api.py` — Health, upload, report, frontend route tests (8 cases)
- `tests/test_rag.py` — EmbeddingService, FAISSService, RetrievalService tests (16 cases)
- `tests/test_services.py` — GeminiVisionService + GeminiDiagnosisService unit tests (14 cases)
- `tests/test_pdf.py` — PDFGenerator unit tests (10 cases)
- `tests/test_validation.py` — file_handler validation tests (16 cases)

### Phase 10 — pytest Configuration ✅
- `pytest.ini` — asyncio_mode=auto, coverage config, 80% threshold

### Phase 11 — Documentation ✅
- `README.md` — Full project documentation (setup, env vars, API reference, architecture)

### Bug Fix — B-001 ✅ RESOLVED
- `app/core/dependencies.py` — Replaced `lru_cache(Settings)` with module-level singleton dicts keyed by primitive values (model name string, index path string). Eliminates `TypeError: unhashable type` on first `/diagnose` request.

---

## Pending Tasks (Next Tasks Queue)

| Priority | Task | File | Notes |
|----------|------|------|-------|
| 1 | Install dependencies | Shell | `pip install -r requirements.txt` |
| 2 | Build FAISS index | Shell | `python -m app.rag.index_builder` |
| 3 | Run test suite | Shell | `pytest --cov=app` |
| 4 | Boot validation | Shell | `uvicorn app.main:app --reload` |

---

## Known Issues

| ID | Issue | Status | Resolution |
|----|-------|--------|------------|
| I-001 | `lru_cache` on `_get_embedding_service` hashes `Settings` (unhashable). | **RESOLVED** | Replaced with module-level singleton dict in `app/core/dependencies.py` |
| I-002 | Circular import risk between services and core. | VERIFIED SAFE | Import order confirmed correct — services only import from core, not vice versa |
| I-003 | FAISS index not present at first boot. | EXPECTED | Documented in README; run `python -m app.rag.index_builder` once before first use |
| I-004 | Gemini API rate limits may cause 500 errors under rapid concurrent requests. | OPEN | Add tenacity retry logic in future iteration |
| I-005 | `generate_content()` is synchronous — blocks the event loop under high concurrency. | OPEN | Wrap with `asyncio.to_thread()` in future iteration |

---

## File Manifest

```
ai-error-diagnosis/
├── .env.example                          ✅
├── requirements.txt                      ✅
├── pytest.ini                            ✅
├── README.md                             ✅
├── agent-state.md                        ✅ (this file)
├── app/
│   ├── __init__.py                       ✅
│   ├── main.py                           ✅
│   ├── api/
│   │   ├── __init__.py                   ✅
│   │   └── router.py                     ✅
│   ├── core/
│   │   ├── __init__.py                   ✅
│   │   ├── config.py                     ✅
│   │   ├── logging.py                    ✅
│   │   └── dependencies.py               ✅ B-001 FIXED
│   ├── models/
│   │   └── __init__.py                   ✅
│   ├── schemas/
│   │   ├── __init__.py                   ✅
│   │   └── diagnosis.py                  ✅
│   ├── services/
│   │   ├── __init__.py                   ✅
│   │   ├── gemini_vision.py              ✅
│   │   └── gemini_diagnosis.py           ✅
│   ├── rag/
│   │   ├── __init__.py                   ✅
│   │   ├── embedding_service.py          ✅
│   │   ├── faiss_service.py              ✅
│   │   ├── retrieval_service.py          ✅
│   │   └── index_builder.py              ✅
│   ├── prompts/
│   │   ├── __init__.py                   ✅
│   │   └── templates.py                  ✅
│   ├── pdf/
│   │   ├── __init__.py                   ✅
│   │   └── report_generator.py           ✅
│   ├── utils/
│   │   ├── __init__.py                   ✅
│   │   └── file_handler.py               ✅
│   ├── templates/
│   │   ├── index.html                    ✅
│   │   └── results.html                  ✅
│   └── static/
│       ├── css/
│       │   ├── main.css                  ✅
│       │   └── results.css               ✅
│       └── js/
│           ├── upload.js                 ✅
│           └── results.js                ✅
├── data/
│   └── errors/
│       ├── python_errors.json            ✅
│       ├── fastapi_errors.json           ✅
│       ├── javascript_errors.json        ✅
│       └── database_errors.json          ✅
├── faiss_index/                          ✅ (dir exists — build with index_builder)
├── reports/                              ✅ (dir exists — PDFs written at runtime)
├── uploads/                              ✅ (dir exists — files written at runtime)
└── tests/
    ├── __init__.py                       ✅
    ├── conftest.py                       ✅
    ├── test_api.py                       ✅
    ├── test_rag.py                       ✅
    ├── test_services.py                  ✅
    ├── test_pdf.py                       ✅
    └── test_validation.py                ✅
```

---

## Validation Checklist

- [x] Accept screenshot uploads (PNG/JPG/JPEG/WEBP)
- [x] Gemini Vision analysis → structured JSON
- [x] Knowledge base (4 JSON files, 23 records)
- [x] Sentence Transformer embeddings (all-MiniLM-L6-v2)
- [x] FAISS retrieval (top-K, L2 flat index)
- [x] RAG-augmented prompt engineering
- [x] Gemini diagnosis → structured JSON
- [x] PDF report (ReportLab, all required sections)
- [x] Frontend: upload page (drag-and-drop)
- [x] Frontend: results page
- [x] API: POST /upload, POST /diagnose, GET /report/{id}, GET /health
- [x] Clean architecture / SOLID / type hints / docstrings
- [x] Environment variable config (no hardcoded secrets)
- [x] Structured logging
- [x] B-001 lru_cache bug fixed
- [x] tests/test_services.py
- [x] tests/test_pdf.py
- [x] tests/test_validation.py
- [x] pytest.ini
- [x] README.md
- [ ] FAISS index built (run: python -m app.rag.index_builder)
- [ ] pytest --cov=app passing ≥80%
- [ ] uvicorn app.main:app --reload boots cleanly

---

## Resume Instructions

If execution is interrupted, resume by:

1. Reading this file (`agent-state.md`) for current state.
2. Checking **Pending Tasks** table above.
3. Only 4 shell-level tasks remain (install → index → test → boot).
4. After each milestone completion, update:
   - Move task from **Pending** → **Completed Tasks**
   - Update **Current Task** section
   - Note any new **Known Issues**
