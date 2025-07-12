from unittest.mock import Mock, AsyncMock, patch

import pytest
from tests.conftest import TestingSessionLocal, test_user
from sqlalchemy import select
from src.database.models import Users
from uuid import uuid4


def generate_user_data():
    return {
        "full_name": "agent007",
        "email": f"agent_{uuid4().hex}@example.com",
        "password": "12345678",
        "roles": "user",
    }


@pytest.mark.asyncio
async def test_signup(async_client, monkeypatch):
    user_data = generate_user_data()
    mock_send_email = AsyncMock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)

    resp = await async_client.post("/api/auth/signup", json=user_data)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["full_name"] == user_data["full_name"]
    assert data["email"] == user_data["email"]
    assert data["roles"] == user_data["roles"]


def test_duplicate_signup(client, monkeypatch):
    monkeypatch.setattr("src.services.email.send_email", Mock())
    res = client.post(
        "/api/auth/signup",
        json=test_user,
    )
    assert res.status_code == 409


def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "tester@example.com", "password": "12345678"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid(client):
    """Attempt login with wrong credentials and expect HTTP 401."""
    resp = client.post(
        "/api/auth/login",
        data={
            "username": "wrong@example.com",
            "password": "wrongpassword",
        },
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] in {
        "Invalid email",
        "Invalid password",
        "Email not confirmed",
        "Invalid authorization",
    }


def test_unconfirmed_login(client):
    res = client.post(
        "/api/auth/login",
        data={
            "username": "tester@example.com",
            "password": "1234568",
        },
    )
    assert res.status_code == 401
