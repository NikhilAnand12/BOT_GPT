"""Unit tests for BOT GPT API."""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models import init_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Initialize test database."""
    init_db()
    yield


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "BOT GPT API" in response.json()["message"]


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_user():
    """Test user creation."""
    response = client.post(
        "/api/v1/users",
        json={
            "username": "test_user",
            "email": "test@example.com"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "test_user"
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_create_duplicate_user():
    """Test duplicate user creation fails."""
    # First user
    client.post(
        "/api/v1/users",
        json={
            "username": "duplicate_user",
            "email": "duplicate@example.com"
        }
    )

    # Try to create duplicate
    response = client.post(
        "/api/v1/users",
        json={
            "username": "duplicate_user",
            "email": "duplicate@example.com"
        }
    )
    assert response.status_code == 400


def test_create_and_get_conversation():
    """Test conversation creation and retrieval."""
    # Create user first
    user_response = client.post(
        "/api/v1/users",
        json={
            "username": "conv_test_user",
            "email": "convtest@example.com"
        }
    )
    user_id = user_response.json()["id"]

    # Create conversation
    conv_response = client.post(
        "/api/v1/conversations",
        json={
            "user_id": user_id,
            "title": "Test Conversation",
            "mode": "open_chat"
        }
    )
    assert conv_response.status_code == 201
    conv_data = conv_response.json()
    assert conv_data["title"] == "Test Conversation"
    assert conv_data["mode"] == "open_chat"

    # Get conversation
    conv_id = conv_data["id"]
    get_response = client.get(f"/api/v1/conversations/{conv_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == conv_id


def test_list_conversations():
    """Test listing conversations."""
    # Create user
    user_response = client.post(
        "/api/v1/users",
        json={
            "username": "list_test_user",
            "email": "listtest@example.com"
        }
    )
    user_id = user_response.json()["id"]

    # Create multiple conversations
    for i in range(3):
        client.post(
            "/api/v1/conversations",
            json={
                "user_id": user_id,
                "title": f"Test Conv {i}",
                "mode": "open_chat"
            }
        )

    # List conversations
    list_response = client.get(f"/api/v1/conversations?user_id={user_id}")
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] >= 3
    assert len(data["conversations"]) >= 3


def test_delete_conversation():
    """Test conversation deletion."""
    # Create user and conversation
    user_response = client.post(
        "/api/v1/users",
        json={
            "username": "delete_test_user",
            "email": "deletetest@example.com"
        }
    )
    user_id = user_response.json()["id"]

    conv_response = client.post(
        "/api/v1/conversations",
        json={
            "user_id": user_id,
            "title": "To Delete",
            "mode": "open_chat"
        }
    )
    conv_id = conv_response.json()["id"]

    # Delete conversation
    delete_response = client.delete(f"/api/v1/conversations/{conv_id}")
    assert delete_response.status_code == 200

    # Verify deletion
    get_response = client.get(f"/api/v1/conversations/{conv_id}")
    assert get_response.status_code == 404
