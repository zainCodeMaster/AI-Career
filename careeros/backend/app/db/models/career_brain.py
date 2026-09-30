"""Career Brain chunk model — persistent storage for embedded career document chunks.

Each row stores a single chunk of a normalized career document along with its
embedding vector. The embedding column uses the pgvector type for production
(PostgreSQL + pgvector) and degrades to a JSON-text column on SQLite for tests.
"""

from datetime import datetime, timezone
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class CareerBrainChunk(Base):
    """An embedded chunk of career data, scoped to a single user."""

    __tablename__ = "career_brain_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Ownership
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Source identity (which Phase 2 record this chunk came from)
    source_type = Column(String(50), nullable=False, index=True)  # profile|education|experience|skill|certification
    source_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Content
    title = Column(String(512), nullable=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False, default=0)

    # Embedding
    embedding_model = Column(String(128), nullable=False)
    embedding_dimension = Column(Integer, nullable=False)
    embedding = Column(Vector(384), nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<CareerBrainChunk(id={self.id}, user_id={self.user_id}, "
            f"source={self.source_type}, idx={self.chunk_index})>"
        )
