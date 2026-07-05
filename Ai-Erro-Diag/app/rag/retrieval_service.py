"""
Retrieval service that composes EmbeddingService and FAISSService.

Provides a single entry point for the RAG retrieval step:
  1. Embed the query string.
  2. Search the FAISS index.
  3. Return typed RetrievedError schema objects.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.rag.embedding_service import EmbeddingService
from app.rag.faiss_service import FAISSService
from app.schemas.diagnosis import RetrievedError

logger = get_logger(__name__)


class RetrievalService:
    """
    Orchestrates embedding + FAISS search to retrieve similar errors from
    the knowledge base.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        faiss_service: FAISSService,
        top_k: int = 5,
    ) -> None:
        """
        Initialise the retrieval service.

        Args:
            embedding_service: Service for generating text embeddings.
            faiss_service: Service for vector similarity search.
            top_k: Number of results to retrieve per query.
        """
        self._embedding_service = embedding_service
        self._faiss_service = faiss_service
        self._top_k = top_k

    def retrieve(self, query: str) -> list[RetrievedError]:
        """
        Retrieve the most similar errors from the knowledge base.

        Args:
            query: Natural language query, typically the extracted error message.

        Returns:
            List of RetrievedError instances ordered by similarity (descending).

        Raises:
            RuntimeError: If the FAISS index is not ready.
        """
        if not self._faiss_service.is_ready:
            logger.warning("FAISS index not ready — returning empty retrieval results")
            return []

        logger.debug("Embedding query for FAISS search")
        query_vector = self._embedding_service.embed(query)

        raw_results = self._faiss_service.search(query_vector, top_k=self._top_k)
        logger.info("Retrieved %d similar errors from knowledge base", len(raw_results))

        retrieved: list[RetrievedError] = []
        for record in raw_results:
            try:
                retrieved.append(
                    RetrievedError(
                        error_name=record.get("error_name", "Unknown"),
                        description=record.get("description", ""),
                        root_cause=record.get("root_cause", ""),
                        solution=record.get("solution", ""),
                        troubleshooting_steps=record.get("troubleshooting_steps", []),
                        similarity_score=record.get("similarity_score", 0.0),
                    )
                )
            except Exception as exc:
                logger.warning("Failed to parse retrieved record: %s", exc)

        return retrieved
