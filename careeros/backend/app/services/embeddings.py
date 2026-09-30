"""Embedding provider abstraction and local hash-based implementation.

The abstract ``EmbeddingProvider`` defines the contract for converting text to
fixed-dimensional float vectors. This module provides a local, deterministic
hash-based provider that works fully offline — useful for development, tests,
and environments where a transformer model cannot be downloaded.

A future ``SentenceTransformerEmbeddingProvider`` (e.g. backed by
sentence-transformers/all-MiniLM-L6-v2) can be plugged in by implementing the
same interface and switching ``settings.embedding_provider``.
"""
from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod
from typing import Sequence

import numpy as np


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string. Must reject empty text."""

    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of texts. Empty texts must be rejected."""


_TOKEN_RE = re.compile(r"[A-Za-z0-9_\-]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text) if t]


class HashEmbeddingProvider(EmbeddingProvider):
    """Deterministic, fully local hash-based embedding provider.

    This is NOT a semantic model. It produces deterministic vectors based on
    token-hash bucketing. It is intentionally simple:

    - No network access.
    - No model download.
    - Deterministic for the same input.
    - Reasonable enough for token-overlap retrieval during development.

    It is designed to be replaced by a real semantic provider (e.g. a
    sentence-transformers model) without changing the rest of the system.
    """

    def __init__(self, dimension: int = 384) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be > 0")
        self._dimension = dimension

    @property
    def model_name(self) -> str:
        return "local-hash-384"

    @property
    def dimension(self) -> int:
        return self._dimension

    def _embed_tokens(self, tokens: Sequence[str]) -> np.ndarray:
        vec = np.zeros(self._dimension, dtype=np.float32)
        if not tokens:
            return vec
        for token in tokens:
            h = hashlib.sha256(token.encode("utf-8")).digest()
            # Use 4 bytes -> 32-bit integer -> bucket index.
            bucket = int.from_bytes(h[:4], "big") % self._dimension
            sign = 1.0 if (h[4] & 1) else -1.0
            vec[bucket] += sign
        # L2 normalise for cosine similarity via dot product.
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        tokens = _tokenize(text)
        return self._embed_tokens(tokens).tolist()

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if any((not t) or (not str(t).strip()) for t in texts):
            raise ValueError("Cannot embed empty text")
        return [self.embed_text(t) for t in texts]


def get_embedding_provider() -> EmbeddingProvider:
    """Factory: return the configured embedding provider.

    Currently only the local hash provider is wired. The settings.embedding_provider
    value is checked so future providers (e.g. ``sentence-transformers``) can be
    selected via configuration without changing call sites.
    """
    from app.core.config import get_settings

    settings = get_settings()
    name = (settings.embedding_provider or "local").lower()
    if name in ("local", "hash", "local-hash", "local-hash-384"):
        dim = int(settings.embedding_dimension or 384)
        return HashEmbeddingProvider(dimension=dim)
    # Unknown provider — fall back to local rather than crashing.
    return HashEmbeddingProvider(dimension=int(settings.embedding_dimension or 384))
