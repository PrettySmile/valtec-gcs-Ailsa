import asyncio
from datetime import datetime, timezone
import random
import uuid
from typing import Dict, List, Optional
import logging

from app.exceptions.drone import DroneNotFoundError, DroneOfflineError
from app.dependencies import simulator
from app.models.drone import CommandRequest, CommandResponse, QueuedCommand, QueueStateResponse

logger = logging.getLogger(__name__)


class CommandService:
    def __init__(self):
        # Structure per drone:
        # self._queues[drone_id] = {
        #     "executing": QueuedCommand | None,
        #     "pending": List[QueuedCommand],
        #     "task": asyncio.Task | None
        # }
        self._queues: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def _get_or_create_queue(self, drone_id: str) -> dict:
        async with self._lock:
            if drone_id not in self._queues:
                self._queues[drone_id] = {
                    "executing": None,
                    "pending": [],
                    "task": None
                }
            return self._queues[drone_id]

    async def get_queue_state(self, drone_id: str) -> QueueStateResponse:
        # Validate drone existence first
        drone_status = simulator.get_drone_status(drone_id)
        if drone_status is None:
            raise DroneNotFoundError(f"drone_id={drone_id}")

        queue = await self._get_or_create_queue(drone_id)
        async with self._lock:
            return QueueStateResponse(
                drone_id=drone_id,
                executing=queue["executing"],
                pending=list(queue["pending"])
            )

    async def execute(self, drone_id: str, command: CommandRequest) -> CommandResponse:
        drone_status = simulator.get_drone_status(drone_id)
        if drone_status is None:
            raise DroneNotFoundError(f"drone_id={drone_id}")

        if drone_status != "online" and drone_status != "warning":
            raise DroneOfflineError(f"drone_id={drone_id}")

        command_id = str(uuid.uuid4())[:8]
        queued_cmd = QueuedCommand(
            command_id=command_id,
            type=command.type,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        queue = await self._get_or_create_queue(drone_id)
        async with self._lock:
            queue["pending"].append(queued_cmd)
            # If background worker task is idle, start it
            if queue["task"] is None or queue["task"].done():
                queue["task"] = asyncio.create_task(self._run_next_command(drone_id))

        return CommandResponse(
            command_id=command_id,
            drone_id=drone_id,
            type=command.type,
            status="accepted",
            message=f"Command {command.type} dispatched to {drone_id}",
        )

    async def _run_next_command(self, drone_id: str):
        try:
            while True:
                queue = await self._get_or_create_queue(drone_id)
                current_cmd = None

                async with self._lock:
                    if not queue["pending"]:
                        queue["executing"] = None
                        queue["task"] = None
                        break

                    # Move first item from pending to executing
                    current_cmd = queue["pending"].pop(0)
                    queue["executing"] = current_cmd

                # Broadcast command_executing to all WebSockets
                await self._broadcast_status("command_executing", current_cmd, drone_id)

                # Simulate execution (2-4 seconds)
                duration = random.uniform(2, 4)
                await asyncio.sleep(duration)

                # Clear executing status under lock before broadcast to eliminate race with drain_queue
                async with self._lock:
                    queue["executing"] = None

                # Broadcast command_completed to all WebSockets
                await self._broadcast_status("command_completed", current_cmd, drone_id)

        except asyncio.CancelledError:
            # Task was cancelled because drone went offline.
            # Draining is handled by drain_queue.
            pass
        except Exception as e:
            logger.exception(f"Unexpected error in background command runner for {drone_id}: {e}")
        finally:
            # Self-healing safety gate: Ensure task states are cleared if we exit unexpectedly
            queue = await self._get_or_create_queue(drone_id)
            async with self._lock:
                if queue["task"] == asyncio.current_task():
                    queue["executing"] = None
                    queue["task"] = None

    async def reset_state(self):
        async with self._lock:
            # We do not use self._lock during task cancels because we want to clear states safely
            for drone_id, queue in list(self._queues.items()):
                if queue["task"] is not None and not queue["task"].done():
                    try:
                        queue["task"].cancel()
                    except Exception:
                        pass
            self._queues.clear()

    async def drain_queue(self, drone_id: str):
        queue = await self._get_or_create_queue(drone_id)
        
        executing_cmd = None
        pending_cmds = []

        async with self._lock:
            executing_cmd = queue["executing"]
            pending_cmds = list(queue["pending"])

            queue["pending"].clear()
            queue["executing"] = None

            # Cancel active sleep task
            if queue["task"] is not None and not queue["task"].done():
                queue["task"].cancel()
                queue["task"] = None

        # Broadcast cancellations
        if executing_cmd:
            await self._broadcast_status("command_cancelled", executing_cmd, drone_id)

        for cmd in pending_cmds:
            await self._broadcast_status("command_cancelled", cmd, drone_id)

    async def process_frame(self, frame):
        if frame.status == "offline":
            await self.drain_queue(frame.drone_id)

    async def _broadcast_status(self, cmd_name: str, cmd_info: QueuedCommand, drone_id: str):
        try:
            from app.services.connection_manager import connection_manager
            payload = {
                "cmd": cmd_name,
                "data": {
                    "command_id": cmd_info.command_id,
                    "drone_id": drone_id,
                    "type": cmd_info.type,
                    "created_at": cmd_info.created_at
                }
            }
            await connection_manager.broadcast(payload)
        except Exception as e:
            logger.error(f"Failed to broadcast command status {cmd_name} for {drone_id}: {e}")


# Singleton instance
command_service = CommandService()
