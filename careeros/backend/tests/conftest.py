from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_password_hash
from app.core.rate_limiter import api_rate_limiter, auth_rate_limiter
from app.db.database import Base, get_db
from app.db.models.user import User
# Import all models to ensure they are registered with Base before table creation
from app.db import models  # noqa: F401
from app.main import create_app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db_session() -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    app = create_app()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Reset global rate limiter state before each test."""
    auth_rate_limiter.requests.clear()
    api_rate_limiter.requests.clear()
    yield


_SEED_SOURCES = [
    ("pk_fpsc", "FPSC", "government", "public_page", "PK"),
    ("pk_ppsc", "PPSC", "government", "public_page", "PK"),
    ("pk_rozee", "Rozee.pk", "private_board", "public_page", "PK"),
    ("pk_mustakbil", "Mustakbil", "private_board", "public_page", "PK"),
    ("pk_brightspyre", "BrightSpyre", "private_board", "public_page", "PK"),
    ("linkedin_pk", "LinkedIn PK", "private_board", "unsupported", "PK"),
    ("indeed_pk", "Indeed PK", "private_board", "unsupported", "PK"),
    ("remote_generic", "Remote", "remote", "unsupported", ""),
    ("company_template", "Company Page", "company_career", "public_page", "PK"),
]


@pytest.fixture(autouse=True)
def _seed_job_sources(db_session: Session):
    """Seed the default source registry for every test (mimics the
    migration seed for the in-memory test database)."""
    from app.db.models.jobs import JobSource
    for sid, name, cat, method, country in _SEED_SOURCES:
        if db_session.get(JobSource, sid) is None:
            db_session.add(JobSource(
                id=sid,
                name=name,
                category=cat,
                source_type=cat,
                integration_method=method,
                country=country or "PK",
                enabled=False,
                is_active=True,
            ))
    db_session.commit()
    yield


@pytest.fixture()
def test_user(db_session: Session) -> User:
    user = User(
        email="demo@example.com",
        full_name="Demo User",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_helpers():
    """Helper methods for registering users and obtaining tokens."""

    def register(client: TestClient, email: str, full_name: str = "Test User") -> dict:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "StrongPass123",
                "full_name": full_name,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    def login(client: TestClient, email: str) -> str:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "StrongPass123"},
        )
        assert response.status_code == 200, response.text
        return response.json()["access_token"]

    def token_headers(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def register_and_login(client: TestClient, email: str, full_name: str = "Test User") -> dict[str, str]:
        register(client, email, full_name)
        token = login(client, email)
        return token_headers(token)

    return SimpleNamespace(
        register=register,
        login=login,
        token_headers=token_headers,
        register_and_login=register_and_login,
    )


class SimpleNamespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
