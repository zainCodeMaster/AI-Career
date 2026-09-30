"""Vector store abstraction for Career Brain chunks.

Defines a ``VectorStore`` interface that is implemented by:

- ``PgVectorVectorStore`` — production: uses PostgreSQL + pgvector's ``<=>``
  cosine-distance operator via raw SQL.
- ``InMemoryVectorStore`` — tests / SQLite fallback: fetches user-scoped
  candidates from the database and computes cosine similarity in Python with
  numpy.

Both implementations are strictly user-scoped: every operation requires
``user_id`` and filters by it. There is no global search API.
"""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

import numpy as np
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.career_brain import CareerBrainChunk


@dataclass(frozen=True)
class StoredVector:
    """A vector stored in the vector store."""

    id: str
    user_id: str
    source_type: str
    source_id: str
    title: str | None
    content: str
    embedding: list[float]


@dataclass(frozen=True)
class SearchHit:
    """A single search result with similarity score."""

    id: str
    source_type: str
    source_id: str
    title: str | None
    content: str
    score: float


class VectorStore(ABC):
    """Abstract vector store. Every method is user-scoped."""

    @abstractmethod
    def upsert_chunks(self, db: Session, user_id: UUID, chunks: Sequence[StoredVector]) -> int:
        """Insert or update chunks for the user. Returns the number of rows written."""

    @abstractmethod
    def delete_for_source(self, db: Session, user_id: UUID, source_type: str, source_id: str) -> int:
        """Delete all chunks belonging to a (source_type, source_id) for the user."""

    @abstractmethod
    def search(self, db: Session, user_id: UUID, query_embedding: list[float], top_k: int) -> list[SearchHit]:
        """User-scoped similarity search. Must never return another user's data."""

    @abstractmethod
    def count_for_user(self, db: Session, user_id: UUID) -> int:
        """Return the number of stored chunks for the user."""


# ---------------------------------------------------------------------------
# Production implementation: PostgreSQL + pgvector
# ---------------------------------------------------------------------------


class PgVectorVectorStore(VectorStore):
    """pgvector-backed vector store using the ``<=>`` cosine distance operator.

    The production database URL must point to a PostgreSQL instance with the
    ``vector`` extension enabled. The Alembic migration creates the extension
    and the ``career_brain_chunks`` table.
    """

    def upsert_chunks(self, db: Session, user_id: UUID, chunks: Sequence[StoredVector]) -> int:
        if not chunks:
            return 0
        # Strategy: delete existing chunks for each (user, source_type, source_id)
        # then insert fresh ones. This is simple, correct, and avoids the need
        # for ON CONFLICT semantics on the pgvector column.
        by_source: dict[tuple[str, str], list[StoredVector]] = {}
        for c in chunks:
            by_source.setdefault((c.source_type, c.source_id), []).append(c)

        written = 0
        for (source_type, source_id), group in by_source.items():
            source_uuid = _to_uuid(source_id)
            db.execute(
                delete(CareerBrainChunk).where(
                    CareerBrainChunk.user_id == user_id,
                    CareerBrainChunk.source_type == source_type,
                    CareerBrainChunk.source_id == source_uuid,
                )
            )
            for c in group:
                db.add(
                    CareerBrainChunk(
                        user_id=user_id,
                        source_type=c.source_type,
                        source_id=_to_uuid(c.source_id),
                        title=c.title,
                        content=c.content,
                        content_hash=_content_hash(c.content),
                        chunk_index=int(c.id.split(":")[-1]) if ":" in c.id else 0,
                        embedding_model="local",
                        embedding_dimension=len(c.embedding),
                        embedding=c.embedding,
                    )
                )
                written += 1
        db.commit()
        return written

    def delete_for_source(self, db: Session, user_id: UUID, source_type: str, source_id: str) -> int:
        result = db.execute(
            delete(CareerBrainChunk).where(
                CareerBrainChunk.user_id == user_id,
                CareerBrainChunk.source_type == source_type,
                CareerBrainChunk.source_id == _to_uuid(source_id),
            )
        )
        db.commit()
        return int(result.rowcount or 0)

    def search(self, db: Session, user_id: UUID, query_embedding: list[float], top_k: int) -> list[SearchHit]:
        if top_k <= 0:
            return []
        # pgvector cosine distance operator: ``embedding <=> :query``
        # Smaller distance = more similar. We convert to a similarity score
        # in [0, 1] via ``1 - distance`` (clamped).
        distance = CareerBrainChunk.embedding.cosine_distance(query_embedding)
        stmt = (
            select(
                CareerBrainChunk.id,
                CareerBrainChunk.source_type,
                CareerBrainChunk.source_id,
                CareerBrainChunk.title,
                CareerBrainChunk.content,
                distance.label("dist"),
            )
            .where(CareerBrainChunk.user_id == user_id)
            .order_by(distance)
            .limit(top_k)
        )
        rows = db.execute(stmt).all()
        hits: list[SearchHit] = []
        for row in rows:
            dist = float(row.dist)
            score = max(0.0, min(1.0, 1.0 - dist))
            hits.append(
                SearchHit(
                    id=str(row.id),
                    source_type=row.source_type,
                    source_id=str(row.source_id),
                    title=row.title,
                    content=row.content,
                    score=score,
                )
            )
        return hits

    def count_for_user(self, db: Session, user_id: UUID) -> int:
        stmt = select(CareerBrainChunk.id).where(CareerBrainChunk.user_id == user_id)
        return len(db.execute(stmt).all())


# ---------------------------------------------------------------------------
# Test / SQLite fallback implementation
# ---------------------------------------------------------------------------


class InMemoryVectorStore(VectorStore):
    """In-process cosine-similarity implementation.

    Used when the database backend is SQLite (tests). Fetches user-scoped
    candidates via SQLAlchemy and computes cosine similarity in Python with
    numpy. Strictly user-scoped; cannot return another user's data.
    """

    def upsert_chunks(self, db: Session, user_id: UUID, chunks: Sequence[StoredVector]) -> int:
        if not chunks:
            return 0
        by_source: dict[tuple[str, str], list[StoredVector]] = {}
        for c in chunks:
            by_source.setdefault((c.source_type, c.source_id), []).append(c)
        written = 0
        for (source_type, source_id), group in by_source.items():
            source_uuid = _to_uuid(source_id)
            db.execute(
                delete(CareerBrainChunk).where(
                    CareerBrainChunk.user_id == user_id,
                    CareerBrainChunk.source_type == source_type,
                    CareerBrainChunk.source_id == source_uuid,
                )
            )
            for c in group:
                idx = int(c.id.split(":")[-1]) if ":" in c.id else 0
                db.add(
                    CareerBrainChunk(
                        user_id=user_id,
                        source_type=c.source_type,
                        source_id=_to_uuid(c.source_id),
                        title=c.title,
                        content=c.content,
                        content_hash=_content_hash(c.content),
                        chunk_index=idx,
                        embedding_model="local",
                        embedding_dimension=len(c.embedding),
                        embedding=c.embedding,
                    )
                )
                written += 1
        db.commit()
        return written

    def delete_for_source(self, db: Session, user_id: UUID, source_type: str, source_id: str) -> int:
        result = db.execute(
            delete(CareerBrainChunk).where(
                CareerBrainChunk.user_id == user_id,
                CareerBrainChunk.source_type == source_type,
                CareerBrainChunk.source_id == _to_uuid(source_id),
            )
        )
        db.commit()
        return int(result.rowcount or 0)

    def search(self, db: Session, user_id: UUID, query_embedding: list[float], top_k: int) -> list[SearchHit]:
        if top_k <= 0:
            return []
        # Use raw SQL via the session. The pgvector Vector type on SQLite can
        # interfere with ORM row materialization when the result set includes
        # the Vector column alongside UUID columns. A raw SELECT bypasses the
        # ORM's type coercion.
        # The user_id / source_id UUID columns are stored by the PostgreSQL
        # dialect's bind processor as their integer representation on SQLite,
        # so we match the bind format and reconstruct UUIDs from the int
        # values returned by the driver.
        from sqlalchemy import text
        result = db.execute(
            text(
                "SELECT id, source_type, source_id, title, content, embedding "
                "FROM career_brain_chunks WHERE user_id = :uid"
            ),
            {"uid": str(user_id).replace("-", "")},
        )
        rows = result.fetchall()
        if not rows:
            return []
        q = np.asarray(query_embedding, dtype=np.float32)
        q_norm = float(np.linalg.norm(q))
        if q_norm == 0:
            return []
        scored: list[SearchHit] = []
        for row in rows:
            raw_emb = row.embedding
            if isinstance(raw_emb, str):
                import json
                raw_emb = json.loads(raw_emb)
            v = np.asarray(raw_emb, dtype=np.float32)
            v_norm = float(np.linalg.norm(v))
            if v_norm == 0:
                continue
            score = float(np.dot(q, v) / (q_norm * v_norm))
            score = max(0.0, min(1.0, score))
            raw_source_id = row.source_id
            if isinstance(raw_source_id, int):
                source_id_str = str(UUID(int=raw_source_id))
            else:
                source_id_str = str(raw_source_id)
            scored.append(
                SearchHit(
                    id=str(row.id),
                    source_type=row.source_type,
                    source_id=source_id_str,
                    title=row.title,
                    content=row.content,
                    score=score,
                )
            )
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]

    def count_for_user(self, db: Session, user_id: UUID) -> int:
        stmt = select(CareerBrainChunk.id).where(CareerBrainChunk.user_id == user_id)
        return len(db.execute(stmt).all())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _to_uuid(value: str | UUID) -> UUID:
    """Coerce a string to UUID. The ``source_id`` may be passed as a string
    from dataclass-based ``StoredVector`` objects; the database column is
    ``UUID(as_uuid=True)`` and requires a UUID object for safe binding."""
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def get_vector_store() -> VectorStore:
    """Factory: return the configured vector store.

    - ``pgvector`` (default) → ``PgVectorVectorStore`` for production.
    - ``in_memory`` → ``InMemoryVectorStore`` (used in tests / SQLite).

    SQLite tests are detected at runtime and transparently fall back to the
    in-memory store so the test suite does not require PostgreSQL.
    """
    from app.core.config import get_settings
    from app.db.database import engine

    settings = get_settings()
    backend = (settings.vector_store_backend or "pgvector").lower()
    url = (engine.url.get_backend_name() if engine is not None else "").lower()
    if "sqlite" in url or backend == "in_memory":
        return InMemoryVectorStore()
    return PgVectorVectorStore()
