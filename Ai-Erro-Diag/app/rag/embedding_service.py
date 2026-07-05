"""
Embedding service using Sentence Transformers.

Wraps the all-MiniLM-L6-v2 model to generate dense vector embeddings
for knowledge base entries and query strings.
"""
from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Generates sentence embeddings using a pre-trained Sentence Transformer model.

    The model is loaded once and reused for all embedding calls to avoid
    repeated initialisation overhead.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """
        Initialise the embedding service.

        Args:
            model_name: HuggingFace model identifier. Defaults to all-MiniLM-L6-v2.
        """
        logger.info("Loading embedding model: %s", model_name)
        self._model = SentenceTransformer(model_name)
        self._model_name = model_name
        logger.info("Embedding model loaded successfully")

    def embed(self, text: str) -> np.ndarray:
        """
        Generate a single embedding vector for a text string.

        Args:
            text: Input text to embed.

        Returns:
            1-D numpy array of shape (embedding_dim,).
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        embedding: np.ndarray = self._model.encode(text, convert_to_numpy=True)
        return embedding

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for a batch of text strings.

        Args:
            texts: List of input strings to embed.

        Returns:
            2-D numpy array of shape (n_texts, embedding_dim).
        """
        if not texts:
            raise ValueError("Cannot embed an empty list of texts")

        logger.debug("Embedding batch of %d texts", len(texts))
        embeddings: np.ndarray = self._model.encode(
            texts, convert_to_numpy=True, show_progress_bar=False
        )
        return embeddings

    @property
    def dimension(self) -> int:
        """Return the embedding dimension for the loaded model."""
        return int(self._model.get_sentence_embedding_dimension())
