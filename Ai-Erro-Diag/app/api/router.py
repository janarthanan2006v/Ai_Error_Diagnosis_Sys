"""
Diagnosis API router.

Implements:
  POST /api/v1/upload    — Upload an error screenshot
  POST /api/v1/diagnose  — Run the full diagnosis pipeline
  GET  /api/v1/report/{report_id} — Download a PDF report
  GET  /api/v1/health    — Health check
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import Settings, get_settings
from app.core.dependencies import (
    get_diagnosis_service,
    get_retrieval_service,
    get_vision_service,
)
from app.core.logging import get_logger
from app.pdf.report_generator import PDFGenerator
from app.rag.retrieval_service import RetrievalService
from app.schemas.diagnosis import (
    DiagnoseResponse,
    ErrorResponse,
    HealthResponse,
    UploadResponse,
)
from app.services.gemini_diagnosis import GeminiDiagnosisService
from app.services.gemini_vision import GeminiVisionService
from app.utils.file_handler import save_upload, validate_upload

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Diagnosis"])


# ── Health ────────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the current health status of the API.",
)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """Return API health status."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment=settings.app_env,
    )


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload Error Screenshot",
    description=(
        "Upload a PNG, JPG, JPEG, or WEBP screenshot containing a software error. "
        "Returns the server-side image path to use with /diagnose."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file type or empty file"},
        413: {"model": ErrorResponse, "description": "File size exceeds limit"},
    },
)
async def upload_screenshot(
    file: Annotated[UploadFile, File(description="Error screenshot image file")],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadResponse:
    """
    Upload an error screenshot for subsequent diagnosis.

    Args:
        file: The uploaded image file.
        settings: Application configuration.

    Returns:
        UploadResponse with the server-side image path.
    """
    validate_upload(file, max_bytes=settings.max_upload_size_bytes)
    image_path = await save_upload(
        file,
        uploads_dir=settings.uploads_dir,
        max_bytes=settings.max_upload_size_bytes,
    )

    logger.info("Screenshot uploaded: %s", image_path.name)
    return UploadResponse(
        filename=file.filename or image_path.name,
        image_path=str(image_path),
        message="File uploaded successfully. Use /diagnose to analyse the error.",
    )


# ── Diagnose ──────────────────────────────────────────────────────────────────

@router.post(
    "/diagnose",
    response_model=DiagnoseResponse,
    summary="Diagnose Error from Screenshot",
    description=(
        "Run the full AI diagnosis pipeline on an uploaded screenshot. "
        "Performs Gemini Vision analysis, FAISS retrieval, and Gemini diagnosis generation."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Validation error or unsupported file"},
        404: {"model": ErrorResponse, "description": "Uploaded image not found"},
        500: {"model": ErrorResponse, "description": "AI service error"},
    },
)
async def diagnose_screenshot(
    file: Annotated[UploadFile, File(description="Error screenshot image file")],
    settings: Annotated[Settings, Depends(get_settings)],
    vision_service: Annotated[GeminiVisionService, Depends(get_vision_service)],
    diagnosis_service: Annotated[GeminiDiagnosisService, Depends(get_diagnosis_service)],
    retrieval_service: Annotated[RetrievalService, Depends(get_retrieval_service)],
) -> DiagnoseResponse:
    """
    Full pipeline: upload → vision → retrieval → diagnosis → PDF.

    Args:
        file: The error screenshot.
        settings: Application configuration.
        vision_service: Gemini Vision service.
        diagnosis_service: Gemini Diagnosis service.
        retrieval_service: FAISS retrieval service.

    Returns:
        DiagnoseResponse with vision analysis, retrieved errors, diagnosis, and PDF URL.
    """
    # 1. Validate and save upload
    validate_upload(file, max_bytes=settings.max_upload_size_bytes)
    image_path = await save_upload(
        file,
        uploads_dir=settings.uploads_dir,
        max_bytes=settings.max_upload_size_bytes,
    )
    logger.info("Starting diagnosis pipeline for: %s", image_path.name)

    # 2. Gemini Vision analysis
    try:
        vision_result = await vision_service.analyse_screenshot(image_path)
        logger.info("Vision analysis complete: '%s'", vision_result.error_title)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"Vision analysis failed: {exc}") from exc

    # 3. RAG retrieval
    query = f"{vision_result.error_title} {vision_result.error_message}"
    retrieved_errors = retrieval_service.retrieve(query)
    logger.info("Retrieved %d similar errors", len(retrieved_errors))

    # 4. Gemini Diagnosis
    try:
        diagnosis = await diagnosis_service.generate_diagnosis(vision_result, retrieved_errors)
        logger.info("Diagnosis generated with confidence: %.2f", diagnosis.confidence_score)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=f"Diagnosis generation failed: {exc}") from exc

    # 5. PDF generation
    report_id = uuid.uuid4().hex
    try:
        pdf_gen = PDFGenerator(reports_dir=settings.reports_dir)
        pdf_path = pdf_gen.generate(
            report_id=report_id,
            image_path=image_path,
            vision_result=vision_result,
            diagnosis=diagnosis,
        )
        pdf_url = f"/api/v1/report/{report_id}"
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        pdf_url = ""

    return DiagnoseResponse(
        report_id=report_id,
        vision_analysis=vision_result,
        retrieved_errors=retrieved_errors,
        diagnosis=diagnosis,
        pdf_url=pdf_url,
    )


# ── Report Download ───────────────────────────────────────────────────────────

@router.get(
    "/report/{report_id}",
    summary="Download PDF Report",
    description="Download a previously generated PDF diagnosis report by its report ID.",
    responses={
        404: {"model": ErrorResponse, "description": "Report not found"},
    },
)
async def download_report(
    report_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> FileResponse:
    """
    Serve a generated PDF report for download.

    Args:
        report_id: Unique report identifier (returned from /diagnose).
        settings: Application configuration.

    Returns:
        FileResponse streaming the PDF file.
    """
    # Sanitise report_id to prevent path traversal
    safe_id = "".join(c for c in report_id if c.isalnum() or c in ("-", "_"))
    pdf_path = settings.reports_dir / f"{safe_id}.pdf"

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Report '{safe_id}' not found. It may have expired or never been generated.",
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"error-diagnosis-{safe_id}.pdf",
    )
