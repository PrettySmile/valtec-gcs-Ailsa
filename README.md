# Valtec GCS

A simplified Ground Control Station for monitoring a simulated drone fleet.

## Stack

- **Frontend:** React 18, Redux Toolkit, Vite
- **Backend:** Python 3.11, FastAPI, WebSockets
- **Infra:** Docker Compose

## Quick start

```bash
docker-compose up
```

Frontend: http://localhost:5173  
Backend API docs: http://localhost:8000/docs

## Running backend tests

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest
```

## Project structure

```
valtec-gcs-assignment/
├── frontend/
│   └── src/
│       ├── components/     # React UI components
│       ├── hooks/          # Custom hooks (WebSocket, telemetry)
│       ├── store/          # Redux slices
│       ├── api/            # REST API calls
│       └── utils/          # Helpers
├── backend/
│   ├── app/
│   │   ├── routers/        # FastAPI route handlers
│   │   ├── services/       # Business logic
│   │   └── models/         # Pydantic models
│   └── tests/
└── docker-compose.yml
```

## Architecture

The backend runs a drone simulator that generates telemetry for 3 virtual drones at 2 Hz. Each drone periodically goes offline for a short window — this is simulated automatically and is expected behaviour. A WebSocket endpoint streams this data to connected frontend clients. The frontend maintains a Redux store of drone states and renders a real-time dashboard.

```
Drone Simulator → WebSocket stream → Redux store → Dashboard UI

Frontend → REST POST /command → Command Service → Drone Simulator
```

## Known simplifications

This codebase is intentionally simplified for a single-process, in-memory environment. Not everything here reflects production best practices — that's on purpose.

---

## Your notes (fill this in)

### Bug 1 — Re-render fix

_Describe what was wrong and what you changed._
[發現問題1]
題目一開始就有說，每次單一無人機資料更新時，三個 DroneCard 都會重新 render。
所以我第一步是先加 console 去確認實際情況，結果發現：
    當 WebSocket 收到資料時，確實會導致 FleetDashboard 和三個 DroneCard 都一起 re-render。
我的優化步驟：
1. 先處理 FleetDashboard 的 handleCommand。
使用 useCallback，讓傳給 DroneCard 的 function reference 不會因為每次 render 都變動，避免 child 因 props 變化而被誤判需要更新。
2. DroneCard 加上 React.memo。
讓 React 在 props 沒變的情況下，不要重新 render component。
上述兩點，解決了單一無人機資料更新時，三個 DroneCard 都會被重新渲染的問題。

[發現問題2]
後來我用 React Developer Tools 看 render 情況，發現 FleetDashboard 本身也會一直 re-render，而且耗時挺高。
目標：單一無人機更新時，只更新對應的 DroneCard，不要影響 FleetDashboard。
再做了兩個調整：
1. DroneCard 改成自己 useSelector。
讓每個 DroneCard，只訂閱自己那台 drone 的資料，而不是整個 fleet。
2. FleetDashboard 改成只訂閱 ids，而不是整個 byId。
這樣當某一台 drone 更新時，不會讓 FleetDashboard 被牽動 re-render。


### Bug 2 — API error handling

_List each issue you found and how you fixed it._

### Feature 3 — Alert system

_Describe your state design and any decisions you made._

### Feature 4 — Command queue

_Describe your queue design and how you handle the offline drain case._
