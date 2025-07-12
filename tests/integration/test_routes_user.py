import pytest
from tests.conftest import test_user


def test_get_me(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    resp = client.get("/api/users/me", headers=headers)

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["full_name"] == test_user["full_name"]
    assert data["email"] == test_user["email"]
    assert "avatar" in data
