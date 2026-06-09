import json
import logging
from datetime import datetime
from fastapi import WebSocket
from app.dependencies import simulator
from app.models.drone import TelemetryFrame
from app.services.alert_service import alert_service

logger = logging.getLogger("app.alert_service")


class ConnectionManager:
    def __init__(self):
        self.subscriptions: dict[WebSocket, callable] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

        active_ids = [alert.id for alert in alert_service.get_active_alerts()]
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(
            f"[ALERT LOG] {timestamp_str} | Broadcast: [Connection Sync] Active Alerts: {active_ids}"
        )

        try:
            payload = {
                "cmd": "alerts",
                "data": [
                    alert.model_dump(mode="json")
                    for alert in alert_service.get_active_alerts()
                ],
            }
            await websocket.send_text(json.dumps(payload))
        except Exception:
            # 直接 return，避免將已失效的連線註冊到模擬器中
            return

        async def push_frame(frame: TelemetryFrame):
            try:
                payload = {"cmd": "telemetry", "data": frame.model_dump(mode="json")}
                await websocket.send_text(json.dumps(payload))
            except Exception:
                await self.disconnect(websocket)

        self.subscriptions[websocket] = push_frame
        simulator.subscribe(push_frame)

    async def disconnect(self, websocket: WebSocket):
        push_frame = self.subscriptions.pop(websocket, None)
        if push_frame:
            simulator.unsubscribe(push_frame)

    async def broadcast(self, payload: dict):
        payload_str = json.dumps(payload)
        for ws in list(self.subscriptions.keys()):
            try:
                await ws.send_text(payload_str)
            except Exception:
                await self.disconnect(ws)


connection_manager = ConnectionManager()
