"""
Dependency injection providers for FastAPI endpoints.

Each function is a FastAPI dependency that returns a configured service
instance, allowing easy overriding in tests.

Implementation note on caching:
    Pydantic BaseSettings objects are **not** hashable, so they cannot be
    used as lru_cache arguments directly.  We use module-level singleton
    dicts keyed by primitive values (strings / resolved Path strings) to
    achieve the same one-instance-per-configuration guarantee without the
    TypeError that would occur when lru_cache attempts to hash a Settings
    object.  The cache is intentionally simple: a single settings object
    is resolved once at startup and never mutated, so a single-slot dict
    is sufficient.
"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.rag.embedding_service import EmbeddingService
from app.rag.faiss_service import FAISSService
from app.rag.retrieval_service import RetrievalService
from app.services.gemini_vision import GeminiVisionService
from app.services.gemini_diagnosis import GeminiDiagnosisService

# ── Module-level singleton caches ─────────────────────────────────────────────
# Keyed by the primitive config values that uniquely identify each service
# instance.  This avoids the lru_cache(Settings) unhashable-type crash.

_embedding_cache: dict[str, EmbeddingService] = {}
_faiss_cache: dict[str, FAISSService] = {}


def _get_embedding_singleton(model_name: str) -> EmbeddingService:
    """Return (or create and cache) an EmbeddingService for the given model."""
    if model_name not in _embedding_cache:
        _embedding_cache[model_name] = EmbeddingService(model_name=model_name)
    return _embedding_cache[model_name]


def _get_faiss_singleton(index_path: Path, metadata_path: Path) -> FAISSService:
    """Return (or create and cache) a FAISSService for the given paths."""
    key = str(index_path)
    if key not in _faiss_cache:
        _faiss_cache[key] = FAISSService(
            index_path=index_path,
            metadata_path=metadata_path,
        )
    return _faiss_cache[key]


# ── FastAPI dependency providers ──────────────────────────────────────────────

def get_embedding_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> EmbeddingService:
    """Provide the shared EmbeddingService instance."""
    return _get_embedding_singleton(settings.embedding_model)


def get_faiss_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> FAISSService:
    """Provide the shared FAISSService instance."""
    return _get_faiss_singleton(settings.faiss_index_path, settings.faiss_metadata_path)


def get_retrieval_service(
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding_service)],
    faiss_service: Annotated[FAISSService, Depends(get_faiss_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RetrievalService:
    """Provide a RetrievalService composed of embedding + FAISS."""
    return RetrievalService(
        embedding_service=embedding_service,
        faiss_service=faiss_service,
        top_k=settings.top_k_results,
    )


def get_vision_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GeminiVisionService:
    """Provide the GeminiVisionService."""
    return GeminiVisionService(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_vision_model,
    )


def get_diagnosis_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GeminiDiagnosisService:
    """Provide the GeminiDiagnosisService."""
    return GeminiDiagnosisService(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_diagnosis_model,
    )

