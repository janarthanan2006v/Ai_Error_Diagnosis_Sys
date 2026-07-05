"""
FAISS vector index service.

Handles building, persisting, loading, and searching the FAISS index
that stores knowledge base embeddings.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from app.core.logging import get_logger

logger = get_logger(__name__)


class FAISSService:
    """
    Manages a FAISS flat L2 vector index for similarity search over
    knowledge base error embeddings.
    """

    def __init__(self, index_path: Path, metadata_path: Path) -> None:
        """
        Initialise the FAISS service.

        Args:
            index_path: Path where the FAISS index binary is stored.
            metadata_path: Path where the JSON metadata (error records) is stored.
        """
        self._index_path = index_path
        self._metadata_path = metadata_path
        self._index: faiss.IndexFlatL2 | None = None
        self._metadata: list[dict[str, Any]] = []

        if index_path.exists() and metadata_path.exists():
            self._load_index()

    # ── Build ────────────────────────────────────────────────────────────────

    def build_index(
        self,
        embeddings: np.ndarray,
        metadata: list[dict[str, Any]],
    ) -> None:
        """
        Build and persist a new FAISS index from embeddings and metadata.

        Args:
            embeddings: 2-D float32 numpy array of shape (n, dim).
            metadata: Parallel list of dicts with error records.

        Raises:
            ValueError: If embeddings and metadata lengths differ.
        """
        if len(embeddings) != len(metadata):
            raise ValueError(
                f"Embeddings ({len(embeddings)}) and metadata ({len(metadata)}) "
                "must have the same length"
            )

        embeddings_f32 = np.array(embeddings, dtype=np.float32)
        dimension = embeddings_f32.shape[1]

        logger.info("Building FAISS index with %d vectors (dim=%d)", len(embeddings), dimension)

        self._index = faiss.IndexFlatL2(dimension)
        self._index.add(embeddings_f32)
        self._metadata = metadata

        self._save_index()
        logger.info("FAISS index built and saved to %s", self._index_path)

    # ── Search ───────────────────────────────────────────────────────────────

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top-k most similar errors to the query vector.

        Args:
            query_vector: 1-D float32 numpy array of shape (dim,).
            top_k: Number of nearest neighbours to retrieve.

        Returns:
            List of metadata dicts with an added `similarity_score` field.

        Raises:
            RuntimeError: If the index has not been loaded or built.
        """
        if self._index is None:
            raise RuntimeError(
                "FAISS index is not loaded. Run the index builder script first."
            )

        query = np.array([query_vector], dtype=np.float32)
        distances, indices = self._index.search(query, min(top_k, self._index.ntotal))

        results: list[dict[str, Any]] = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            record = dict(self._metadata[idx])
            # Convert L2 distance to a similarity score in [0, 1]
            record["similarity_score"] = float(1.0 / (1.0 + distance))
            results.append(record)

        return results

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_index(self) -> None:
        """Persist the FAISS index and metadata to disk."""
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self._index_path))

        with open(self._metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, indent=2, ensure_ascii=False)

        logger.info("FAISS index saved: %s", self._index_path)

    def _load_index(self) -> None:
        """Load a persisted FAISS index and its metadata from disk."""
        logger.info("Loading FAISS index from %s", self._index_path)
        self._index = faiss.read_index(str(self._index_path))

        with open(self._metadata_path, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)

        logger.info(
            "FAISS index loaded: %d vectors, %d metadata records",
            self._index.ntotal,
            len(self._metadata),
        )

    @property
    def is_ready(self) -> bool:
        """Return True if the index is loaded and contains vectors."""
        return self._index is not None and self._index.ntotal > 0
