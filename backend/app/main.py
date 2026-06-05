from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers import telemetry, commands, drones
from app.dependencies import simulator

app = FastAPI(title="Valtec GCS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "http://localhost:5173")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry.router)
app.include_router(commands.router)
app.include_router(drones.router)


@app.on_event("startup")
async def startup():
    await simulator.start()


@app.on_event("shutdown")
async def shutdown():
    await simulator.stop()


@app.get("/health")
async def health():
    return {"status": "ok"}
