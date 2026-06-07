from fastapi import APIRouter, Depends
from app.models.drone import CommandRequest, CommandResponse, QueueStateResponse
from app.services.command_service import CommandService, command_service

router = APIRouter(prefix="/drones", tags=["commands"])


def get_command_service():
    return command_service


# -----------------------------------------------------------------------
# BUG #2 — This endpoint has multiple error handling problems.
#
# Your task (see ASSIGNMENT.md Task 2):
#   Find all the issues and fix them. Do not change the URL or schema.
# -----------------------------------------------------------------------


@router.post("/{drone_id}/command", response_model=CommandResponse)
async def send_command(
    drone_id: str,
    command: CommandRequest,
    service: CommandService = Depends(get_command_service),
):
    return await service.execute(drone_id, command)


@router.get("/{drone_id}/commands/pending", response_model=QueueStateResponse)
async def get_pending_commands(
    drone_id: str,
    service: CommandService = Depends(get_command_service),
):
    return await service.get_queue_state(drone_id)
