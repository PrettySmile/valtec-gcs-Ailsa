# Valtec GCS — Take-Home Assignment

**Role:** Senior Full Stack Engineer (Drone Swarm Systems)  
**Time limit:** 1 week  
**Estimated effort:** 4–6 hours  
**Stack:** React (frontend) · FastAPI (backend)

---

## Overview

This repo contains a simplified Ground Control Station (GCS) that monitors a fleet of 3 simulated drones via WebSocket telemetry. The codebase is intentionally incomplete and contains bugs.

Your tasks:

| # | Type | Area | Description |
|---|------|------|-------------|
| 1 | 🐛 Bug fix | Frontend | Fix a React re-render performance issue |
| 2 | 🐛 Bug fix | Backend | Fix incomplete API error handling |
| 3 | ✨ Feature | Frontend | Implement an alert/warning system |
| 4 | ✨ Feature | Backend | Implement a per-drone command queue |

Complete all 4 tasks. Document your decisions in the README.

---

## Getting started

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Or use Docker:

```bash
docker-compose up
```

Open `http://localhost:5173` to see the dashboard.

---

## Task 1 — Bug fix: React re-render performance (Frontend)

**File:** `frontend/src/components/FleetDashboard.jsx`  
**Symptom:** Open the browser's React DevTools Profiler. You will notice that every time any single drone's telemetry updates (which happens at 2 Hz), **all three DroneCard components re-render**, even if their data has not changed. At higher drone counts or update frequencies, this causes visible UI lag.

**Your task:**
1. Identify the root cause of the unnecessary re-renders.
2. Fix it without changing the observable behaviour of the dashboard.
3. In your README, briefly explain what was wrong and what you changed.

> Hint: there is more than one contributing factor.

---

## Task 2 — Bug fix: API error handling (Backend)

**File:** `backend/app/routers/commands.py`  
**Symptom:** The command endpoint has several error handling gaps that cause poor behaviour in edge cases.

**Your task:**
1. Find and fix all error handling issues in the endpoint.
2. Make sure the API returns meaningful HTTP status codes and error messages for all failure cases.
3. In your README, list each issue you found and how you fixed it.

> Do not change the endpoint's URL or request/response schema.

---

## Task 3 — Feature: Alert system (Frontend)

The dashboard currently displays telemetry numbers but provides no warnings when something goes wrong.

**Requirements:**
- Show an alert banner at the top of the dashboard when **any** of the following conditions are met:
  - A drone's battery level drops below **20%**
  - A drone's connection has been lost for more than **5 seconds** (status becomes `offline`)
- Each alert must identify which drone triggered it (by drone ID or name).
- Multiple alerts can be active simultaneously.
- Each alert can be **individually dismissed** by the user.
- Dismissed alerts should **not** reappear unless the condition clears and then re-triggers.

**Constraints:**
- Do not add any new npm packages.
- The alert state should survive a WebSocket reconnect.

---

## Task 4 — Feature: Per-drone command queue (Backend)

Currently `POST /drones/{drone_id}/command` is fire-and-forget with no queuing.

**Requirements:**
- Each drone has its own **FIFO command queue**.
- Only **one command executes at a time** per drone. Additional commands submitted while one is running are queued.
- Add a new endpoint: `GET /drones/{drone_id}/commands/pending` that returns the queue state for that drone.
- Simulated execution time per command: **2–4 seconds** (use `asyncio.sleep` with a random value in that range).
- If a drone goes `offline`, **drain its queue** and return an appropriate error for any pending commands.

**Response schema for the new endpoint:**

```json
{
  "drone_id": "drone-1",
  "executing": { "command_id": "abc", "type": "land", "submitted_at": "..." },
  "pending": [
    { "command_id": "def", "type": "return_home", "submitted_at": "..." }
  ]
}
```

---

## Submission

- Push your work to a **public GitHub repo** (or grant access to `valtec-hiring`).
- Your commit history should reflect your working process — please do not squash everything into one commit.
- We will ask you to walk through your code in the technical interview. Any part of the codebase is fair game.

---

## Evaluation criteria

| Area | Weight |
|------|--------|
| Bug fixes — correctness and explanation | 40% |
| Feature implementation — correctness and edge case handling | 60% |
