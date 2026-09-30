"""Pydantic schemas for Phase 3 Career Brain endpoints."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IndexResponse(BaseModel):
    """Response for POST /api/v1/career-brain/index."""

    documents_processed: int
    chunks_created: int
    embeddings_created: int
    embeddings_reused: int
    embedding_model: str


class SearchRequest(BaseModel):
    """Request for POST /api/v1/career-brain/search."""

    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def _strip_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query cannot be empty or whitespace")
        return v


class SearchResultItem(BaseModel):
    """A single search hit."""

    id: str
    source_type: str
    source_id: str
    title: Optional[str] = None
    content: str
    score: float


class SearchResponse(BaseModel):
    """Response for POST /api/v1/career-brain/search."""

    model_config = ConfigDict(from_attributes=True)

    query: str
    results: list[SearchResultItem]


class ContextRequest(BaseModel):
    """Request for POST /api/v1/career-brain/context."""

    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def _strip_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query cannot be empty or whitespace")
        return v


class ContextResponse(BaseModel):
    """Response for POST /api/v1/career-brain/context."""

    model_config = ConfigDict(from_attributes=True)

    query: str
    results: list[SearchResultItem]
    context: str
