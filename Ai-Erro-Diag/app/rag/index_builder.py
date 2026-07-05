"""
FAISS Index Builder Script.

Run this script once to encode all knowledge base JSON files and build
the FAISS vector index:

    python -m app.rag.index_builder

The index and metadata are written to the paths specified in .env
(default: faiss_index/errors.index and faiss_index/metadata.json).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as a script from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.rag.embedding_service import EmbeddingService
from app.rag.faiss_service import FAISSService


def _load_knowledge_base(knowledge_dir: Path) -> list[dict]:
    """
    Load all JSON error records from the knowledge base directory.

    Args:
        knowledge_dir: Path to the directory containing error JSON files.

    Returns:
        Flat list of all error records from all files.
    """
    all_records: list[dict] = []
    json_files = list(knowledge_dir.glob("*.json"))

    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {knowledge_dir}")

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            records = json.load(f)
            if not isinstance(records, list):
                raise ValueError(f"{json_file} must contain a JSON array")
            all_records.extend(records)

    return all_records


def _build_text_for_embedding(record: dict) -> str:
    """
    Combine error record fields into a single text string for embedding.

    Args:
        record: Error knowledge base record dictionary.

    Returns:
        Concatenated text representation.
    """
    steps = " ".join(record.get("troubleshooting_steps", []))
    return (
        f"{record.get('error_name', '')} "
        f"{record.get('description', '')} "
        f"{record.get('root_cause', '')} "
        f"{record.get('solution', '')} "
        f"{steps}"
    ).strip()


def build_index() -> None:
    """Load knowledge base, generate embeddings, and build the FAISS index."""
    configure_logging("INFO")
    logger = get_logger(__name__)
    settings = get_settings()

    logger.info("Starting FAISS index build")
    logger.info("Knowledge base directory: %s", settings.knowledge_base_dir)

    # 1. Load knowledge base
    records = _load_knowledge_base(settings.knowledge_base_dir)
    logger.info("Loaded %d error records from knowledge base", len(records))

    # 2. Generate embeddings
    embedding_service = EmbeddingService(model_name=settings.embedding_model)
    texts = [_build_text_for_embedding(r) for r in records]
    embeddings = embedding_service.embed_batch(texts)
    logger.info(
        "Generated embeddings: shape=%s, dtype=%s",
        embeddings.shape,
        embeddings.dtype,
    )

    # 3. Build and persist FAISS index
    faiss_service = FAISSService(
        index_path=settings.faiss_index_path,
        metadata_path=settings.faiss_metadata_path,
    )
    faiss_service.build_index(embeddings, records)
    logger.info("FAISS index build complete ✓")


if __name__ == "__main__":
    build_index()
