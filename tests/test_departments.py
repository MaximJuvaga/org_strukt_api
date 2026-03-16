import pytest

@pytest.mark.asyncio
async def test_create_department(client):
    response = await client.post("/api/v1/departments/", json={"name": "IT"})
    assert response.status_code == 201
    assert response.json()["name"] == "IT"

@pytest.mark.asyncio
async def test_duplicate_name(client):
    await client.post("/api/v1/departments/", json={"name": "HR"})
    response = await client.post("/api/v1/departments/", json={"name": "HR"})
    assert response.status_code == 400
