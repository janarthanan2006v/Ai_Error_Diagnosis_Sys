"""
Pytest configuration and shared fixtures.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.config import Settings
from app.schemas.diagnosis import DiagnosisResult, VisionAnalysisResult


# ── Settings Override ─────────────────────────────────────────

@pytest.fixture(scope="session")
def test_settings(tmp_path_factory) -> Settings:
    """Provide test settings with temp directories."""
    tmp = tmp_path_factory.mktemp("test")
    return Settings(
        gemini_api_key="test-api-key",
        uploads_dir=tmp / "uploads",
        reports_dir=tmp / "reports",
        faiss_index_path=tmp / "faiss_index" / "errors.index",
        faiss_metadata_path=tmp / "faiss_index" / "metadata.json",
        knowledge_base_dir=Path("data/errors"),
        app_env="testing",
    )


# ── Mock Vision Result ────────────────────────────────────────

@pytest.fixture
def mock_vision_result() -> VisionAnalysisResult:
    return VisionAnalysisResult(
        error_title="ModuleNotFoundError: No module named 'fastapi'",
        error_message="ModuleNotFoundError: No module named 'fastapi'",
        language="Python",
        framework="FastAPI",
        environment="Linux terminal",
        raw_stacktrace="Traceback (most recent call last):\n  File 'main.py', line 1, in <module>\n    import fastapi\nModuleNotFoundError: No module named 'fastapi'",
    )


# ── Mock Diagnosis Result ─────────────────────────────────────

@pytest.fixture
def mock_diagnosis_result() -> DiagnosisResult:
    return DiagnosisResult(
        error_summary="Python cannot locate the 'fastapi' package because it is not installed.",
        root_cause="The 'fastapi' package is missing from the active Python virtual environment.",
        confidence_score=0.95,
        recommended_fix="Run `pip install fastapi` in the active virtual environment.",
        step_by_step_solution=[
            "Step 1: Activate the virtual environment: `source venv/bin/activate`",
            "Step 2: Install fastapi: `pip install fastapi`",
            "Step 3: Verify installation: `pip show fastapi`",
            "Step 4: Re-run the application.",
        ],
        prevention_tips=[
            "Add all dependencies to requirements.txt.",
            "Use a consistent virtual environment across development and production.",
        ],
        related_errors=["ImportError", "PackageNotFoundError"],
    )


# ── Test Client ───────────────────────────────────────────────

@pytest.fixture
def client() -> TestClient:
    """Return a synchronous test client with mocked dependencies."""
    from app.main import app
    from app.core.dependencies import get_settings

    def override_settings():
        return Settings(
            gemini_api_key="test-api-key",
            uploads_dir=Path("uploads"),
            reports_dir=Path("reports"),
            faiss_index_path=Path("faiss_index/errors.index"),
            faiss_metadata_path=Path("faiss_index/metadata.json"),
            knowledge_base_dir=Path("data/errors"),
            app_env="testing",
        )

    app.dependency_overrides[get_settings] = override_settings

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
