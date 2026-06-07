import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch
from app.services.command_service import command_service
from app.models.drone import CommandRequest

# Capture real sleep to avoid infinite recursion
real_sleep = asyncio.sleep

async def mock_sleep_async(delay):
    # Sleep for 100ms in tests to simulate an active execution task
    await real_sleep(0.1)

@pytest.mark.asyncio
async def test_command_queue_workflow():
    # Reset command service state completely before test
    await command_service.reset_state()

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        # 1. Query initial queue state (should be empty)
        res = await client.get("/drones/drone-1/commands/pending")
        assert res.status_code == 200
        data = res.json()
        assert data["drone_id"] == "drone-1"
        assert data["executing"] is None
        assert data["pending"] == []

        # 2. Submit first command
        # We patch asyncio.sleep to run quickly during unit tests
        with patch("asyncio.sleep", mock_sleep_async):
            res = await client.post(
                "/drones/drone-1/command",
                json={"type": "land"},
            )
            assert res.status_code == 200
            cmd_data_1 = res.json()
            assert cmd_data_1["status"] == "accepted"
            assert "command_id" in cmd_data_1

            # Submit second command (should go to pending)
            res = await client.post(
                "/drones/drone-1/command",
                json={"type": "return_home"},
            )
            assert res.status_code == 200
            cmd_data_2 = res.json()
            assert cmd_data_2["status"] == "accepted"

            # Allow the event loop to run slightly (20ms) so background worker starts executing the first command.
            # Since the mock sleep takes 100ms, the first command will still be "executing"
            # and the second will be "pending".
            await real_sleep(0.02)

            # 3. Query queue state immediately (one should be executing, one pending)
            res = await client.get("/drones/drone-1/commands/pending")
            assert res.status_code == 200
            queue_data = res.json()
            assert queue_data["executing"] is not None
            assert queue_data["executing"]["command_id"] == cmd_data_1["command_id"]
            assert queue_data["executing"]["type"] == "land"

            assert len(queue_data["pending"]) == 1
            assert queue_data["pending"][0]["command_id"] == cmd_data_2["command_id"]
            assert queue_data["pending"][0]["type"] == "return_home"

    # Clean up
    await command_service.reset_state()


@pytest.mark.asyncio
async def test_command_queue_offline_drain():
    # Reset command service state completely before test
    await command_service.reset_state()

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        # Submit command
        with patch("asyncio.sleep", mock_sleep_async):
            await client.post("/drones/drone-1/command", json={"type": "land"})
            await client.post("/drones/drone-1/command", json={"type": "return_home"})

            # Allow event loop to run slightly (20ms) so background worker starts executing the first command,
            # while the second command is still pending.
            await real_sleep(0.02)

            # Verify it's not empty
            res = await client.get("/drones/drone-1/commands/pending")
            assert len(res.json()["pending"]) > 0

            # Trigger offline draining
            await command_service.drain_queue("drone-1")

            # Check queue is drained
            res = await client.get("/drones/drone-1/commands/pending")
            assert res.json()["executing"] is None
            assert res.json()["pending"] == []

    # Clean up
    await command_service.reset_state()
