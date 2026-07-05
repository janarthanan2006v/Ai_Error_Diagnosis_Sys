"""
Tests for API endpoints.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.diagnosis import DiagnosisResult, RetrievedError, VisionAnalysisResult


# ── Health Endpoint ───────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient):
        """GET /api/v1/health should return status='ok'."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "environment" in data

    def test_health_includes_version(self, client: TestClient):
        """Health endpoint should include a version string."""
        response = client.get("/api/v1/health")
        assert response.json()["version"] == "1.0.0"


# ── Upload Endpoint ───────────────────────────────────────────

class TestUploadEndpoint:
    def _make_image_bytes(self, format: str = "PNG") -> bytes:
        """Create a minimal valid image in memory."""
        from PIL import Image as PILImage
        buf = io.BytesIO()
        img = PILImage.new("RGB", (100, 100), color=(255, 0, 0))
        img.save(buf, format=format)
        return buf.getvalue()

    def test_upload_valid_png(self, client: TestClient):
        """POST /upload with a valid PNG should return 200."""
        image_bytes = self._make_image_bytes("PNG")
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test_error.png", image_bytes, "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "image_path" in data
        assert "message" in data

    def test_upload_unsupported_type(self, client: TestClient):
        """POST /upload with a .txt file should return 400."""
        response = client.post(
            "/api/v1/upload",
            files={"file": ("error.txt", b"some text", "text/plain")},
        )
        assert response.status_code == 400

    def test_upload_empty_file(self, client: TestClient):
        """POST /upload with an empty file should return 400."""
        response = client.post(
            "/api/v1/upload",
            files={"file": ("empty.png", b"", "image/png")},
        )
        assert response.status_code == 400


# ── Report Endpoint ───────────────────────────────────────────

class TestReportEndpoint:
    def test_report_not_found(self, client: TestClient):
        """GET /report/nonexistent should return 404."""
        response = client.get("/api/v1/report/nonexistent_report_id")
        assert response.status_code == 404

    def test_report_path_traversal_blocked(self, client: TestClient):
        """Path traversal characters in report_id should be sanitised."""
        response = client.get("/api/v1/report/../../../etc/passwd")
        # Should not succeed — either 404 (not found) or sanitised
        assert response.status_code in (404, 400)


# ── Frontend Routes ───────────────────────────────────────────

class TestFrontendRoutes:
    def test_index_page_loads(self, client: TestClient):
        """GET / should return 200 with HTML content."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_results_page_loads(self, client: TestClient):
        """GET /results should return 200 with HTML content."""
        response = client.get("/results")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_docs_accessible(self, client: TestClient):
        """GET /docs should return 200 (OpenAPI interactive docs)."""
        response = client.get("/docs")
        assert response.status_code == 200
