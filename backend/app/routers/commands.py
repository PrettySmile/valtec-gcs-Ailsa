from fastapi import APIRouter
from app.models.drone import CommandRequest, CommandResponse
from app.services.command_service import CommandService

router = APIRouter(prefix="/drones", tags=["commands"])
command_service = CommandService()


# -----------------------------------------------------------------------
# BUG #2 — This endpoint has multiple error handling problems.
#
# Your task (see ASSIGNMENT.md Task 2):
#   Find all the issues and fix them. Do not change the URL or schema.
# -----------------------------------------------------------------------

@router.post("/{drone_id}/command", response_model=CommandResponse)
async def send_command(drone_id: str, command: CommandRequest):
    result = await command_service.execute(drone_id, command)
    return result
