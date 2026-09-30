import uuid
from fastapi.testclient import TestClient

from app.main import create_app


def test_request_id_middleware_adds_header():
    """Test that the request ID middleware adds a unique X-Request-ID header."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    request_id = response.headers["x-request-id"]
    # Validate that it is a UUID
    uuid.UUID(request_id)


def test_request_id_middleware_preserves_provided_header():
    """Test that if a client provides an X-Request-ID header, it is preserved."""
    app = create_app()
    client = TestClient(app)
    custom_request_id = "custom-request-id-123"

    response = client.get(
        "/health", headers={"X-Request-ID": custom_request_id}
    )
    assert response.status_code == 200
    assert response.headers["x-request-id"] == custom_request_id


def test_request_id_middleware_generates_different_ids():
    """Test that different requests get different request IDs."""
    app = create_app()
    client = TestClient(app)

    response1 = client.get("/health")
    response2 = client.get("/health")
    assert response1.headers["x-request-id"] != response2.headers["x-request-id"]
    # Both should be valid UUIDs
    uuid.UUID(response1.headers["x-request-id"])
    uuid.UUID(response2.headers["x-request-id"])