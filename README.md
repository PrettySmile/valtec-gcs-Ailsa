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
python3 -m venv venv && source venv/bin/activate
pip3 install -r requirements.txt
pytest
pytest -v -s --log-cli-level=INFO tests/test_commands.py::test_send_command_unexpected_exception
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
[發現問題1]
- 問題: 後端收到 API 的第一件事是進行參數與狀態檢查，確保不會讓無效的請求繼續執行後續流程。
- 修正: 在 command_service.py 內取得無人機狀態，並在無人機不存在或離線時，拋出對應的 DroneNotFoundError 與 DroneOfflineError。

[發現問題2]
- 問題: 發生異常時，API 需要回傳對應且正確的 HTTP 狀態碼與結構。
- 修正: 透過 handlers.py 全域異常處理器，將 DroneNotFoundError 映射至 404 Not Found， DroneOfflineError  映射至 409 Conflict，回傳標準化錯誤訊息。

[發現問題3]
- 問題: 商務邏輯檢查，當無人機狀態為 offline 時，不應該返回代表發送成功的 accepted 狀態。
- 修正: (這點我先保留，因為如果是 offline 時，或許不該噴錯誤，而是 status 改成 rejected 或 error) 後續考慮修正

[發現問題4]
- 問題: commands.py 原本直接實例化服務，導致代碼耦合度高，不便於未來替換或測試。
- 修正: 引入 FastAPI 的 Depends 機制進行依賴注入（Dependency Injection），實現解耦。

[發現問題5]
- 問題: 需要保障後端 API 的穩定性與邊界案例正確性。
- 修正: 在 test_commands.py 中補上完整測試案例（包含正常、不存在、格式錯誤、離線、未預期異常等情境），並使用 unittest.mock.patch 進行狀態模擬。

[發現問題6]
- 問題: 執行單元測試時出現 Deprecation Warning，原因為 @app.on_event 在 FastAPI 中已過時。
- 修正: 改用 FastAPI 官方推薦最新的 lifespan 異步上下文管理器，使測試輸出更乾淨，代碼符合最新規範。 

[發現問題7]
- 問題: 錯誤代碼（Error Code）若使用純字串易造成拼寫錯誤（Typo），且缺乏統一結構。
- 修正: 新增 ErrorCode Enum 集中管理常數，並定義 ErrorResponse Pydantic Model 確保全站錯誤回傳格式一致。


### Feature 3 — Alert system

_Describe your state design and any decisions you made._

### Feature 4 — Command queue

_Describe your queue design and how you handle the offline drain case._
