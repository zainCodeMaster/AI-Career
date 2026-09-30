"""Career Brain API routes.

- POST /api/v1/career-brain/index   — rebuild the authenticated user's index
- POST /api/v1/career-brain/search  — user-scoped semantic search
- POST /api/v1/career-brain/context — RAG-ready context for future LLM
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.db.models.user import User
from app.schemas.career_brain import (
    ContextRequest,
    ContextResponse,
    IndexResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from app.services.audit import create_audit_log
from app.services.career_brain import (
    CareerBrainIndexer,
    CareerBrainRetriever,
    RAGContextBuilder,
)

router = APIRouter(prefix="/career-brain", tags=["career-brain"])


@router.post("/index", response_model=IndexResponse, status_code=status.HTTP_200_OK)
def index_career_brain(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> IndexResponse:
    """Rebuild the semantic index for the authenticated user."""
    indexer = CareerBrainIndexer()
    result = indexer.index_user(db, current_user.id)

    create_audit_log(
        db,
        event_type="CAREER_BRAIN_INDEXED",
        user_id=current_user.id,
        details={
            "documents_processed": result.documents_processed,
            "chunks_created": result.chunks_created,
            "embeddings_created": result.embeddings_created,
            "embeddings_reused": result.embeddings_reused,
            "embedding_model": indexer.embedding_model,
        },
    )
    return IndexResponse(
        documents_processed=result.documents_processed,
        chunks_created=result.chunks_created,
        embeddings_created=result.embeddings_created,
        embeddings_reused=result.embeddings_reused,
        embedding_model=indexer.embedding_model,
    )


@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
def search_career_brain(
    payload: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """User-scoped semantic search over the authenticated user's career data."""
    retriever = CareerBrainRetriever()
    chunks = retriever.search(db, current_user.id, payload.query, payload.top_k)

    # Log only non-sensitive aggregate metadata — not the full query or content.
    create_audit_log(
        db,
        event_type="CAREER_BRAIN_SEARCHED",
        user_id=current_user.id,
        details={
            "query_length": len(payload.query),
            "top_k": payload.top_k,
            "results_returned": len(chunks),
        },
    )

    return SearchResponse(
        query=payload.query,
        results=[
            SearchResultItem(
                id=c.id,
                source_type=c.source_type,
                source_id=c.source_id,
                title=c.title,
                content=c.content,
                score=c.score,
            )
            for c in chunks
        ],
    )


@router.post("/context", response_model=ContextResponse, status_code=status.HTTP_200_OK)
def build_career_brain_context(
    payload: ContextRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ContextResponse:
    """Return a formatted RAG-ready context string for the user's query."""
    retriever = CareerBrainRetriever()
    chunks = retriever.search(db, current_user.id, payload.query, payload.top_k)

    context = RAGContextBuilder().build(payload.query, chunks)

    create_audit_log(
        db,
        event_type="CAREER_BRAIN_CONTEXT_BUILT",
        user_id=current_user.id,
        details={
            "query_length": len(payload.query),
            "top_k": payload.top_k,
            "chunks_used": len(chunks),
        },
    )

    return ContextResponse(
        query=payload.query,
        results=[
            SearchResultItem(
                id=c.id,
                source_type=c.source_type,
                source_id=c.source_id,
                title=c.title,
                content=c.content,
                score=c.score,
            )
            for c in chunks
        ],
        context=context,
    )
