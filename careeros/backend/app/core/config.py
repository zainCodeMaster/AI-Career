from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "CareerOS API"
    debug: bool = False
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    database_url: str = "sqlite:///./careeros.db"
    database_echo_sql: bool = False
    secret_key: str = Field(description="JWT secret key — must be set explicitly for production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    frontend_url: str = "http://localhost:5173"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    # Phase 3 — Career Brain (Embeddings + RAG)
    embedding_provider: str = "local"
    embedding_model: str = "local-hash-384"
    embedding_dimension: int = 384
    vector_store_backend: str = "pgvector"  # pgvector | in_memory (tests)
    career_brain_chunk_size: int = 500
    career_brain_chunk_overlap: int = 50
    career_brain_max_chunks_per_doc: int = 8

    # Phase 4 — Job Discovery
    job_discovery_enabled: bool = True
    job_discovery_max_results_per_source: int = 200
    job_discovery_timeout_seconds: float = 20.0
    job_discovery_retry_count: int = 2
    job_discovery_stale_days: int = 60
    job_discovery_user_agent: str = "CareerOS-Bot/1.0 (+https://careeros.local/bot)"

    # Phase 4.x — Automatic Discovery Scheduler
    job_discovery_scheduler_enabled: bool = True
    job_discovery_interval_minutes: int = 60
    job_discovery_scheduler_max_lookahead_jobs: int = 500

    # Phase 5 — Job Matching
    # Score weights (sum should be 1.0; weights are configurable so operators
    # can tune the ranking emphasis). Defaults reflect a skill-first ranking:
    # skills carry the strongest signal, followed by experience, education,
    # location, preferences, semantic similarity, and role/title overlap.
    match_weight_skills: float = 0.30
    match_weight_experience: float = 0.15
    match_weight_education: float = 0.10
    match_weight_location: float = 0.15
    match_weight_preferences: float = 0.15
    match_weight_semantic: float = 0.10
    match_weight_role_title: float = 0.05
    match_candidate_pool_size: int = 200  # max jobs to score per feed request

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate SECRET_KEY is not the insecure default in production mode."""
        debug = info.data.get("debug", False)
        database_url = info.data.get("database_url", "").lower()
        
        # Check if this is clearly a production environment
        is_production = not debug and (
            "postgresql" in database_url or 
            "postgres" in database_url or
            "supabase" in database_url
        )
        
        # In production (non-debug + PostgreSQL), require strong secrets
        if is_production:
            known_defaults = {
                "change-me-in-production",
                "dev-secret-key-for-local-development-only-change-in-production-12345",
                "your-secret-key-change-in-production",
            }
            if v in known_defaults:
                raise ValueError(
                    "SECRET_KEY must be changed from default for production environments. "
                    "Set a strong, unique SECRET_KEY environment variable."
                )
            if len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters for production")
        
        # For development/test environments, minimum 16 characters recommended
        if len(v) < 16:
            raise ValueError("SECRET_KEY should be at least 16 characters")
        
        return v

    @field_validator("database_echo_sql")
    @classmethod
    def validate_database_echo_sql(cls, v: bool, info) -> bool:
        """Prevent SQL query logging in production."""
        debug = info.data.get("debug", False)
        if v and not debug:
            raise ValueError("database_echo_sql cannot be True in production")
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str, info) -> str:
        """Validate database configuration is appropriate for environment."""
        debug = info.data.get("debug", False)
        
        # Only enforce PostgreSQL in production (non-debug without SQLite)
        if not debug and v.startswith("sqlite"):
            raise ValueError(
                "SQLite is not permitted in production. "
                "Use PostgreSQL via DATABASE_URL (e.g., postgresql://user:pass@host/db)"
            )
        
        if not v.startswith(("sqlite", "postgresql", "postgres")):
            raise ValueError(
                "Unsupported database backend. Use SQLite (sqlite://) or PostgreSQL (postgresql://)"
            )
        
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
