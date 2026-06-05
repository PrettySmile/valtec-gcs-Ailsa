import uuid
from app.models.drone import CommandRequest, CommandResponse


class CommandService:

    async def execute(self, drone_id: str, command: CommandRequest) -> CommandResponse:
        command_id = str(uuid.uuid4())[:8]

        return CommandResponse(
            command_id=command_id,
            drone_id=drone_id,
            type=command.type,
            status="accepted",
            message=f"Command {command.type} dispatched to {drone_id}",
        )
