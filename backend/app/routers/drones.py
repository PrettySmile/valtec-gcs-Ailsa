from fastapi import APIRouter
from app.dependencies import simulator

router = APIRouter(prefix="/drones", tags=["drones"])


@router.get("/")
async def list_drones():
    return {"drone_ids": simulator.get_drone_ids()}
