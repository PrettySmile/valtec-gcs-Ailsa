"""
Starter tests for the command endpoint.
Candidates may extend these as part of their submission.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_send_command_valid_drone():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/drones/drone-1/command",
            json={"type": "land"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["drone_id"] == "drone-1"
    assert data["status"] in ("accepted", "rejected")


@pytest.mark.asyncio
async def test_send_command_unknown_drone():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/drones/drone-99/command",
            json={"type": "land"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_send_command_invalid_type():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/drones/drone-1/command",
            json={"type": "self_destruct"},
        )
    assert response.status_code == 422
