"""Blackbox tests for the embeddings module.

Tests embedding generation without testing internal model weights.
"""

from __future__ import annotations

import numpy as np
import pytest

from engram import embeddings


def test_get_model_name():
    """Test that model name is correctly returned."""
    name = embeddings.get_model_name()
    assert name == "all-MiniLM-L6-v2"


def test_get_model_version():
    """Test that model version is captured after first use."""
    version = embeddings.get_model_version()
    assert isinstance(version, str)
    assert len(version) > 0


def test_encode_returns_vector():
    """Test that encode returns a numpy array of expected size."""
    text = "This is a test sentence for embedding"
    result = embeddings.encode(text)

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    assert result.shape == (384,)


def test_encode_empty_string():
    """Test encoding empty string."""
    result = embeddings.encode("")

    assert isinstance(result, np.ndarray)
    assert result.shape == (384,)


def test_encode_normalizes():
    """Test that embeddings are normalized (L2=1)."""
    text = "Testing normalization"
    emb = embeddings.encode(text)

    norm = np.linalg.norm(emb)
    assert np.isclose(norm, 1.0, atol=1e-5)


def test_embedding_to_bytes_roundtrip():
    """Test serialization/deserialization roundtrip."""
    original = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)

    data = embeddings.embedding_to_bytes(original)
    restored = embeddings.bytes_to_embedding(data)

    np.testing.assert_array_almost_equal(original, restored)


def test_bytes_to_embedding_invalid():
    """Test that invalid bytes raises error."""
    invalid_data = b"not enough bytes"

    with pytest.raises(ValueError):
        embeddings.bytes_to_embedding(invalid_data)


def test_cosine_similarity_identical():
    """Test cosine similarity of identical vectors."""
    v = np.array([1.0, 0.0], dtype=np.float32)

    sim = embeddings.cosine_similarity(v, v)
    assert np.isclose(sim, 1.0)


def test_cosine_similarity_orthogonal():
    """Test cosine similarity of orthogonal vectors."""
    v1 = np.array([1.0, 0.0], dtype=np.float32)
    v2 = np.array([0.0, 1.0], dtype=np.float32)

    sim = embeddings.cosine_similarity(v1, v2)
    assert np.isclose(sim, 0.0)


def test_cosine_similarity_opposite():
    """Test cosine similarity of opposite vectors."""
    v1 = np.array([1.0, 0.0], dtype=np.float32)
    v2 = np.array([-1.0, 0.0], dtype=np.float32)

    sim = embeddings.cosine_similarity(v1, v2)
    assert np.isclose(sim, -1.0)


def test_cosine_similarity_batch_empty():
    """Test batch similarity with empty list."""
    query = np.array([1.0, 0.0], dtype=np.float32)

    result = embeddings.cosine_similarity_batch(query, [])
    assert result == []


def test_cosine_similarity_batch_multiple():
    """Test batch similarity with multiple candidates."""
    query = np.array([1.0, 0.0], dtype=np.float32)
    candidates = [
        np.array([1.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.0], dtype=np.float32),
        np.array([0.707, 0.707], dtype=np.float32),
    ]

    result = embeddings.cosine_similarity_batch(query, candidates)

    assert len(result) == 3
    assert np.isclose(result[0], 1.0)
    assert np.isclose(result[1], 0.0)
    assert np.isclose(result[2], 0.707, atol=0.01)