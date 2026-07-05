"""
Unit tests for GeminiVisionService and GeminiDiagnosisService.

All calls to the Gemini SDK are mocked so no real API key is required.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image as PILImage

from app.schemas.diagnosis import DiagnosisResult, RetrievedError, VisionAnalysisResult
from app.services.gemini_diagnosis import GeminiDiagnosisService
from app.services.gemini_vision import GeminiVisionService


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_png(tmp_path: Path) -> Path:
    """Create a minimal valid PNG file and return its path."""
    img_path = tmp_path / "test_error.png"
    img = PILImage.new("RGB", (200, 100), color=(30, 30, 30))
    img.save(img_path, format="PNG")
    return img_path


def _vision_json() -> str:
    """Return a valid Gemini Vision JSON response string."""
    return json.dumps(
        {
            "error_title": "ModuleNotFoundError: No module named 'fastapi'",
            "error_message": "ModuleNotFoundError: No module named 'fastapi'",
            "language": "Python",
            "framework": "FastAPI",
            "environment": "Linux terminal",
            "raw_stacktrace": (
                "Traceback (most recent call last):\n"
                "  File 'main.py', line 1, in <module>\n"
                "    import fastapi\n"
                "ModuleNotFoundError: No module named 'fastapi'"
            ),
        }
    )


def _diagnosis_json() -> str:
    """Return a valid Gemini Diagnosis JSON response string."""
    return json.dumps(
        {
            "error_summary": "The 'fastapi' package is missing from the Python environment.",
            "root_cause": "Package not installed in the active virtual environment.",
            "confidence_score": 0.92,
            "recommended_fix": "Run `pip install fastapi` inside the virtual environment.",
            "step_by_step_solution": [
                "Step 1: Activate virtual environment: source venv/bin/activate",
                "Step 2: Install fastapi: pip install fastapi",
                "Step 3: Verify: pip show fastapi",
                "Step 4: Re-run the application.",
            ],
            "prevention_tips": [
                "Pin all dependencies in requirements.txt.",
                "Use a reproducible virtual environment (venv or conda).",
            ],
            "related_errors": ["ImportError", "PackageNotFoundError"],
        }
    )


# ── GeminiVisionService ───────────────────────────────────────────────────────


class TestGeminiVisionService:
    """Tests for GeminiVisionService.analyse_screenshot()."""

    def test_init_raises_on_empty_api_key(self):
        """Passing an empty API key should raise ValueError."""
        with pytest.raises(ValueError, match="API key"):
            GeminiVisionService(api_key="")

    def test_init_succeeds_with_valid_key(self):
        """Valid API key should not raise during initialisation."""
        with patch("app.services.gemini_vision.genai"):
            service = GeminiVisionService(api_key="test-key", model_name="gemini-1.5-flash")
            assert service is not None

    @pytest.mark.asyncio
    async def test_analyse_raises_file_not_found(self, tmp_path: Path):
        """analyse_screenshot() with a non-existent path should raise FileNotFoundError."""
        with patch("app.services.gemini_vision.genai"):
            service = GeminiVisionService(api_key="test-key")
        non_existent = tmp_path / "missing.png"
        with pytest.raises(FileNotFoundError):
            await service.analyse_screenshot(non_existent)

    @pytest.mark.asyncio
    async def test_analyse_raises_on_unsupported_extension(self, tmp_path: Path):
        """analyse_screenshot() with a .gif file should raise ValueError."""
        gif_path = tmp_path / "error.gif"
        gif_path.write_bytes(b"GIF89a")
        with patch("app.services.gemini_vision.genai"):
            service = GeminiVisionService(api_key="test-key")
        with pytest.raises(ValueError, match="Unsupported image format"):
            await service.analyse_screenshot(gif_path)

    @pytest.mark.asyncio
    async def test_analyse_returns_vision_result(self, tmp_path: Path):
        """analyse_screenshot() should return a VisionAnalysisResult on success."""
        png_path = _make_png(tmp_path)

        mock_response = MagicMock()
        mock_response.text = _vision_json()

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("app.services.gemini_vision.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            mock_genai.types = MagicMock()
            service = GeminiVisionService(api_key="test-key")

        result = await service.analyse_screenshot(png_path)

        assert isinstance(result, VisionAnalysisResult)
        assert "fastapi" in result.error_title.lower()
        assert result.language == "Python"
        assert result.framework == "FastAPI"

    @pytest.mark.asyncio
    async def test_analyse_raises_on_invalid_json(self, tmp_path: Path):
        """analyse_screenshot() should raise ValueError on malformed Gemini response."""
        png_path = _make_png(tmp_path)

        mock_response = MagicMock()
        mock_response.text = "This is not JSON at all."

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("app.services.gemini_vision.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            mock_genai.types = MagicMock()
            service = GeminiVisionService(api_key="test-key")

        with pytest.raises(ValueError, match="invalid JSON"):
            await service.analyse_screenshot(png_path)

    @pytest.mark.asyncio
    async def test_analyse_strips_markdown_fences(self, tmp_path: Path):
        """analyse_screenshot() should handle ```json ... ``` wrapped responses."""
        png_path = _make_png(tmp_path)

        mock_response = MagicMock()
        mock_response.text = f"```json\n{_vision_json()}\n```"

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("app.services.gemini_vision.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            mock_genai.types = MagicMock()
            service = GeminiVisionService(api_key="test-key")

        result = await service.analyse_screenshot(png_path)
        assert isinstance(result, VisionAnalysisResult)

    @pytest.mark.asyncio
    async def test_analyse_raises_runtime_on_api_error(self, tmp_path: Path):
        """analyse_screenshot() should raise RuntimeError when Gemini API fails."""
        png_path = _make_png(tmp_path)

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API quota exceeded")

        with patch("app.services.gemini_vision.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            mock_genai.types = MagicMock()
            service = GeminiVisionService(api_key="test-key")

        with pytest.raises(RuntimeError, match="Gemini Vision API error"):
            await service.analyse_screenshot(png_path)


# ── GeminiDiagnosisService ────────────────────────────────────────────────────


class TestGeminiDiagnosisService:
    """Tests for GeminiDiagnosisService.generate_diagnosis()."""

    def test_init_raises_on_empty_api_key(self):
        """Empty API key should raise ValueError."""
        with pytest.raises(ValueError, match="API key"):
            GeminiDiagnosisService(api_key="")

    def test_init_succeeds_with_valid_key(self):
        """Valid API key should not raise during initialisation."""
        with patch("app.services.gemini_diagnosis.genai"):
            service = GeminiDiagnosisService(api_key="test-key")
            assert service is not None

    @pytest.fixture
    def mock_vision_result(self) -> VisionAnalysisResult:
        return VisionAnalysisResult(
            error_title="ModuleNotFoundError: No module named 'fastapi'",
            error_message="ModuleNotFoundError: No module named 'fastapi'",
            language="Python",
            framework="FastAPI",
            environment="Linux terminal",
            raw_stacktrace="Traceback ...\nModuleNotFoundError: No module named 'fastapi'",
        )

    @pytest.fixture
    def mock_retrieved_errors(self) -> list[RetrievedError]:
        return [
            RetrievedError(
                error_name="ModuleNotFoundError",
                description="Python cannot find the requested module.",
                root_cause="Package is not installed in the current environment.",
                solution="Install the missing package using pip.",
                troubleshooting_steps=["Check pip list", "Run pip install <package>"],
                similarity_score=0.91,
            )
        ]

    @pytest.mark.asyncio
    async def test_generate_diagnosis_returns_result(
        self, mock_vision_result, mock_retrieved_errors
    ):
        """generate_diagnosis() should return a DiagnosisResult on success."""
        mock_response = MagicMock()
        mock_response.text = _diagnosis_json()

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("app.services.gemini_diagnosis.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            mock_genai.types = MagicMock()
            service = GeminiDiagnosisService(api_key="test-key")

        result = await service.generate_diagnosis(mock_vision_result, mock_retrieved_errors)

        assert isinstance(result, DiagnosisResult)
        assert 0.0 <= result.confidence_score <= 1.0
        assert len(result.step_by_step_solution) >= 1
        assert len(result.prevention_tips) >= 1

    @pytest.mark.asyncio
    async def test_generate_diagnosis_clamps_confidence_above_one(
        self, mock_vision_result, mock_retrieved_errors
    ):
        """confidence_score > 1.0 in the API response should be clamped to 1.0."""
        data = json.loads(_diagnosis_json())
        data["confidence_score"] = 1.5
        mock_response = MagicMock()
        mock_response.text = json.dumps(data)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("app.services.gemini_diagnosis.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            mock_genai.types = MagicMock()
            service = GeminiDiagnosisService(api_key="test-key")

        result = await service.generate_diagnosis(mock_vision_result, mock_retrieved_errors)
        assert result.confidence_score == 1.0

    @pytest.mark.asyncio
    async def test_generate_diagnosis_clamps_confidence_below_zero(
        self, mock_vision_result, mock_retrieved_errors
    ):
        """confidence_score < 0.0 in the API response should be clamped to 0.0."""
        data = json.loads(_diagnosis_json())
        data["confidence_score"] = -0.5
        mock_response = MagicMock()
        mock_response.text = json.dumps(data)

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("app.services.gemini_diagnosis.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            mock_genai.types = MagicMock()
            service = GeminiDiagnosisService(api_key="test-key")

        result = await service.generate_diagnosis(mock_vision_result, mock_retrieved_errors)
        assert result.confidence_score == 0.0

    @pytest.mark.asyncio
    async def test_generate_diagnosis_raises_on_invalid_json(
        self, mock_vision_result, mock_retrieved_errors
    ):
        """generate_diagnosis() should raise ValueError on unparseable Gemini response."""
        mock_response = MagicMock()
        mock_response.text = "Not JSON at all."

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("app.services.gemini_diagnosis.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            mock_genai.types = MagicMock()
            service = GeminiDiagnosisService(api_key="test-key")

        with pytest.raises(ValueError, match="invalid JSON"):
            await service.generate_diagnosis(mock_vision_result, mock_retrieved_errors)

    @pytest.mark.asyncio
    async def test_generate_diagnosis_raises_runtime_on_api_error(
        self, mock_vision_result, mock_retrieved_errors
    ):
        """generate_diagnosis() should raise RuntimeError when the Gemini API call fails."""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("Network timeout")

        with patch("app.services.gemini_diagnosis.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            mock_genai.types = MagicMock()
            service = GeminiDiagnosisService(api_key="test-key")

        with pytest.raises(RuntimeError, match="Gemini Diagnosis API error"):
            await service.generate_diagnosis(mock_vision_result, mock_retrieved_errors)

    @pytest.mark.asyncio
    async def test_generate_diagnosis_works_with_no_retrieved_errors(
        self, mock_vision_result
    ):
        """generate_diagnosis() should succeed even with an empty retrieved_errors list."""
        mock_response = MagicMock()
        mock_response.text = _diagnosis_json()

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("app.services.gemini_diagnosis.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            mock_genai.types = MagicMock()
            service = GeminiDiagnosisService(api_key="test-key")

        result = await service.generate_diagnosis(mock_vision_result, [])
        assert isinstance(result, DiagnosisResult)

    @pytest.mark.asyncio
    async def test_generate_diagnosis_strips_markdown_fences(
        self, mock_vision_result, mock_retrieved_errors
    ):
        """generate_diagnosis() should handle ```json ... ``` wrapped responses."""
        mock_response = MagicMock()
        mock_response.text = f"```json\n{_diagnosis_json()}\n```"

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("app.services.gemini_diagnosis.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = MagicMock()
            mock_genai.types = MagicMock()
            service = GeminiDiagnosisService(api_key="test-key")

        result = await service.generate_diagnosis(mock_vision_result, mock_retrieved_errors)
        assert isinstance(result, DiagnosisResult)
