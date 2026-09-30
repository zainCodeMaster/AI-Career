from __future__ import annotations

from app.core.security import create_access_token
from app.db.models.user import User


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_user_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "password": "StrongPass123",
            "full_name": "Alice Example",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == "alice@example.com"
    assert payload["full_name"] == "Alice Example"
    assert "password" not in payload
    assert "password_hash" not in payload


def test_duplicate_email_rejected(client):
    payload = {
        "email": "charlie@example.com",
        "password": "StrongPass123",
        "full_name": "Charlie User",
    }
    first = client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == "Email already registered"


def test_password_is_hashed(db_session):
    user = User(
        email="hashed@example.com",
        full_name="Hashed User",
        password_hash="$2b$12$examplehashvalue1234567890abcdefghijkl",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.password_hash != "StrongPass123"
    assert user.password_hash.startswith("$")


def test_login_success(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@example.com",
            "password": "StrongPass123",
            "full_name": "Bob Example",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "bob@example.com",
            "password": "StrongPass123",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


def test_login_rejects_incorrect_password(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "dave@example.com",
            "password": "StrongPass123",
            "full_name": "Dave Example",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "dave@example.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_me_with_valid_token(client):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "erin@example.com",
            "password": "StrongPass123",
            "full_name": "Erin Example",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        json={
            "email": "erin@example.com",
            "password": "StrongPass123",
        },
    ).json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert register.status_code == 201
    assert response.status_code == 200
    assert response.json()["email"] == "erin@example.com"
    assert "password_hash" not in response.text


def test_me_without_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_me_with_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"


def test_user_isolation_basics(client):
    user_a = client.post(
        "/api/v1/auth/register",
        json={
            "email": "usera@example.com",
            "password": "StrongPass123",
            "full_name": "User A",
        },
    )
    user_b = client.post(
        "/api/v1/auth/register",
        json={
            "email": "userb@example.com",
            "password": "StrongPass123",
            "full_name": "User B",
        },
    )

    token_a = client.post(
        "/api/v1/auth/login",
        json={
            "email": "usera@example.com",
            "password": "StrongPass123",
        },
    ).json()["access_token"]

    assert user_a.status_code == 201
    assert user_b.status_code == 201

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "usera@example.com"
    assert response.json()["full_name"] == "User A"


def test_auth_token_has_user_identity(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "tokenuser@example.com",
            "password": "StrongPass123",
            "full_name": "Token User",
        },
    )
    user_id = register_response.json()["id"]
    token = create_access_token({"sub": str(user_id)})

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "tokenuser@example.com"


def test_logout_revokes_existing_access_token(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "logout@example.com",
            "password": "StrongPass123",
            "full_name": "Logout User",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": "StrongPass123"},
    ).json()["access_token"]
    headers = {"Authorization": "Bearer " + token}

    logout = client.post("/api/v1/auth/logout", headers=headers)

    assert logout.status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_logout_does_not_revoke_future_login_tokens(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "relogin@example.com",
            "password": "StrongPass123",
            "full_name": "Relogin User",
        },
    )
    first_token = client.post(
        "/api/v1/auth/login",
        json={"email": "relogin@example.com", "password": "StrongPass123"},
    ).json()["access_token"]
    client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer " + first_token},
    )
    second_token = client.post(
        "/api/v1/auth/login",
        json={"email": "relogin@example.com", "password": "StrongPass123"},
    ).json()["access_token"]

    assert client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer " + first_token}
    ).status_code == 401
    assert client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer " + second_token}
    ).status_code == 200


def test_login_returns_refresh_token(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh_example@example.com",
            "password": "StrongPass123",
            "full_name": "Refresh User",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh_example@example.com", "password": "StrongPass123"},
    )

    assert response.status_code == 200
    assert response.json()["refresh_token"]
    assert response.json()["token_type"] == "bearer"


def test_refresh_endpoint_rotates_tokens(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "rotate@example.com",
            "password": "StrongPass123",
            "full_name": "Rotate User",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "rotate@example.com", "password": "StrongPass123"},
    )
    refresh_token = login.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["refresh_token"]
    assert payload["refresh_token"] != refresh_token


def test_readiness_endpoint(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
