from pydantic import BaseModel
from typing import Literal, List, Optional
from datetime import datetime


class GPSCoordinate(BaseModel):
    lat: float
    lng: float
    alt: float  # metres above ground


class TelemetryFrame(BaseModel):
    drone_id: str
    timestamp: datetime
    battery: float  # 0.0 – 100.0 percent
    gps: GPSCoordinate
    speed: float  # m/s
    heading: float  # degrees 0–360
    status: Literal["online", "warning", "offline"]


class CommandRequest(BaseModel):
    type: Literal["land", "return_home", "hover", "emergency_land"]
    payload: dict = {}


class CommandResponse(BaseModel):
    command_id: str
    drone_id: str
    type: Literal["land", "return_home", "hover", "emergency_land"]
    status: Literal["accepted", "rejected", "error"]
    message: str = ""
    created_at: Optional[str] = None


class Command(BaseModel):
    command_id: str
    type: Literal["land", "return_home", "hover", "emergency_land"]
    status: Literal["pending", "executing", "completed", "cancelled", "failed"] = (
        "pending"
    )
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    def update_status(
        self,
        new_status: str,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
    ):
        """
        後端不變性防線：
        一旦狀態鎖定在終端狀態 (completed / cancelled / failed)，就不允許再變更。
        """
        TERMINAL_STATES = {"completed", "cancelled", "failed"}
        if self.status in TERMINAL_STATES:
            raise ValueError(
                f"Command {self.command_id} is already in terminal state '{self.status}' "
                f"and cannot transition to '{new_status}'."
            )
        self.status = new_status
        if started_at:
            self.started_at = started_at
        if completed_at:
            self.completed_at = completed_at


class QueueStateResponse(BaseModel):
    drone_id: str
    executing: Optional[Command] = None
    pending: List[Command] = []
