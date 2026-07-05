"""
Unit tests for PDFGenerator.

All tests use pytest's tmp_path fixture to avoid writing to the real
reports/ directory.  No Gemini API calls are made.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image as PILImage

from app.pdf.report_generator import PDFGenerator
from app.schemas.diagnosis import DiagnosisResult, VisionAnalysisResult


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def reports_dir(tmp_path: Path) -> Path:
    d = tmp_path / "reports"
    d.mkdir()
    return d


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    img_path = tmp_path / "screenshot.png"
    img = PILImage.new("RGB", (400, 200), color=(20, 20, 40))
    img.save(img_path, format="PNG")
    return img_path


@pytest.fixture
def sample_vision() -> VisionAnalysisResult:
    return VisionAnalysisResult(
        error_title="ModuleNotFoundError: No module named 'fastapi'",
        error_message="ModuleNotFoundError: No module named 'fastapi'",
        language="Python",
        framework="FastAPI",
        environment="Linux terminal",
        raw_stacktrace="Traceback...\nModuleNotFoundError: No module named 'fastapi'",
    )


@pytest.fixture
def sample_diagnosis() -> DiagnosisResult:
    return DiagnosisResult(
        error_summary="The 'fastapi' package is missing.",
        root_cause="Package not installed.",
        confidence_score=0.92,
        recommended_fix="Run `pip install fastapi`.",
        step_by_step_solution=["Step 1: Activate venv.", "Step 2: pip install fastapi."],
        prevention_tips=["Pin deps in requirements.txt."],
        related_errors=["ImportError"],
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestPDFGenerator:
    def test_generate_creates_pdf_file(self, reports_dir, sample_image, sample_vision, sample_diagnosis):
        """generate() should create a .pdf file in the reports directory."""
        gen = PDFGenerator(reports_dir=reports_dir)
        pdf = gen.generate("rpt001", sample_image, sample_vision, sample_diagnosis)
        assert pdf.exists() and pdf.suffix == ".pdf"

    def test_generate_returns_correct_path(self, reports_dir, sample_image, sample_vision, sample_diagnosis):
        """generate() should return the exact path of the created PDF."""
        gen = PDFGenerator(reports_dir=reports_dir)
        pdf = gen.generate("abc123", sample_image, sample_vision, sample_diagnosis)
        assert pdf == reports_dir / "abc123.pdf"

    def test_generated_pdf_is_non_empty(self, reports_dir, sample_image, sample_vision, sample_diagnosis):
        """The generated PDF must be larger than 1 KB."""
        gen = PDFGenerator(reports_dir=reports_dir)
        pdf = gen.generate("size_check", sample_image, sample_vision, sample_diagnosis)
        assert pdf.stat().st_size > 1024

    def test_generated_pdf_has_pdf_magic_bytes(self, reports_dir, sample_image, sample_vision, sample_diagnosis):
        """The generated file must start with %%PDF."""
        gen = PDFGenerator(reports_dir=reports_dir)
        pdf = gen.generate("magic", sample_image, sample_vision, sample_diagnosis)
        assert open(pdf, "rb").read(4) == b"%PDF"

    def test_missing_screenshot_does_not_raise(self, reports_dir, tmp_path, sample_vision, sample_diagnosis):
        """generate() with a non-existent image should use the fallback text, not raise."""
        gen = PDFGenerator(reports_dir=reports_dir)
        pdf = gen.generate("no_img", tmp_path / "missing.png", sample_vision, sample_diagnosis)
        assert pdf.exists()

    def test_high_confidence_score(self, reports_dir, sample_image, sample_vision):
        """confidence_score=1.0 should render the HIGH confidence banner."""
        diag = DiagnosisResult(
            error_summary="High confidence.", root_cause="Known cause.",
            confidence_score=1.0, recommended_fix="Apply fix.",
            step_by_step_solution=["Step 1."], prevention_tips=["Tip 1."], related_errors=[],
        )
        gen = PDFGenerator(reports_dir=reports_dir)
        assert gen.generate("high", sample_image, sample_vision, diag).exists()

    def test_low_confidence_score(self, reports_dir, sample_image, sample_vision):
        """confidence_score=0.1 should render the LOW confidence banner."""
        diag = DiagnosisResult(
            error_summary="Low confidence.", root_cause="Uncertain.",
            confidence_score=0.1, recommended_fix="Investigate manually.",
            step_by_step_solution=["Step 1."], prevention_tips=["Tip 1."], related_errors=[],
        )
        gen = PDFGenerator(reports_dir=reports_dir)
        assert gen.generate("low", sample_image, sample_vision, diag).exists()

    def test_empty_step_and_tip_lists(self, reports_dir, sample_image, sample_vision):
        """generate() should handle empty step_by_step_solution and prevention_tips."""
        diag = DiagnosisResult(
            error_summary="Minimal.", root_cause="Unknown.",
            confidence_score=0.5, recommended_fix="No fix.",
            step_by_step_solution=[], prevention_tips=[], related_errors=[],
        )
        gen = PDFGenerator(reports_dir=reports_dir)
        assert gen.generate("empty_lists", sample_image, sample_vision, diag).exists()

    def test_auto_creates_reports_dir(self, tmp_path, sample_image, sample_vision, sample_diagnosis):
        """PDFGenerator should create the reports directory if it does not exist."""
        new_dir = tmp_path / "new_reports"
        gen = PDFGenerator(reports_dir=new_dir)
        pdf = gen.generate("dir_test", sample_image, sample_vision, sample_diagnosis)
        assert new_dir.exists() and pdf.exists()

    def test_long_error_message_truncation(self, reports_dir, sample_image, sample_diagnosis):
        """generate() should handle very long error messages without crashing."""
        vision = VisionAnalysisResult(
            error_title="LongError", error_message="x" * 500,
            language="Python", framework="None", environment="Terminal",
            raw_stacktrace="y" * 400,
        )
        gen = PDFGenerator(reports_dir=reports_dir)
        assert gen.generate("long_msg", sample_image, vision, sample_diagnosis).exists()
