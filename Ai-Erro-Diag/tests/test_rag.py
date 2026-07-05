"""
Tests for EmbeddingService, FAISSService, and RetrievalService.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.rag.embedding_service import EmbeddingService
from app.rag.faiss_service import FAISSService
from app.rag.retrieval_service import RetrievalService
from app.schemas.diagnosis import RetrievedError


# ── EmbeddingService ──────────────────────────────────────────

class TestEmbeddingService:
    """Tests for the SentenceTransformer embedding wrapper."""

    @pytest.fixture(scope="class")
    def embedding_service(self) -> EmbeddingService:
        return EmbeddingService(model_name="all-MiniLM-L6-v2")

    def test_embed_returns_ndarray(self, embedding_service: EmbeddingService):
        """embed() should return a 1-D numpy array."""
        result = embedding_service.embed("ModuleNotFoundError: No module named fastapi")
        assert isinstance(result, np.ndarray)
        assert result.ndim == 1

    def test_embed_dimension_matches(self, embedding_service: EmbeddingService):
        """Embedding dimension should match the model's declared dimension."""
        result = embedding_service.embed("Test error message")
        assert result.shape[0] == embedding_service.dimension

    def test_embed_empty_text_raises(self, embedding_service: EmbeddingService):
        """embed() should raise ValueError for empty string."""
        with pytest.raises(ValueError, match="empty"):
            embedding_service.embed("")

    def test_embed_whitespace_raises(self, embedding_service: EmbeddingService):
        """embed() should raise ValueError for whitespace-only string."""
        with pytest.raises(ValueError, match="empty"):
            embedding_service.embed("   ")

    def test_embed_batch_returns_2d(self, embedding_service: EmbeddingService):
        """embed_batch() should return a 2-D array with correct shape."""
        texts = ["Error one", "Error two", "Error three"]
        result = embedding_service.embed_batch(texts)
        assert isinstance(result, np.ndarray)
        assert result.ndim == 2
        assert result.shape[0] == 3

    def test_embed_batch_empty_raises(self, embedding_service: EmbeddingService):
        """embed_batch() should raise ValueError for empty list."""
        with pytest.raises(ValueError, match="empty"):
            embedding_service.embed_batch([])

    def test_dimension_property(self, embedding_service: EmbeddingService):
        """dimension property should return a positive integer."""
        assert embedding_service.dimension > 0
        assert isinstance(embedding_service.dimension, int)


# ── FAISSService ──────────────────────────────────────────────

class TestFAISSService:
    """Tests for FAISS index build, search, and persistence."""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        return tmp_path

    @pytest.fixture
    def sample_embeddings(self) -> np.ndarray:
        """Generate 10 fake 384-dim embeddings."""
        np.random.seed(42)
        return np.random.rand(10, 384).astype(np.float32)

    @pytest.fixture
    def sample_metadata(self) -> list[dict]:
        return [
            {
                "error_name": f"TestError{i}",
                "description": f"Description of test error {i}",
                "root_cause": f"Root cause {i}",
                "solution": f"Solution {i}",
                "troubleshooting_steps": [f"Step {i}.1", f"Step {i}.2"],
            }
            for i in range(10)
        ]

    @pytest.fixture
    def faiss_service(self, temp_dir: Path) -> FAISSService:
        return FAISSService(
            index_path=temp_dir / "test.index",
            metadata_path=temp_dir / "test_metadata.json",
        )

    def test_is_ready_false_before_build(self, faiss_service: FAISSService):
        """is_ready should be False before any index is built."""
        assert faiss_service.is_ready is False

    def test_build_index_sets_ready(
        self, faiss_service: FAISSService, sample_embeddings, sample_metadata
    ):
        """build_index() should make is_ready True."""
        faiss_service.build_index(sample_embeddings, sample_metadata)
        assert faiss_service.is_ready is True

    def test_build_index_persists_to_disk(
        self, faiss_service: FAISSService, sample_embeddings, sample_metadata, temp_dir: Path
    ):
        """build_index() should write index and metadata files."""
        faiss_service.build_index(sample_embeddings, sample_metadata)
        assert (temp_dir / "test.index").exists()
        assert (temp_dir / "test_metadata.json").exists()

    def test_search_returns_results(
        self, faiss_service: FAISSService, sample_embeddings, sample_metadata
    ):
        """search() should return results after building the index."""
        faiss_service.build_index(sample_embeddings, sample_metadata)
        query = sample_embeddings[0]
        results = faiss_service.search(query, top_k=3)
        assert len(results) <= 3
        assert len(results) > 0

    def test_search_includes_similarity_score(
        self, faiss_service: FAISSService, sample_embeddings, sample_metadata
    ):
        """Each search result should include a similarity_score in [0, 1]."""
        faiss_service.build_index(sample_embeddings, sample_metadata)
        results = faiss_service.search(sample_embeddings[0], top_k=5)
        for r in results:
            assert "similarity_score" in r
            assert 0.0 <= r["similarity_score"] <= 1.0

    def test_search_on_unloaded_index_raises(self, temp_dir: Path):
        """search() before building should raise RuntimeError."""
        service = FAISSService(
            index_path=temp_dir / "nonexistent.index",
            metadata_path=temp_dir / "nonexistent.json",
        )
        query = np.zeros(384, dtype=np.float32)
        with pytest.raises(RuntimeError, match="not loaded"):
            service.search(query, top_k=3)

    def test_build_index_mismatched_lengths_raises(
        self, faiss_service: FAISSService, sample_embeddings
    ):
        """build_index() with mismatched embeddings/metadata lengths should raise."""
        with pytest.raises(ValueError, match="same length"):
            faiss_service.build_index(sample_embeddings, [{"error_name": "only one"}])

    def test_index_loads_from_disk(
        self, temp_dir: Path, sample_embeddings, sample_metadata
    ):
        """A new FAISSService instance should load an existing index from disk."""
        s1 = FAISSService(
            index_path=temp_dir / "idx.index",
            metadata_path=temp_dir / "meta.json",
        )
        s1.build_index(sample_embeddings, sample_metadata)

        s2 = FAISSService(
            index_path=temp_dir / "idx.index",
            metadata_path=temp_dir / "meta.json",
        )
        assert s2.is_ready is True
        results = s2.search(sample_embeddings[0], top_k=3)
        assert len(results) > 0


# ── RetrievalService ──────────────────────────────────────────

class TestRetrievalService:
    """Tests for the composed retrieval pipeline."""

    @pytest.fixture
    def mock_embedding_service(self) -> MagicMock:
        service = MagicMock()
        service.embed.return_value = np.random.rand(384).astype(np.float32)
        return service

    @pytest.fixture
    def mock_faiss_service(self) -> MagicMock:
        service = MagicMock()
        service.is_ready = True
        service.search.return_value = [
            {
                "error_name": "ModuleNotFoundError",
                "description": "Module not found",
                "root_cause": "Package not installed",
                "solution": "pip install the package",
                "troubleshooting_steps": ["Step 1", "Step 2"],
                "similarity_score": 0.9,
            }
        ]
        return service

    def test_retrieve_returns_typed_results(
        self, mock_embedding_service, mock_faiss_service
    ):
        """retrieve() should return a list of RetrievedError instances."""
        service = RetrievalService(
            embedding_service=mock_embedding_service,
            faiss_service=mock_faiss_service,
            top_k=5,
        )
        results = service.retrieve("ModuleNotFoundError: No module named fastapi")
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], RetrievedError)

    def test_retrieve_returns_empty_when_faiss_not_ready(
        self, mock_embedding_service
    ):
        """retrieve() should return empty list when FAISS index is not ready."""
        mock_faiss = MagicMock()
        mock_faiss.is_ready = False
        service = RetrievalService(
            embedding_service=mock_embedding_service,
            faiss_service=mock_faiss,
            top_k=5,
        )
        results = service.retrieve("Some error")
        assert results == []

    def test_retrieve_calls_embed_then_search(
        self, mock_embedding_service, mock_faiss_service
    ):
        """retrieve() should call embed() then search() in sequence."""
        service = RetrievalService(
            embedding_service=mock_embedding_service,
            faiss_service=mock_faiss_service,
            top_k=3,
        )
        service.retrieve("test error")
        mock_embedding_service.embed.assert_called_once_with("test error")
        mock_faiss_service.search.assert_called_once()
