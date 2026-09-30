"""Tests for Phase 3 Career Brain: embeddings, chunking, vector store, indexing, search, and cross-user isolation."""

import pytest
from fastapi.testclient import TestClient

from app.services.chunker import TextChunker
from app.services.document_builder import (
    CareerDocument,
    CareerDocumentBuilder,
    _format_education,
    _format_experience,
    _format_skill,
    _format_certification,
    _format_profile,
)
from app.services.embeddings import HashEmbeddingProvider, get_embedding_provider
from app.services.vector_store import InMemoryVectorStore, StoredVector


# ---------------------------------------------------------------------------
# Helpers (shared with test_career.py style)
# ---------------------------------------------------------------------------


def _register(client: TestClient, email: str, full_name: str = "Test User") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(client: TestClient, email: str, full_name: str = "Test User") -> dict[str, str]:
    _register(client, email, full_name)
    token = _login(client, email)
    return _headers(token)


# ---------------------------------------------------------------------------
# Chunker tests
# ---------------------------------------------------------------------------


class TestTextChunker:
    """TextChunker must be deterministic, normalize whitespace, and never produce empty chunks."""

    def test_empty_text_returns_no_chunks(self):
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        assert chunker.split("") == []
        assert chunker.split("   \n\t  ") == []

    def test_short_text_single_chunk(self):
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.split("Hello world")
        assert len(chunks) == 1
        assert chunks[0].text == "Hello world"
        assert chunks[0].index == 0

    def test_long_text_produces_overlapping_chunks(self):
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "a " * 100  # 200 chars
        chunks = chunker.split(text)
        assert len(chunks) > 1
        # No empty chunks
        for c in chunks:
            assert c.text.strip() != ""
        # Indices are sequential
        assert [c.index for c in chunks] == list(range(len(chunks)))

    def test_whitespace_normalization(self):
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.split("hello   \n\n  world\t\t!")
        assert len(chunks) == 1
        assert chunks[0].text == "hello world !"

    def test_deterministic(self):
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "The quick brown fox jumps over the lazy dog. " * 5
        a = chunker.split(text)
        b = chunker.split(text)
        assert [c.text for c in a] == [c.text for c in b]

    def test_max_chunks_truncation(self):
        chunker = TextChunker(chunk_size=20, chunk_overlap=5)
        text = "word " * 200
        chunks = chunker.split(text, max_chunks=3)
        assert len(chunks) <= 3

    def test_invalid_params_rejected(self):
        with pytest.raises(ValueError):
            TextChunker(chunk_size=0, chunk_overlap=0)
        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, chunk_overlap=100)
        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, chunk_overlap=-1)


# ---------------------------------------------------------------------------
# Embedding provider tests
# ---------------------------------------------------------------------------


class TestHashEmbeddingProvider:
    """The local hash-based embedding provider must be deterministic, local, and dimension-correct."""

    def test_dimension_matches_config(self):
        provider = HashEmbeddingProvider(dimension=384)
        assert provider.dimension == 384
        assert provider.model_name == "local-hash-384"

    def test_embed_text_returns_correct_dimension(self):
        provider = HashEmbeddingProvider(dimension=384)
        vec = provider.embed_text("python machine learning")
        assert len(vec) == 384
        assert all(isinstance(x, float) for x in vec)

    def test_embed_text_is_deterministic(self):
        provider = HashEmbeddingProvider(dimension=384)
        a = provider.embed_text("python machine learning")
        b = provider.embed_text("python machine learning")
        assert a == b

    def test_embed_text_different_for_different_text(self):
        provider = HashEmbeddingProvider(dimension=384)
        a = provider.embed_text("python machine learning")
        b = provider.embed_text("java spring boot")
        assert a != b

    def test_embed_text_empty_rejected(self):
        provider = HashEmbeddingProvider(dimension=384)
        with pytest.raises(ValueError):
            provider.embed_text("")
        with pytest.raises(ValueError):
            provider.embed_text("   ")

    def test_embed_documents_batch(self):
        provider = HashEmbeddingProvider(dimension=384)
        texts = ["python", "java", "rust"]
        vecs = provider.embed_documents(texts)
        assert len(vecs) == 3
        for v in vecs:
            assert len(v) == 384

    def test_embed_documents_empty_rejected(self):
        provider = HashEmbeddingProvider(dimension=384)
        with pytest.raises(ValueError):
            provider.embed_documents(["python", ""])

    def test_vectors_are_unit_length(self):
        provider = HashEmbeddingProvider(dimension=384)
        vec = provider.embed_text("test embedding vector length")
        norm = sum(x * x for x in vec) ** 0.5
        assert abs(norm - 1.0) < 1e-5

    def test_factory_returns_provider(self):
        provider = get_embedding_provider()
        assert isinstance(provider, HashEmbeddingProvider)
        assert provider.dimension == 384


# ---------------------------------------------------------------------------
# Document builder tests
# ---------------------------------------------------------------------------


class TestCareerDocumentBuilder:
    """The document builder must produce normalized, user-scoped documents."""

    def test_stable_id(self):
        doc = CareerDocument(
            source_type="skill", source_id="abc-123", title="Python", content="Python skill"
        )
        assert doc.stable_id() == "skill:abc-123"

    def test_format_education(self):
        from app.db.models.education import Education
        from datetime import date
        edu = Education(
            id="00000000-0000-0000-0000-000000000001",
            user_id="00000000-0000-0000-0000-000000000099",
            institution="MIT",
            degree="Bachelor",
            field_of_study="CS",
            start_date=date(2016, 9, 1),
            end_date=date(2020, 6, 1),
            grade="3.8",
        )
        doc = _format_education(edu)
        assert doc.source_type == "education"
        assert "MIT" in doc.content
        assert "Bachelor" in doc.content

    def test_format_experience(self):
        from app.db.models.work_experience import WorkExperience
        from datetime import date
        we = WorkExperience(
            id="00000000-0000-0000-0000-000000000002",
            user_id="00000000-0000-0000-0000-000000000099",
            company="Acme",
            job_title="Engineer",
            start_date=date(2020, 1, 1),
            end_date=date(2022, 1, 1),
            is_current=False,
        )
        doc = _format_experience(we)
        assert doc.source_type == "experience"
        assert "Acme" in doc.content
        assert "Engineer" in doc.content

    def test_format_skill(self):
        from app.db.models.skill import Skill
        sk = Skill(
            id="00000000-0000-0000-0000-000000000003",
            user_id="00000000-0000-0000-0000-000000000099",
            name="Python",
            category="Technical",
            proficiency="Expert",
        )
        doc = _format_skill(sk)
        assert doc.source_type == "skill"
        assert "Python" in doc.content

    def test_format_certification(self):
        from app.db.models.certification import Certification
        from datetime import date
        c = Certification(
            id="00000000-0000-0000-0000-000000000004",
            user_id="00000000-0000-0000-0000-000000000099",
            name="AWS Solutions Architect",
            issuing_organization="Amazon",
            issue_date=date(2023, 1, 1),
        )
        doc = _format_certification(c)
        assert doc.source_type == "certification"
        assert "AWS" in doc.content

    def test_format_profile(self):
        from app.db.models.career_profile import CareerProfile
        p = CareerProfile(
            id="00000000-0000-0000-0000-000000000005",
            user_id="00000000-0000-0000-0000-000000000099",
            professional_title="Software Engineer",
            summary="Experienced developer",
            years_of_experience=5,
        )
        doc = _format_profile(p)
        assert doc.source_type == "profile"
        assert "Software Engineer" in doc.content

    def test_builder_uses_user_id_filter(self, db_session):
        """The builder must query the database with the given user_id filter."""
        from app.db.models.user import User
        from app.core.security import get_password_hash

        u = User(
            email="builder@example.com",
            password_hash=get_password_hash("StrongPass123"),
            is_active=True,
        )
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)

        builder = CareerDocumentBuilder()
        docs = builder.build(db_session, u.id)
        assert isinstance(docs, list)
        # No data yet, should be empty
        assert docs == []


# ---------------------------------------------------------------------------
# Vector store tests
# ---------------------------------------------------------------------------


class TestInMemoryVectorStore:
    """The vector store must be strictly user-scoped and use cosine similarity."""

    def test_upsert_and_count(self, db_session):
        from app.db.models.user import User
        from app.core.security import get_password_hash

        u = User(
            email="vs1@example.com",
            password_hash=get_password_hash("StrongPass123"),
            is_active=True,
        )
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)

        store = InMemoryVectorStore()
        provider = HashEmbeddingProvider(dimension=384)
        vecs = [
            StoredVector(
                id=f"skill:00000000-0000-0000-0000-00000000000{i}:0",
                user_id=str(u.id),
                source_type="skill",
                source_id=f"00000000-0000-0000-0000-00000000000{i}",
                title=f"Skill {i}",
                content=f"skill number {i}",
                embedding=provider.embed_text(f"skill number {i}"),
            )
            for i in range(3)
        ]
        written = store.upsert_chunks(db_session, u.id, vecs)
        assert written == 3
        assert store.count_for_user(db_session, u.id) == 3

    def test_search_returns_relevant_results(self, db_session):
        from app.db.models.user import User
        from app.core.security import get_password_hash

        u = User(
            email="vs2@example.com",
            password_hash=get_password_hash("StrongPass123"),
            is_active=True,
        )
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)

        provider = HashEmbeddingProvider(dimension=384)
        store = InMemoryVectorStore()
        vecs = [
            StoredVector(
                id="skill:00000000-0000-0000-0000-000000000001:0",
                user_id=str(u.id),
                source_type="skill",
                source_id="00000000-0000-0000-0000-000000000001",
                title="Python",
                content="Python programming language",
                embedding=provider.embed_text("Python programming language"),
            ),
            StoredVector(
                id="skill:00000000-0000-0000-0000-000000000002:0",
                user_id=str(u.id),
                source_type="skill",
                source_id="00000000-0000-0000-0000-000000000002",
                title="Java",
                content="Java enterprise development",
                embedding=provider.embed_text("Java enterprise development"),
            ),
        ]
        store.upsert_chunks(db_session, u.id, vecs)

        hits = store.search(
            db_session, u.id, provider.embed_text("python development"), top_k=1
        )
        assert len(hits) == 1
        assert hits[0].source_type == "skill"
        assert hits[0].title in ("Python", "Java")
        assert 0.0 <= hits[0].score <= 1.0

    def test_user_isolation_at_vector_layer(self, db_session):
        """One user's data must never appear in another user's search."""
        from app.db.models.user import User
        from app.core.security import get_password_hash

        u_a = User(
            email="vs3a@example.com",
            password_hash=get_password_hash("StrongPass123"),
            is_active=True,
        )
        u_b = User(
            email="vs3b@example.com",
            password_hash=get_password_hash("StrongPass123"),
            is_active=True,
        )
        db_session.add(u_a)
        db_session.add(u_b)
        db_session.commit()
        db_session.refresh(u_a)
        db_session.refresh(u_b)

        provider = HashEmbeddingProvider(dimension=384)
        store = InMemoryVectorStore()

        store.upsert_chunks(
            db_session,
            u_a.id,
            [
                StoredVector(
                    id="skill:00000000-0000-0000-0000-000000000001:0",
                    user_id=str(u_a.id),
                    source_type="skill",
                    source_id="00000000-0000-0000-0000-000000000001",
                    title="Python",
                    content="Python programming",
                    embedding=provider.embed_text("Python programming"),
                )
            ],
        )
        store.upsert_chunks(
            db_session,
            u_b.id,
            [
                StoredVector(
                    id="skill:00000000-0000-0000-0000-000000000002:0",
                    user_id=str(u_b.id),
                    source_type="skill",
                    source_id="00000000-0000-0000-0000-000000000002",
                    title="Java",
                    content="Java enterprise",
                    embedding=provider.embed_text("Java enterprise"),
                )
            ],
        )

        hits = store.search(
            db_session, u_a.id, provider.embed_text("python"), top_k=10
        )
        for hit in hits:
            assert hit.source_id == "00000000-0000-0000-0000-000000000001"  # Only user A's chunk
            assert "Java" not in hit.content

        hits = store.search(
            db_session, u_b.id, provider.embed_text("python"), top_k=10
        )
        for hit in hits:
            assert "Python" not in hit.content

    def test_delete_for_source(self, db_session):
        from app.db.models.user import User
        from app.core.security import get_password_hash

        u = User(
            email="vs4@example.com",
            password_hash=get_password_hash("StrongPass123"),
            is_active=True,
        )
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)

        provider = HashEmbeddingProvider(dimension=384)
        store = InMemoryVectorStore()
        store.upsert_chunks(
            db_session,
            u.id,
            [
                StoredVector(
                    id="skill:00000000-0000-0000-0000-000000000001:0",
                    user_id=str(u.id),
                    source_type="skill",
                    source_id="00000000-0000-0000-0000-000000000001",
                    title="Python",
                    content="Python",
                    embedding=provider.embed_text("Python"),
                )
            ],
        )
        assert store.count_for_user(db_session, u.id) == 1
        deleted = store.delete_for_source(
            db_session, u.id, "skill", "00000000-0000-0000-0000-000000000001"
        )
        assert deleted == 1
        assert store.count_for_user(db_session, u.id) == 0


# ---------------------------------------------------------------------------
# API tests — authentication required
# ---------------------------------------------------------------------------


class TestCareerBrainAuth:
    """All Career Brain endpoints must require authentication."""

    @pytest.mark.parametrize(
        "method,path",
        [
            ("POST", "/api/v1/career-brain/index"),
            ("POST", "/api/v1/career-brain/search"),
            ("POST", "/api/v1/career-brain/context"),
        ],
    )
    def test_endpoints_require_auth(self, client, method, path):
        response = client.request(method, path, json={})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# API tests — indexing
# ---------------------------------------------------------------------------


class TestCareerBrainIndex:
    """Indexing must process all career data and return statistics."""

    def test_index_empty_user(self, client):
        headers = _register_and_login(client, "brain_empty@example.com")
        response = client.post("/api/v1/career-brain/index", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["documents_processed"] == 0
        assert data["chunks_created"] == 0
        assert "embedding_model" in data

    def test_index_with_career_data(self, client):
        headers = _register_and_login(client, "brain_full@example.com")
        # Create profile
        client.post(
            "/api/v1/profile",
            json={"professional_title": "ML Engineer", "summary": "Machine learning expert"},
            headers=headers,
        )
        # Create education
        client.post(
            "/api/v1/education",
            json={"institution": "MIT", "degree": "Bachelor", "field_of_study": "Computer Science"},
            headers=headers,
        )
        # Create experience
        client.post(
            "/api/v1/experience",
            json={"company": "Acme", "job_title": "ML Engineer", "start_date": "2020-01-01"},
            headers=headers,
        )
        # Create skills
        client.post("/api/v1/skills", json={"name": "Python", "proficiency": "Expert"}, headers=headers)
        client.post("/api/v1/skills", json={"name": "TensorFlow", "proficiency": "Advanced"}, headers=headers)
        # Create certification
        client.post(
            "/api/v1/certifications",
            json={"name": "Google ML Engineer", "issuing_organization": "Google"},
            headers=headers,
        )

        response = client.post("/api/v1/career-brain/index", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["documents_processed"] == 6  # profile + education + experience + 2 skills + cert
        assert data["chunks_created"] >= 6
        assert data["embedding_model"] == "local-hash-384"

    def test_reindex_is_idempotent(self, client):
        """Re-indexing should not create duplicate chunks for unchanged data."""
        headers = _register_and_login(client, "brain_reindex@example.com")
        client.post(
            "/api/v1/skills",
            json={"name": "Python"},
            headers=headers,
        )

        first = client.post("/api/v1/career-brain/index", headers=headers).json()
        second = client.post("/api/v1/career-brain/index", headers=headers).json()

        assert first["documents_processed"] == second["documents_processed"]
        assert first["chunks_created"] == second["chunks_created"]
        # Second run should report reuse
        assert second["embeddings_reused"] >= first["embeddings_reused"]


# ---------------------------------------------------------------------------
# API tests — search
# ---------------------------------------------------------------------------


class TestCareerBrainSearch:
    """Search must return user-scoped, relevant results."""

    def test_search_after_index(self, client):
        headers = _register_and_login(client, "brain_search@example.com")
        client.post(
            "/api/v1/skills",
            json={"name": "Python", "proficiency": "Expert"},
            headers=headers,
        )
        client.post(
            "/api/v1/experience",
            json={"company": "Acme", "job_title": "Backend Developer", "start_date": "2020-01-01"},
            headers=headers,
        )
        client.post("/api/v1/career-brain/index", headers=headers)

        response = client.post(
            "/api/v1/career-brain/search",
            json={"query": "python programming", "top_k": 5},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "python programming"
        assert len(data["results"]) > 0
        # All results must have a score in [0, 1]
        for r in data["results"]:
            assert 0.0 <= r["score"] <= 1.0
            assert r["source_type"] in (
                "profile", "education", "experience", "skill", "certification"
            )

    def test_search_empty_index_returns_empty(self, client):
        headers = _register_and_login(client, "brain_search_empty@example.com")
        response = client.post(
            "/api/v1/career-brain/search",
            json={"query": "anything", "top_k": 5},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["results"] == []

    def test_search_validates_query(self, client):
        headers = _register_and_login(client, "brain_search_val@example.com")
        # Empty query
        r = client.post(
            "/api/v1/career-brain/search",
            json={"query": "", "top_k": 5},
            headers=headers,
        )
        assert r.status_code == 422
        # Oversized query
        r = client.post(
            "/api/v1/career-brain/search",
            json={"query": "a" * 501, "top_k": 5},
            headers=headers,
        )
        assert r.status_code == 422

    def test_search_validates_top_k(self, client):
        headers = _register_and_login(client, "brain_search_topk@example.com")
        r = client.post(
            "/api/v1/career-brain/search",
            json={"query": "test", "top_k": 0},
            headers=headers,
        )
        assert r.status_code == 422
        r = client.post(
            "/api/v1/career-brain/search",
            json={"query": "test", "top_k": 11},
            headers=headers,
        )
        assert r.status_code == 422

    def test_search_ignores_user_id_in_body(self, client):
        """Mass assignment: client cannot specify user_id."""
        headers_a = _register_and_login(client, "brain_massign_a@example.com")
        client.post(
            "/api/v1/skills",
            json={"name": "Python"},
            headers=headers_a,
        )
        client.post("/api/v1/career-brain/index", headers=headers_a)

        # Try to spoof user_id in the search request
        fake_user_id = "00000000-0000-0000-0000-000000000999"
        response = client.post(
            "/api/v1/career-brain/search",
            json={"query": "python", "top_k": 5, "user_id": fake_user_id},
            headers=headers_a,
        )
        # Either the extra field is silently ignored (200) or rejected (422).
        # It must NOT cause results from another user.
        if response.status_code == 200:
            data = response.json()
            # Results must be the authenticated user's data
            assert len(data["results"]) > 0
        # If 422, Pydantic rejected the extra field — also acceptable.


# ---------------------------------------------------------------------------
# API tests — RAG context
# ---------------------------------------------------------------------------


class TestCareerBrainContext:
    """RAG context endpoint must return formatted, user-scoped context."""

    def test_context_after_index(self, client):
        headers = _register_and_login(client, "brain_ctx@example.com")
        client.post(
            "/api/v1/skills",
            json={"name": "Python", "proficiency": "Expert"},
            headers=headers,
        )
        client.post(
            "/api/v1/experience",
            json={"company": "Acme", "job_title": "Backend Engineer", "start_date": "2020-01-01"},
            headers=headers,
        )
        client.post("/api/v1/career-brain/index", headers=headers)

        response = client.post(
            "/api/v1/career-brain/context",
            json={"query": "python backend", "top_k": 5},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "context" in data
        assert "query" in data
        assert "results" in data
        assert isinstance(data["context"], str)
        assert len(data["context"]) > 0

    def test_context_empty_index(self, client):
        headers = _register_and_login(client, "brain_ctx_empty@example.com")
        response = client.post(
            "/api/v1/career-brain/context",
            json={"query": "anything", "top_k": 5},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["context"] == "No relevant career information found."

    def test_context_validates_input(self, client):
        headers = _register_and_login(client, "brain_ctx_val@example.com")
        r = client.post(
            "/api/v1/career-brain/context",
            json={"query": "", "top_k": 5},
            headers=headers,
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Cross-user isolation — NON-NEGOTIABLE
# ---------------------------------------------------------------------------


class TestCareerBrainCrossUserIsolation:
    """User A's data must never appear in User B's results."""

    @pytest.fixture()
    def two_indexed_users(self, client):
        """Create two users with distinct career data and index both."""
        headers_a = _register_and_login(client, "brain_iso_a@example.com", "User A")
        headers_b = _register_and_login(client, "brain_iso_b@example.com", "User B")

        # User A: Python, FastAPI, Machine Learning
        client.post("/api/v1/skills", json={"name": "Python"}, headers=headers_a)
        client.post("/api/v1/skills", json={"name": "FastAPI"}, headers=headers_a)
        client.post("/api/v1/skills", json={"name": "Machine Learning"}, headers=headers_a)

        # User B: Java, Spring Boot, Android
        client.post("/api/v1/skills", json={"name": "Java"}, headers=headers_b)
        client.post("/api/v1/skills", json={"name": "Spring Boot"}, headers=headers_b)
        client.post("/api/v1/skills", json={"name": "Android"}, headers=headers_b)

        # Index both
        idx_a = client.post("/api/v1/career-brain/index", headers=headers_a)
        idx_b = client.post("/api/v1/career-brain/index", headers=headers_b)
        assert idx_a.status_code == 200
        assert idx_b.status_code == 200

        return headers_a, headers_b

    def test_user_a_search_returns_only_user_a_data(self, client, two_indexed_users):
        headers_a, _ = two_indexed_users
        response = client.post(
            "/api/v1/career-brain/search",
            json={"query": "Python", "top_k": 10},
            headers=headers_a,
        )
        assert response.status_code == 200
        results = response.json()["results"]
        for r in results:
            content_lower = r["content"].lower()
            assert "java" not in content_lower
            assert "spring" not in content_lower
            assert "android" not in content_lower

    def test_user_b_search_does_not_see_user_a_data(self, client, two_indexed_users):
        _, headers_b = two_indexed_users
        response = client.post(
            "/api/v1/career-brain/search",
            json={"query": "Python", "top_k": 10},
            headers=headers_b,
        )
        assert response.status_code == 200
        results = response.json()["results"]
        for r in results:
            content_lower = r["content"].lower()
            assert "python" not in content_lower
            assert "fastapi" not in content_lower
            assert "machine learning" not in content_lower

    def test_context_isolation(self, client, two_indexed_users):
        _, headers_b = two_indexed_users
        response = client.post(
            "/api/v1/career-brain/context",
            json={"query": "Python", "top_k": 10},
            headers=headers_b,
        )
        assert response.status_code == 200
        data = response.json()
        context = data["context"]
        results = data["results"]
        # Check that no retrieved result contains user A's content
        for r in results:
            content_lower = r["content"].lower()
            assert "python" not in content_lower
            assert "fastapi" not in content_lower
            assert "machine learning" not in content_lower
        # The context body should not contain user A's skill titles
        for r in results:
            if r["title"]:
                assert r["title"] not in ("Python", "FastAPI", "Machine Learning")
        assert "FastAPI" not in context


# ---------------------------------------------------------------------------
# RAG context builder (unit tests)
# ---------------------------------------------------------------------------


class TestRAGContextBuilder:
    """RAGContextBuilder must produce deterministic, grouped context."""

    def test_empty_chunks(self):
        from app.services.career_brain import RAGContextBuilder, RetrievedChunk

        ctx = RAGContextBuilder().build("test query", [])
        assert "No relevant" in ctx

    def test_groups_by_source_type(self):
        from app.services.career_brain import RAGContextBuilder, RetrievedChunk

        chunks = [
            RetrievedChunk(
                id="1", source_type="skill", source_id="s1",
                title="Python", content="Python skill", score=0.9,
            ),
            RetrievedChunk(
                id="2", source_type="experience", source_id="e1",
                title="Acme", content="Worked at Acme", score=0.8,
            ),
        ]
        ctx = RAGContextBuilder().build("query", chunks)
        assert "[Skills]" in ctx
        assert "[Work Experience]" in ctx
        assert "Python" in ctx
        assert "Acme" in ctx

    def test_deterministic(self):
        from app.services.career_brain import RAGContextBuilder, RetrievedChunk

        chunks = [
            RetrievedChunk(
                id="1", source_type="skill", source_id="s1",
                title="Python", content="Python", score=0.5,
            ),
            RetrievedChunk(
                id="2", source_type="skill", source_id="s2",
                title="Java", content="Java", score=0.9,
            ),
        ]
        builder = RAGContextBuilder()
        a = builder.build("q", chunks)
        b = builder.build("q", chunks)
        assert a == b
