from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers import telemetry, commands, drones, alerts
from app.dependencies import simulator
from app.exceptions.handlers import register_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.alert_service import alert_service
    from app.services.connection_manager import connection_manager
    alert_service.on_alerts_update = connection_manager.broadcast
    simulator.subscribe(alert_service.process_frame)
    await simulator.start()
    yield
    alert_service.on_alerts_update = None
    simulator.unsubscribe(alert_service.process_frame)
    await simulator.stop()

app = FastAPI(title="Valtec GCS API", lifespan=lifespan)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "http://localhost:5173")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry.router)
app.include_router(commands.router)
app.include_router(drones.router)
app.include_router(alerts.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
