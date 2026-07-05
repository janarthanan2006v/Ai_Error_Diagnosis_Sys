# skills.md

## Engineering Principles

* Follow Clean Architecture.
* Follow SOLID Principles.
* Use Dependency Injection where appropriate.
* Use modular folder structure.
* Avoid monolithic files.
* Write reusable services.
* Add type hints everywhere.
* Use Pydantic models.
* Use async FastAPI endpoints.
* Create structured logging.

---

## Code Quality Rules

* Production-ready code only.
* No placeholder implementations.
* No TODO comments.
* No hardcoded secrets.
* Use environment variables.
* Add docstrings.
* Add exception handling.
* Add validation.

---

## Backend Standards

Use:

* FastAPI
* Uvicorn
* Pydantic
* Python 3.11+

Folder Structure:

app/
├── api/
├── core/
├── models/
├── schemas/
├── services/
├── rag/
├── prompts/
├── utils/
├── pdf/
├── tests/
└── main.py

---

## Gemini Standards

Create dedicated services:

services/
├── gemini_vision.py
├── gemini_diagnosis.py

Responsibilities:

Gemini Vision:

* OCR
* Error Extraction
* Stacktrace Parsing

Gemini Diagnosis:

* Root Cause Analysis
* Troubleshooting
* Recommendations

---

## RAG Standards

Use:

SentenceTransformer("all-MiniLM-L6-v2")

Implement:

* embedding_service.py
* faiss_service.py
* retrieval_service.py

Functions:

* create_embeddings()
* build_index()
* search_similar_errors()

---

## Knowledge Base Standards

Store:

data/errors/

Files:

* python_errors.json
* fastapi_errors.json
* javascript_errors.json
* database_errors.json

Each record:

{
"error_name":"",
"description":"",
"root_cause":"",
"solution":"",
"troubleshooting_steps":[]
}

---

## Prompt Engineering Standards

Always use RAG context.

Prompt Structure:

1. Error Details
2. Stack Trace
3. Retrieved Errors
4. Root Causes
5. Solutions
6. Request Diagnosis

Output must be JSON.

---

## API Standards

Endpoints:

POST /upload

POST /diagnose

GET /report/{report_id}

GET /health

GET /docs

---

## PDF Standards

Use ReportLab.

Sections:

* Screenshot
* Summary
* Root Cause
* Fix
* Troubleshooting
* Prevention

Generate:

reports/report.pdf

---

## Frontend Standards

Technologies:

* HTML
* CSS
* JavaScript

Pages:

* index.html
* results.html

Features:

* Drag & Drop Upload
* Progress Indicator
* Result Viewer
* PDF Download

---

## Security Standards

* Validate uploads.
* Restrict file size.
* Sanitize inputs.
* Protect API keys.
* Never expose secrets.

---

## Testing Standards

Use:

pytest

Coverage:

* API Tests
* Service Tests
* RAG Tests
* PDF Tests

Target:

> 80% coverage

---

## Documentation Standards

Generate:

README.md

Include:

* Setup
* Installation
* Environment Variables
* Running Application
* API Usage
* Architecture Diagram

---

## Success Criteria

The application must:

1. Accept screenshot uploads.
2. Extract software errors using Gemini Vision.
3. Retrieve similar issues using FAISS.
4. Generate diagnosis using Gemini.
5. Return structured JSON.
6. Generate PDF reports.
7. Be fully runnable with:

uvicorn app.main:app --reload

8. Be production ready.
