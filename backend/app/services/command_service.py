import uuid
from app.exceptions.drone import DroneNotFoundError, DroneOfflineError
from app.dependencies import simulator
from app.models.drone import CommandRequest, CommandResponse


class CommandService:

    async def execute(self, drone_id: str, command: CommandRequest) -> CommandResponse:
        drone_status = simulator.get_drone_status(drone_id)
        if drone_status is None:
            raise DroneNotFoundError(f"drone_id={drone_id}")

        if drone_status != "online":
            raise DroneOfflineError(f"drone_id={drone_id}")
        
        command_id = str(uuid.uuid4())[:8]

        return CommandResponse(
            command_id=command_id,
            drone_id=drone_id,
            type=command.type,
            status="accepted",
            message=f"Command {command.type} dispatched to {drone_id}",
        )
