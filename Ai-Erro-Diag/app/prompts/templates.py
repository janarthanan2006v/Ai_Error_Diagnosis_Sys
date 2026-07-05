"""
Prompt templates for Gemini Vision and Diagnosis services.

All prompts are defined as module-level constants and pure functions.
They are never constructed inline inside service classes to keep
prompts maintainable and version-controllable independently.
"""
from __future__ import annotations

from app.schemas.diagnosis import RetrievedError, VisionAnalysisResult

# ── Vision Prompt ─────────────────────────────────────────────────────────────

VISION_SYSTEM_PROMPT = """You are an expert software error analyst with deep expertise in:
- Programming languages: Python, JavaScript, TypeScript, Java, Go, Rust, C++
- Frameworks: FastAPI, Django, Flask, React, Next.js, Node.js, Spring Boot
- Databases: PostgreSQL, MySQL, MongoDB, Redis
- Infrastructure: Docker, Kubernetes, AWS, GCP, Linux
- Development tools: VS Code, PyCharm, IntelliJ IDEA, browser DevTools

Your task is to analyze the provided error screenshot and extract structured information.

CRITICAL INSTRUCTIONS:
1. Read ALL text visible in the image carefully.
2. Extract the COMPLETE error message and stack trace.
3. Identify the programming language from syntax, imports, or file extensions.
4. Detect the framework from package names, error messages, or file paths.
5. Determine the environment from terminal prompts, IDE themes, or browser chrome.

You MUST respond ONLY with a valid JSON object. No markdown, no explanations, no code blocks.

Required JSON structure:
{
  "error_title": "Short descriptive title of the error",
  "error_message": "Complete error message as shown in the image",
  "language": "Programming language (Python/JavaScript/Java/etc or 'Unknown')",
  "framework": "Framework or library name (FastAPI/React/etc or 'None')",
  "environment": "Runtime environment (Linux terminal/VS Code/Browser/Docker/etc)",
  "raw_stacktrace": "Full stack trace text extracted from the image, or empty string if not present"
}"""

VISION_USER_PROMPT = """Analyze this error screenshot and extract all error information.

Return ONLY a JSON object with these exact keys:
- error_title
- error_message
- language
- framework
- environment
- raw_stacktrace

Do not include any text before or after the JSON."""


# ── Diagnosis Prompt ──────────────────────────────────────────────────────────

DIAGNOSIS_SYSTEM_PROMPT = """You are a Senior Software Engineer and debugging expert. 
Your role is to provide precise, actionable error diagnoses based on error information 
and relevant knowledge base context.

Your analysis must be:
- Technically accurate and specific
- Based on the provided error and context
- Actionable with concrete steps
- Honest about confidence levels

You MUST respond ONLY with a valid JSON object. No markdown, no explanations outside the JSON.

Required JSON structure:
{
  "error_summary": "Clear 1-2 sentence summary of what went wrong",
  "root_cause": "Precise technical explanation of the root cause",
  "confidence_score": 0.85,
  "recommended_fix": "Primary recommended action to resolve the error",
  "step_by_step_solution": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "prevention_tips": [
    "Tip 1: ...",
    "Tip 2: ..."
  ],
  "related_errors": [
    "RelatedError1",
    "RelatedError2"
  ]
}

The confidence_score must be a float between 0.0 and 1.0."""


def build_diagnosis_prompt(
    vision_result: VisionAnalysisResult,
    retrieved_errors: list[RetrievedError],
) -> str:
    """
    Build the augmented diagnosis prompt by combining the vision result
    with RAG-retrieved knowledge base context.

    Args:
        vision_result: Structured error information from Gemini Vision.
        retrieved_errors: Similar errors retrieved from the FAISS index.

    Returns:
        Complete prompt string for the Gemini Diagnosis model.
    """
    # Format retrieved context
    context_blocks: list[str] = []
    for i, error in enumerate(retrieved_errors, start=1):
        steps = "\n".join(f"  {j}. {s}" for j, s in enumerate(error.troubleshooting_steps, 1))
        block = (
            f"[Knowledge Base Entry {i}] (similarity: {error.similarity_score:.2f})\n"
            f"Error: {error.error_name}\n"
            f"Description: {error.description}\n"
            f"Root Cause: {error.root_cause}\n"
            f"Solution: {error.solution}\n"
            f"Troubleshooting Steps:\n{steps}"
        )
        context_blocks.append(block)

    context_section = (
        "\n\n".join(context_blocks)
        if context_blocks
        else "No similar errors found in the knowledge base."
    )

    prompt = f"""Analyze the following software error and provide a comprehensive diagnosis.

## ERROR INFORMATION (from screenshot analysis)

Error Title: {vision_result.error_title}
Error Message: {vision_result.error_message}
Programming Language: {vision_result.language}
Framework/Library: {vision_result.framework}
Environment: {vision_result.environment}
Stack Trace:
{vision_result.raw_stacktrace or "No stack trace available"}

## RELEVANT KNOWLEDGE BASE CONTEXT

{context_section}

## INSTRUCTIONS

Based on the error information and the knowledge base context above:

1. Identify the precise root cause of this error.
2. Determine your confidence score (0.0–1.0) based on how clear the error is.
3. Provide the single best recommended fix.
4. List concrete step-by-step resolution steps (minimum 3, maximum 8 steps).
5. Provide prevention tips to avoid this error in the future (minimum 2 tips).
6. List related error types that developers should be aware of.

Respond ONLY with a valid JSON object matching the required structure. No additional text."""

    return prompt
