"""
File handling utilities for upload validation and storage.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.logging import get_logger

logger = get_logger(__name__)

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".webp"})
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
})


def validate_upload(file: UploadFile, max_bytes: int) -> None:
    """
    Validate an uploaded file for type and size constraints.

    Args:
        file: FastAPI UploadFile instance.
        max_bytes: Maximum allowed file size in bytes.

    Raises:
        HTTPException: 400 if the file type is unsupported or file is empty.
        HTTPException: 413 if the file exceeds the size limit.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: '{extension}'. "
                f"Allowed types: {sorted(ALLOWED_EXTENSIONS)}"
            ),
        )

    content_type = file.content_type or ""
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type: '{content_type}'",
        )


async def save_upload(file: UploadFile, uploads_dir: Path, max_bytes: int) -> Path:
    """
    Persist an uploaded file to disk with a unique filename.

    Validates file size during streaming read and raises an error if
    the limit is exceeded, avoiding large allocations in memory.

    Args:
        file: FastAPI UploadFile instance.
        uploads_dir: Directory where the file should be saved.
        max_bytes: Maximum allowed file size in bytes.

    Returns:
        Path to the saved file on disk.

    Raises:
        HTTPException: 413 if the file exceeds the size limit.
        HTTPException: 400 if the file is empty.
    """
    uploads_dir.mkdir(parents=True, exist_ok=True)
    extension = Path(file.filename or "upload").suffix.lower() or ".jpg"
    unique_name = f"{uuid.uuid4().hex}{extension}"
    dest_path = uploads_dir / unique_name

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File size {len(content) / 1024 / 1024:.1f} MB exceeds "
                f"the {max_bytes / 1024 / 1024:.0f} MB limit"
            ),
        )

    with open(dest_path, "wb") as f:
        f.write(content)

    logger.info("Saved upload: %s (%d bytes)", dest_path.name, len(content))
    return dest_path
