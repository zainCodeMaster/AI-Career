"""Text chunker for Career Brain documents.

Deterministic, whitespace-normalizing character-based chunker with overlap.
Career profile data is generally short, so defaults are conservative.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """A single chunk of text derived from a larger document."""

    text: str
    index: int


class TextChunker:
    """Split text into overlapping chunks of roughly equal size."""

    _WHITESPACE = re.compile(r"\s+")

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _normalize(self, text: str) -> str:
        # Collapse all whitespace runs to a single space, strip ends.
        return self._WHITESPACE.sub(" ", text).strip()

    def split(self, text: str, max_chunks: int | None = None) -> list[Chunk]:
        """Split text into chunks. Empty text returns no chunks.

        If ``max_chunks`` is set, the result is truncated to that many chunks
        (the first N). This prevents pathological documents from producing
        hundreds of tiny chunks.
        """
        normalized = self._normalize(text)
        if not normalized:
            return []

        if len(normalized) <= self.chunk_size:
            chunks = [Chunk(text=normalized, index=0)]
            return chunks[:max_chunks] if max_chunks else chunks

        step = self.chunk_size - self.chunk_overlap
        chunks: list[Chunk] = []
        start = 0
        idx = 0
        while start < len(normalized):
            end = min(start + self.chunk_size, len(normalized))
            piece = normalized[start:end].strip()
            if piece:
                chunks.append(Chunk(text=piece, index=idx))
                idx += 1
            if end >= len(normalized):
                break
            start += step
            if max_chunks and len(chunks) >= max_chunks:
                break

        return chunks
