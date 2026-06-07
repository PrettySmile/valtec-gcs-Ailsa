from fastapi import APIRouter, WebSocket
from app.services.connection_manager import connection_manager

router = APIRouter(tags=["telemetry"])


@router.websocket("/ws/telemetry")
async def telemetry_stream(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        await connection_manager.disconnect(websocket)
