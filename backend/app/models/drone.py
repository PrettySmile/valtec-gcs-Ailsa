from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class GPSCoordinate(BaseModel):
    lat: float
    lng: float
    alt: float  # metres above ground


class TelemetryFrame(BaseModel):
    drone_id: str
    timestamp: datetime
    battery: float        # 0.0 – 100.0 percent
    gps: GPSCoordinate
    speed: float          # m/s
    heading: float        # degrees 0–360
    status: Literal["online", "warning", "offline"]


class CommandRequest(BaseModel):
    type: Literal["land", "return_home", "hover", "emergency_land"]
    payload: dict = {}


class CommandResponse(BaseModel):
    command_id: str
    drone_id: str
    type: str
    status: Literal["accepted", "rejected", "error"]
    message: str = ""
