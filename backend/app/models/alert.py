from pydantic import BaseModel


class Alert(BaseModel):
    id: str  # Format: "{drone_id}-{type}"
    drone_id: str
    type: str  # "low_battery" | "offline"
    message: str
    created_at: str  # ISO timestamp
