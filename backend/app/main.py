from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers import telemetry, commands, drones
from app.dependencies import simulator
from app.exceptions.handlers import register_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    await simulator.start()
    yield
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

@app.get("/health")
async def health():
    return {"status": "ok"}
