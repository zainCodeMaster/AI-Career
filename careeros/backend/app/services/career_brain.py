"""Career Brain services: indexer, retriever, and RAG context builder.

These services orchestrate the document builder, chunker, embedding provider,
and vector store to provide a clean public API for the API layer.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.career_brain import CareerBrainChunk
from app.db.models.certification import Certification
from app.db.models.education import Education
from app.db.models.skill import Skill
from app.db.models.work_experience import WorkExperience
from app.services.chunker import TextChunker
from app.services.document_builder import CareerDocumentBuilder, CareerDocument
from app.services.embeddings import get_embedding_provider
from app.services.vector_store import StoredVector, get_vector_store


def _to_uuid(value: str | UUID) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


# ---------------------------------------------------------------------------
# Indexer
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IndexResult:
    documents_processed: int
    chunks_created: int
    embeddings_created: int
    embeddings_reused: int


class CareerBrainIndexer:
    """Build, chunk, embed, and persist a user's career data."""

    def __init__(self) -> None:
        settings = get_settings()
        self._chunker = TextChunker(
            chunk_size=int(settings.career_brain_chunk_size),
            chunk_overlap=int(settings.career_brain_chunk_overlap),
        )
        self._max_chunks_per_doc = int(settings.career_brain_max_chunks_per_doc)
        self._builder = CareerDocumentBuilder()
        self._embeddings = get_embedding_provider()
        self._store = get_vector_store()

    @property
    def embedding_model(self) -> str:
        return self._embeddings.model_name

    def index_user(self, db: Session, user_id: UUID) -> IndexResult:
        """Rebuild the semantic index for the given user.

        Re-indexing is safe: existing chunks for each (source_type, source_id)
        are replaced atomically inside the vector store. If nothing has changed
        the resulting rows are still written (re-embedded), but the content
        hashes are stable so callers can detect no-op runs.
        """
        documents = self._builder.build(db, user_id)
        if not documents:
            return IndexResult(0, 0, 0, 0)

        total_chunks = 0
        total_created = 0
        total_reused = 0

        for doc in documents:
            chunks = self._chunker.split(doc.content, max_chunks=self._max_chunks_per_doc)
            if not chunks:
                continue
            total_chunks += len(chunks)

            # Check for existing chunks with the same content hashes
            # (re-indexing where content did not change).
            source_uuid = _to_uuid(doc.source_id)
            existing_hashes = {
                row.content_hash
                for row in db.query(CareerBrainChunk).filter(
                    CareerBrainChunk.user_id == user_id,
                    CareerBrainChunk.source_type == doc.source_type,
                    CareerBrainChunk.source_id == source_uuid,
                ).all()
            }

            # Compute hashes for new chunks.
            new_hashes = {hashlib.sha256(c.text.encode("utf-8")).hexdigest() for c in chunks}
            reused = len(existing_hashes & new_hashes)
            created = len(new_hashes) - reused
            total_reused += reused
            total_created += created

            # Generate embeddings for all chunks (created + reused; the store
            # replaces existing rows for this source, so we always write).
            texts = [c.text for c in chunks]
            embeddings = self._embeddings.embed_documents(texts)

            vectors = [
                StoredVector(
                    id=f"{doc.stable_id()}:{chunk.index}",
                    user_id=str(user_id),
                    source_type=doc.source_type,
                    source_id=doc.source_id,
                    title=doc.title,
                    content=chunk.text,
                    embedding=embeddings[i],
                )
                for i, chunk in enumerate(chunks)
            ]
            self._store.upsert_chunks(db, user_id, vectors)

        return IndexResult(
            documents_processed=len(documents),
            chunks_created=total_chunks,
            embeddings_created=total_created,
            embeddings_reused=total_reused,
        )


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    source_type: str
    source_id: str
    title: str | None
    content: str
    score: float


class CareerBrainRetriever:
    """Embed a query and perform user-scoped similarity search."""

    def __init__(self) -> None:
        self._embeddings = get_embedding_provider()
        self._store = get_vector_store()

    def search(self, db: Session, user_id: UUID, query: str, top_k: int) -> list[RetrievedChunk]:
        if top_k <= 0:
            return []
        query_embedding = self._embeddings.embed_text(query)
        hits = self._store.search(db, user_id, query_embedding, top_k)
        return [
            RetrievedChunk(
                id=h.id,
                source_type=h.source_type,
                source_id=h.source_id,
                title=h.title,
                content=h.content,
                score=h.score,
            )
            for h in hits
        ]


# ---------------------------------------------------------------------------
# RAG context builder
# ---------------------------------------------------------------------------


class RAGContextBuilder:
    """Format retrieved chunks into a deterministic, LLM-ready context string.

    The context groups chunks by source_type and orders groups in a stable
    order so that the same query against the same index produces the same
    context string. This is important for reproducibility and for testing.
    """

    _GROUP_ORDER: Sequence[str] = (
        "profile",
        "experience",
        "education",
        "skill",
        "certification",
    )

    _GROUP_LABELS: dict[str, str] = {
        "profile": "Career Profile",
        "experience": "Work Experience",
        "education": "Education",
        "skill": "Skills",
        "certification": "Certifications",
    }

    def build(self, query: str, chunks: Sequence[RetrievedChunk]) -> str:
        if not chunks:
            return "No relevant career information found."

        # Group by source_type, preserving stable order.
        groups: dict[str, list[RetrievedChunk]] = {k: [] for k in self._GROUP_ORDER}
        for c in chunks:
            groups.setdefault(c.source_type, []).append(c)

        lines: list[str] = [f"Career Context (query: {query})", ""]
        for group_key in self._GROUP_ORDER:
            group_chunks = groups.get(group_key) or []
            if not group_chunks:
                continue
            lines.append(f"[{self._GROUP_LABELS.get(group_key, group_key.title())}]")
            # Within a group, order by score descending then by id for stability.
            ordered = sorted(group_chunks, key=lambda c: (-c.score, c.id))
            for c in ordered:
                title = c.title or "(untitled)"
                lines.append(f"- {title}: {c.content}")
            lines.append("")

        return "\n".join(lines).strip()
