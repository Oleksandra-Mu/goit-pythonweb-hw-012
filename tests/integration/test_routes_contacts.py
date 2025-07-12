import json
import pytest
from fastapi.testclient import TestClient
from src.repository.auth import create_access_token
from main import app

contact_data = {
    "name": "Ransom Riggs",
    "email": "ransom@example.com",
    "phone_number": "+396369326598",
    "date_of_birth": "2005-07-15",
    "user_id": 10,
}


client = TestClient(app)


@pytest.mark.asyncio
async def test_create_contact(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}

    response = client.post("/api/contacts/", headers=headers, json=contact_data)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == contact_data["email"]
    assert "id" in data


@pytest.mark.asyncio
async def test_read_all_contacts(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    response = client.get("/api/contacts/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_remove_contact(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    response = client.delete("/api/contacts/10", headers=headers)
    assert response.status_code == 404


# @pytest.mark.asyncio
# async def test_get_upcoming_birthdays(client, get_token):
#     headers = {"Authorization": f"Bearer {get_token}"}
#     response = client.get("/api/contacts/birthdays", headers=headers)
#     assert response.status_code in [200, 404]
#     # assert response.json()["detail"] == "Not authenticated"
