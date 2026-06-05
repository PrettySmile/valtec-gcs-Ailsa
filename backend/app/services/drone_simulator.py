import asyncio
import random
from datetime import datetime, timezone
from typing import Dict

from app.models.drone import TelemetryFrame, GPSCoordinate

DRONE_IDS = ["drone-1", "drone-2", "drone-3"]

# Starting positions around a central point (Taipei 101 area)
BASE_POSITIONS = {
    "drone-1": (25.0330, 121.5654),
    "drone-2": (25.0340, 121.5670),
    "drone-3": (25.0320, 121.5640),
}


class DroneState:
    def __init__(self, drone_id: str):
        self.drone_id = drone_id
        lat, lng = BASE_POSITIONS[drone_id]
        self.lat = lat
        self.lng = lng
        self.alt = random.uniform(50, 120)
        self.battery = random.uniform(60, 100)
        self.speed = random.uniform(5, 15)
        self.heading = random.uniform(0, 360)
        self.status = "online"
        self._offline_until: float = 0.0
        self._tick = 0

    def tick(self) -> TelemetryFrame:
        import time

        self._tick += 1
        now = time.monotonic()

        # Randomly trigger a brief offline window every ~55 ticks
        if self._tick % random.randint(50, 65) == 0:
            self._offline_until = now + random.uniform(6, 10)

        if now < self._offline_until:
            self.status = "offline"
        else:
            # Drift position slightly
            self.lat += random.uniform(-0.00005, 0.00005)
            self.lng += random.uniform(-0.00005, 0.00005)
            self.alt += random.uniform(-1, 1)
            self.alt = max(10, min(200, self.alt))

            # Drain battery slowly
            self.battery -= random.uniform(0.02, 0.06)
            self.battery = max(0, self.battery)

            self.speed = max(0, self.speed + random.uniform(-1, 1))
            self.heading = (self.heading + random.uniform(-5, 5)) % 360

            self.status = "warning" if self.battery < 20 else "online"

        return TelemetryFrame(
            drone_id=self.drone_id,
            timestamp=datetime.now(timezone.utc),
            battery=round(self.battery, 1),
            gps=GPSCoordinate(
                lat=round(self.lat, 6),
                lng=round(self.lng, 6),
                alt=round(self.alt, 1),
            ),
            speed=round(self.speed, 1),
            heading=round(self.heading, 1),
            status=self.status,
        )


class DroneSimulator:
    def __init__(self):
        self._drones: Dict[str, DroneState] = {
            drone_id: DroneState(drone_id) for drone_id in DRONE_IDS
        }
        self._subscribers: list = []
        self._task: asyncio.Task | None = None

    def get_drone_ids(self) -> list[str]:
        return DRONE_IDS

    def get_drone_status(self, drone_id: str) -> str | None:
        state = self._drones.get(drone_id)
        return state.status if state else None

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def unsubscribe(self, callback):
        self._subscribers.remove(callback)

    async def start(self):
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        if self._task:
            self._task.cancel()

    async def _run(self):
        while True:
            for drone_id, state in self._drones.items():
                frame = state.tick()
                for cb in list(self._subscribers):
                    try:
                        await cb(frame)
                    except Exception:
                        pass
            await asyncio.sleep(0.5)  # 2 Hz
