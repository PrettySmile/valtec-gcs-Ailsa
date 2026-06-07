"""
Starter tests for the command endpoint.
Candidates may extend these as part of their submission.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch
from app.constants.error_codes import ErrorCode


@pytest.mark.asyncio
async def test_send_command_valid_drone():
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
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
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/drones/drone-99/command",
            json={"type": "land"},
        )
    assert response.status_code == 404

    data = response.json()

    assert data["code"] == ErrorCode.DRONE_NOT_FOUND.value


@pytest.mark.asyncio
async def test_send_command_invalid_type():
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/drones/drone-1/command",
            json={"type": "self_destruct"},
        )
    assert response.status_code == 422

    data = response.json()
    print(data)

    assert data["code"] == ErrorCode.VALIDATION_ERROR.value


@pytest.mark.asyncio
async def test_send_command_offline_drone():
    with patch(
        "app.dependencies.simulator.get_drone_status", 
        return_value="offline"
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:

            response = await client.post(
                "/drones/drone-1/command",
                json={"type": "land"},
            )

    assert response.status_code == 409

    data = response.json()

    assert data["code"] == ErrorCode.DRONE_OFFLINE.value


@pytest.mark.asyncio
async def test_send_command_unexpected_exception():
    with patch(
        "app.services.command_service.CommandService.execute",
        side_effect=Exception("Database exploded"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:

            response = await client.post(
                "/drones/drone-1/command",
                json={"type": "land"},
            )

    assert response.status_code == 500

    data = response.json()

    assert data["code"] == ErrorCode.INTERNAL_SERVER_ERROR.value
    assert data["message"] == "Unexpected error occurred"
