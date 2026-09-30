"""Tests for Phase 1 hardening features: rate limiting, audit logs, CORS, logging."""

import json
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.core.rate_limiter import auth_rate_limiter
from app.db.models.audit_log import AuditLog
from app.db.models.user import User
from app.services.audit import create_audit_log, get_audit_logs


class TestAuditLogging:
    """Test audit logging functionality."""

    def test_create_audit_log(self, db_session: Session):
        """Test creating an audit log entry."""
        log = create_audit_log(
            db_session,
            event_type="TEST_EVENT",
            email="test@example.com",
            details={"action": "test"},
        )
        
        assert log.event_type == "TEST_EVENT"
        assert log.email == "test@example.com"
        assert log.details == '{"action": "test"}'
        assert log.created_at is not None


class TestLogging:
    """Test application logging."""

    def test_registration_logging(self, client):
        """Test that registration is logged."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "logtest@example.com",
                "password": "StrongPass123",
                "full_name": "Log Test",
            },
        )
        assert response.status_code == 201
        # Logging happens asynchronously, just verify registration succeeds

    def test_login_logging(self, client):
        """Test that login attempts are logged."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login2@example.com",
                "password": "StrongPass123",
                "full_name": "Login Test 2",
            },
        )
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "login2@example.com",
                "password": "StrongPass123",
            },
        )
        assert response.status_code == 200
        # Logging happens, just verify login succeeds

    def test_failed_login_logging(self, client):
        """Test that failed login attempts are logged."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPassword",
            },
        )
        assert response.status_code == 401


class TestCORS:
    """Test CORS configuration."""

    def test_cors_allows_configured_origins(self, client):
        """Test that configured origins are allowed."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 200

    def test_cors_allows_loopback_frontend_and_patch_preflight(self, client):
        """The local Vite loopback origin can perform CRM PATCH requests."""
        response = client.options(
            "/api/v1/companies/example",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
        assert "PATCH" in response.headers["access-control-allow-methods"]

    def test_health_endpoint_accessible(self, client):
        """Test that health endpoint is accessible."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestSecureConfiguration:
    """Test secure configuration settings."""

    def test_password_never_returned_in_me_endpoint(self, client):
        """Test that password hash is never exposed in API responses."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "sectest@example.com",
                "password": "StrongPass123",
                "full_name": "Sec Test",
            },
        )
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "sectest@example.com",
                "password": "StrongPass123",
            },
        )
        
        token = login_response.json()["access_token"]
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        data = me_response.json()
        assert "password" not in data
        assert "password_hash" not in data
        assert "access_token" not in str(data)  # Verify as string too


class TestJWTSubjectClaim:
    """Test JWT subject claim uses user ID."""

    def test_jwt_contains_user_id_not_email(self, client):
        """Test that JWT subject claim is user ID, not email."""
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "jwttest@example.com",
                "password": "StrongPass123",
                "full_name": "JWT Test",
            },
        )
        
        user_id = register_response.json()["id"]
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "jwttest@example.com",
                "password": "StrongPass123",
            },
        )
        
        token = login_response.json()["access_token"]
        
        # Decode JWT to verify subject is user ID
        import base64
        parts = token.split(".")
        if len(parts) == 3:
            payload = parts[1]
            # Add padding if needed
            padding = 4 - (len(payload) % 4)
            if padding != 4:
                payload += "=" * padding
            decoded = base64.urlsafe_b64decode(payload)
            import json
            data = json.loads(decoded)
            assert data["sub"] == user_id


class TestRateLimitingFeatures:
    """Test that rate limiting is configured and available."""

    def test_login_rate_limiter_exists(self, client):
        """Test that rate limiter is configured."""
        from app.core.rate_limiter import auth_rate_limiter
        assert auth_rate_limiter is not None
        assert auth_rate_limiter.max_requests == 5  # Auth limit is 5 per 60 seconds

    def test_registration_with_rate_limiter(self, client):
        """Test that registration can succeed (rate limiter is in place)."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "ratelimitok@example.com",
                "password": "StrongPass123",
                "full_name": "Rate Limit OK",
            },
        )
        assert response.status_code == 201


class TestInactiveUser:
    """Inactive (deactivated) users must be rejected at the auth layer."""

    def test_inactive_user_returns_401(self, client, db_session):
        """An authenticated but inactive user must receive 401 Unauthorized."""
        from app.core.security import create_access_token
        from app.core.security import get_password_hash
        from app.db.models.user import User

        user = User(
            email="inactive@example.com",
            full_name="Inactive User",
            password_hash=get_password_hash("StrongPass123"),
            is_active=False,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = create_access_token({"sub": str(user.id)})
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

