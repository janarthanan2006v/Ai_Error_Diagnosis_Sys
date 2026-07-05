"""
Unit tests for file_handler utilities: validate_upload() and save_upload().
"""
from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image as PILImage

from app.utils.file_handler import ALLOWED_EXTENSIONS, save_upload, validate_upload


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_upload(
    filename: str,
    content: bytes = b"fake image data",
    content_type: str = "image/png",
) -> UploadFile:
    """Create a minimal UploadFile mock."""
    mock = MagicMock(spec=UploadFile)
    mock.filename = filename
    mock.content_type = content_type
    mock.read = MagicMock(return_value=content)
    return mock


def _make_real_png(size: int = 500) -> bytes:
    """Return bytes of a valid in-memory PNG image."""
    buf = io.BytesIO()
    img = PILImage.new("RGB", (10, 10), color=(255, 0, 0))
    img.save(buf, format="PNG")
    return buf.getvalue()


MAX_BYTES = 10 * 1024 * 1024  # 10 MB


# ── validate_upload Tests ─────────────────────────────────────────────────────


class TestValidateUpload:
    def test_valid_png_passes(self):
        """A PNG file with correct content-type should not raise."""
        upload = _make_upload("error.png", content_type="image/png")
        validate_upload(upload, max_bytes=MAX_BYTES)  # Should not raise

    def test_valid_jpeg_passes(self):
        """A JPEG file with correct content-type should not raise."""
        upload = _make_upload("error.jpg", content_type="image/jpeg")
        validate_upload(upload, max_bytes=MAX_BYTES)

    def test_valid_webp_passes(self):
        """A WEBP file should pass validation."""
        upload = _make_upload("error.webp", content_type="image/webp")
        validate_upload(upload, max_bytes=MAX_BYTES)

    def test_no_filename_raises_400(self):
        """File with no filename should raise HTTP 400."""
        upload = _make_upload("")
        upload.filename = ""
        with pytest.raises(HTTPException) as exc_info:
            validate_upload(upload, max_bytes=MAX_BYTES)
        assert exc_info.value.status_code == 400

    def test_unsupported_extension_raises_400(self):
        """A .txt file should raise HTTP 400."""
        upload = _make_upload("error.txt", content_type="text/plain")
        with pytest.raises(HTTPException) as exc_info:
            validate_upload(upload, max_bytes=MAX_BYTES)
        assert exc_info.value.status_code == 400

    def test_pdf_extension_raises_400(self):
        """A .pdf file should raise HTTP 400."""
        upload = _make_upload("report.pdf", content_type="application/pdf")
        with pytest.raises(HTTPException) as exc_info:
            validate_upload(upload, max_bytes=MAX_BYTES)
        assert exc_info.value.status_code == 400

    def test_gif_extension_raises_400(self):
        """A .gif file should raise HTTP 400."""
        upload = _make_upload("anim.gif", content_type="image/gif")
        with pytest.raises(HTTPException) as exc_info:
            validate_upload(upload, max_bytes=MAX_BYTES)
        assert exc_info.value.status_code == 400

    def test_wrong_content_type_raises_400(self):
        """A .png file with wrong content-type (text/html) should raise HTTP 400."""
        upload = _make_upload("error.png", content_type="text/html")
        with pytest.raises(HTTPException) as exc_info:
            validate_upload(upload, max_bytes=MAX_BYTES)
        assert exc_info.value.status_code == 400

    def test_none_content_type_is_accepted(self):
        """A .png file with no content_type header should not raise (optional header)."""
        upload = _make_upload("error.png", content_type="")
        validate_upload(upload, max_bytes=MAX_BYTES)  # Should not raise

    def test_allowed_extensions_set(self):
        """ALLOWED_EXTENSIONS should include .jpg, .jpeg, .png, .webp."""
        assert ".png" in ALLOWED_EXTENSIONS
        assert ".jpg" in ALLOWED_EXTENSIONS
        assert ".jpeg" in ALLOWED_EXTENSIONS
        assert ".webp" in ALLOWED_EXTENSIONS
        assert ".gif" not in ALLOWED_EXTENSIONS
        assert ".txt" not in ALLOWED_EXTENSIONS


# ── save_upload Tests ─────────────────────────────────────────────────────────


class TestSaveUpload:
    @pytest.mark.asyncio
    async def test_save_creates_file(self, tmp_path: Path):
        """save_upload() should write the file to the uploads directory."""
        content = _make_real_png()
        mock = MagicMock(spec=UploadFile)
        mock.filename = "test.png"
        mock.read = MagicMock(return_value=content)

        import asyncio

        async def async_read():
            return content

        mock.read = async_read

        dest = await save_upload(mock, uploads_dir=tmp_path, max_bytes=MAX_BYTES)
        assert dest.exists()
        assert dest.suffix == ".png"

    @pytest.mark.asyncio
    async def test_save_uses_unique_filename(self, tmp_path: Path):
        """save_upload() should generate unique filenames for each call."""
        content = _make_real_png()

        async def async_read():
            return content

        results = []
        for _ in range(3):
            mock = MagicMock(spec=UploadFile)
            mock.filename = "error.png"
            mock.read = async_read
            dest = await save_upload(mock, uploads_dir=tmp_path, max_bytes=MAX_BYTES)
            results.append(dest.name)

        assert len(set(results)) == 3  # All three filenames are unique

    @pytest.mark.asyncio
    async def test_save_raises_413_on_oversized_file(self, tmp_path: Path):
        """save_upload() should raise HTTP 413 if file exceeds max_bytes."""
        big_content = b"x" * (5 * 1024 * 1024)  # 5 MB

        async def async_read():
            return big_content

        mock = MagicMock(spec=UploadFile)
        mock.filename = "big.png"
        mock.read = async_read

        with pytest.raises(HTTPException) as exc_info:
            await save_upload(mock, uploads_dir=tmp_path, max_bytes=1024)  # 1 KB limit
        assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    async def test_save_raises_400_on_empty_file(self, tmp_path: Path):
        """save_upload() should raise HTTP 400 for an empty file."""
        async def async_read():
            return b""

        mock = MagicMock(spec=UploadFile)
        mock.filename = "empty.png"
        mock.read = async_read

        with pytest.raises(HTTPException) as exc_info:
            await save_upload(mock, uploads_dir=tmp_path, max_bytes=MAX_BYTES)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_save_creates_uploads_dir_if_missing(self, tmp_path: Path):
        """save_upload() should create the uploads dir if it doesn't exist."""
        new_dir = tmp_path / "auto_created"
        assert not new_dir.exists()

        content = _make_real_png()

        async def async_read():
            return content

        mock = MagicMock(spec=UploadFile)
        mock.filename = "test.png"
        mock.read = async_read

        dest = await save_upload(mock, uploads_dir=new_dir, max_bytes=MAX_BYTES)
        assert new_dir.exists()
        assert dest.exists()

    @pytest.mark.asyncio
    async def test_save_preserves_extension(self, tmp_path: Path):
        """save_upload() should preserve the original file extension in the saved name."""
        content = b"fake webp data"

        async def async_read():
            return content

        for ext in [".png", ".jpg", ".webp"]:
            mock = MagicMock(spec=UploadFile)
            mock.filename = f"error{ext}"
            mock.read = async_read
            dest = await save_upload(mock, uploads_dir=tmp_path, max_bytes=MAX_BYTES)
            assert dest.suffix == ext
