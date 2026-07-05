"""
Gemini Vision Service.

Sends error screenshots to Google Gemini Vision for OCR, error extraction,
stack trace parsing, language detection, and environment detection.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import google.generativeai as genai
from PIL import Image

from app.core.logging import get_logger
from app.prompts.templates import VISION_SYSTEM_PROMPT, VISION_USER_PROMPT
from app.schemas.diagnosis import VisionAnalysisResult

logger = get_logger(__name__)

# Supported image formats
SUPPORTED_MIME_TYPES: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


class GeminiVisionService:
    """
    Analyses error screenshots using Google Gemini Vision API.

    Extracts:
    - Error title and message
    - Programming language
    - Framework or library
    - Runtime environment
    - Raw stack trace
    """

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash") -> None:
        """
        Initialise the Gemini Vision service.

        Args:
            api_key: Google Gemini API key.
            model_name: Gemini model identifier to use for vision analysis.

        Raises:
            ValueError: If the API key is empty.
        """
        if not api_key:
            raise ValueError("Gemini API key must not be empty")

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=VISION_SYSTEM_PROMPT,
        )
        self._model_name = model_name
        logger.info("GeminiVisionService initialised with model: %s", model_name)

    async def analyse_screenshot(self, image_path: Path) -> VisionAnalysisResult:
        """
        Analyse an error screenshot and extract structured error information.

        Args:
            image_path: Path to the uploaded image file on disk.

        Returns:
            VisionAnalysisResult containing extracted error details.

        Raises:
            FileNotFoundError: If the image file does not exist.
            ValueError: If the image format is not supported or parsing fails.
            RuntimeError: If the Gemini API call fails.
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        suffix = image_path.suffix.lower()
        if suffix not in SUPPORTED_MIME_TYPES:
            raise ValueError(
                f"Unsupported image format: {suffix}. "
                f"Supported: {list(SUPPORTED_MIME_TYPES.keys())}"
            )

        logger.info("Analysing screenshot: %s", image_path.name)

        try:
            image = Image.open(image_path)
            response = self._model.generate_content(
                [VISION_USER_PROMPT, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048,
                ),
            )
        except Exception as exc:
            logger.error("Gemini Vision API call failed: %s", exc)
            raise RuntimeError(f"Gemini Vision API error: {exc}") from exc

        raw_text = response.text.strip()
        logger.debug("Gemini Vision raw response: %s", raw_text[:500])

        return self._parse_vision_response(raw_text)

    def _parse_vision_response(self, raw_text: str) -> VisionAnalysisResult:
        """
        Parse the raw Gemini response into a VisionAnalysisResult.

        Args:
            raw_text: Raw text from the Gemini API response.

        Returns:
            Validated VisionAnalysisResult instance.

        Raises:
            ValueError: If the response cannot be parsed as valid JSON.
        """
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE).strip()
        cleaned = cleaned.rstrip("`").strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Gemini Vision JSON: %s\nRaw: %s", exc, raw_text[:300])
            raise ValueError(f"Gemini Vision returned invalid JSON: {exc}") from exc

        return VisionAnalysisResult(
            error_title=data.get("error_title", "Unknown Error"),
            error_message=data.get("error_message", ""),
            language=data.get("language", "Unknown"),
            framework=data.get("framework", "None"),
            environment=data.get("environment", "Unknown"),
            raw_stacktrace=data.get("raw_stacktrace", ""),
        )
