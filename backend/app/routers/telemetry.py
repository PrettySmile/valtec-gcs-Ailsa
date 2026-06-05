from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.dependencies import simulator
from app.models.drone import TelemetryFrame

router = APIRouter(tags=["telemetry"])


@router.websocket("/ws/telemetry")
async def telemetry_stream(websocket: WebSocket):
    await websocket.accept()

    async def push_frame(frame: TelemetryFrame):
        try:
            await websocket.send_text(frame.model_dump_json())
        except Exception:
            pass

    simulator.subscribe(push_frame)

    try:
        while True:
            # Keep the connection alive; client can send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        simulator.unsubscribe(push_frame)
