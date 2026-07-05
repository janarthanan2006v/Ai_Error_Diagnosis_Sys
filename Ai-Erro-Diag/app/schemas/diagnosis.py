"""
Pydantic schemas for all API request/response models.

These schemas enforce strict typing and validation at the API boundary.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── Vision Analysis ──────────────────────────────────────────────────────────

class VisionAnalysisResult(BaseModel):
    """Structured output from Gemini Vision analysis of an error screenshot."""

    error_title: str = Field(description="Short title of the detected error")
    error_message: str = Field(description="Full error message extracted from the image")
    language: str = Field(description="Programming language detected (e.g. Python, JavaScript)")
    framework: str = Field(description="Framework or library if detected (e.g. FastAPI, React)")
    environment: str = Field(description="Runtime environment (e.g. Docker, Linux terminal, browser)")
    raw_stacktrace: str = Field(description="Raw stack trace text extracted from the image")


# ── RAG Retrieved Errors ─────────────────────────────────────────────────────

class RetrievedError(BaseModel):
    """A single error record retrieved from the FAISS knowledge base."""

    error_name: str
    description: str
    root_cause: str
    solution: str
    troubleshooting_steps: list[str]
    similarity_score: float = Field(ge=0.0, le=1.0)


# ── Diagnosis ────────────────────────────────────────────────────────────────

class DiagnosisResult(BaseModel):
    """Full structured diagnosis output from Gemini."""

    error_summary: str = Field(description="Concise human-readable summary of the error")
    root_cause: str = Field(description="Identified root cause of the error")
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Model confidence in the diagnosis (0.0–1.0)"
    )
    recommended_fix: str = Field(description="Primary recommended fix for the error")
    step_by_step_solution: list[str] = Field(
        description="Ordered list of steps to resolve the error"
    )
    prevention_tips: list[str] = Field(
        description="List of tips to prevent this error in the future"
    )
    related_errors: list[str] = Field(
        description="Names of related or similar errors"
    )


# ── API Request / Response ───────────────────────────────────────────────────

class DiagnoseRequest(BaseModel):
    """Request body for the /diagnose endpoint (used internally after upload)."""

    image_path: str = Field(description="Server-side path to the uploaded image")


class DiagnoseResponse(BaseModel):
    """Full API response after completing the diagnosis pipeline."""

    report_id: str = Field(description="Unique identifier for this diagnosis report")
    vision_analysis: VisionAnalysisResult
    retrieved_errors: list[RetrievedError]
    diagnosis: DiagnosisResult
    pdf_url: str = Field(description="URL path to download the generated PDF report")


class UploadResponse(BaseModel):
    """Response from POST /upload."""

    filename: str
    image_path: str
    message: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    """Standardised error response body."""

    detail: str
    error_code: str = "INTERNAL_ERROR"
