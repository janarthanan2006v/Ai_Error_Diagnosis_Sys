"""
Gemini Diagnosis Service.

Generates a comprehensive error diagnosis by combining extracted vision
results with RAG-retrieved knowledge base context.
"""
from __future__ import annotations

import json
import re

import google.generativeai as genai

from app.core.logging import get_logger
from app.prompts.templates import DIAGNOSIS_SYSTEM_PROMPT, build_diagnosis_prompt
from app.schemas.diagnosis import DiagnosisResult, RetrievedError, VisionAnalysisResult

logger = get_logger(__name__)


class GeminiDiagnosisService:
    """
    Generates structured error diagnoses using Google Gemini.

    Combines Gemini Vision extraction output with RAG-retrieved similar
    errors to produce a context-enriched diagnosis.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash") -> None:
        """
        Initialise the Gemini Diagnosis service.

        Args:
            api_key: Google Gemini API key.
            model_name: Gemini model identifier for text generation.

        Raises:
            ValueError: If the API key is empty.
        """
        if not api_key:
            raise ValueError("Gemini API key must not be empty")

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=DIAGNOSIS_SYSTEM_PROMPT,
        )
        self._model_name = model_name
        logger.info("GeminiDiagnosisService initialised with model: %s", model_name)

    async def generate_diagnosis(
        self,
        vision_result: VisionAnalysisResult,
        retrieved_errors: list[RetrievedError],
    ) -> DiagnosisResult:
        """
        Generate a comprehensive diagnosis using Gemini with RAG augmentation.

        Args:
            vision_result: Structured error data from Gemini Vision analysis.
            retrieved_errors: Similar errors retrieved from the FAISS knowledge base.

        Returns:
            Validated DiagnosisResult with root cause, fix steps, and tips.

        Raises:
            RuntimeError: If the Gemini API call fails.
            ValueError: If the response cannot be parsed into the expected schema.
        """
        prompt = build_diagnosis_prompt(vision_result, retrieved_errors)
        logger.info(
            "Generating diagnosis for error: '%s'",
            vision_result.error_title[:80],
        )
        logger.debug("Retrieved %d context entries for prompt augmentation", len(retrieved_errors))

        try:
            response = self._model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=4096,
                ),
            )
        except Exception as exc:
            logger.error("Gemini Diagnosis API call failed: %s", exc)
            raise RuntimeError(f"Gemini Diagnosis API error: {exc}") from exc

        raw_text = response.text.strip()
        logger.debug("Gemini Diagnosis raw response length: %d chars", len(raw_text))

        return self._parse_diagnosis_response(raw_text)

    def _parse_diagnosis_response(self, raw_text: str) -> DiagnosisResult:
        """
        Parse the raw Gemini text response into a DiagnosisResult.

        Args:
            raw_text: Raw text from the Gemini Diagnosis API call.

        Returns:
            Validated DiagnosisResult instance.

        Raises:
            ValueError: If the response cannot be parsed as valid JSON.
        """
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE).strip()
        cleaned = cleaned.rstrip("`").strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Gemini Diagnosis JSON: %s\nRaw: %s", exc, raw_text[:300])
            raise ValueError(f"Gemini Diagnosis returned invalid JSON: {exc}") from exc

        # Clamp confidence_score within [0.0, 1.0]
        raw_score = float(data.get("confidence_score", 0.7))
        confidence = max(0.0, min(1.0, raw_score))

        return DiagnosisResult(
            error_summary=data.get("error_summary", "Unable to determine error summary"),
            root_cause=data.get("root_cause", "Unable to identify root cause"),
            confidence_score=confidence,
            recommended_fix=data.get("recommended_fix", "Please review the error manually"),
            step_by_step_solution=data.get("step_by_step_solution", []),
            prevention_tips=data.get("prevention_tips", []),
            related_errors=data.get("related_errors", []),
        )
