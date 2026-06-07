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

在做這題時，我的想法是：既然是儀表板 (Dashboard) 系統，**多個操作員看到的畫面必須是完全一致且即時同步的**。因此，我不打算在前端用 local state，而是採取**「後端控制狀態與廣播」**的核心架構。

[設計決定]
1. **狀態與廣播全由後端掌握**：
   所有的告警判斷（電量低於 20%、離線超過 5 秒）、手動消除狀態，均由後端 `AlertService` 單例統一控制與維護。不論有多少使用者同時開著網頁，只要有人消除警報或狀態有變，後端就會發送 WebSocket 廣播通知所有人。這樣做保證了多個使用者看 Dashboard 時，畫面百分之百同步，而且重整網頁也完全不會弄丟狀態（重連時會直接對齊最新 active 警報）。
2. **基於 `cmd` 的 WebSocket 指令分流**：
   我在 WebSocket 設計了 `{"cmd": "...", "data": ...}` 的結構：
   * `cmd: "telemetry"`：接收高頻遙測資料（2 Hz）。
   * `cmd: "alerts"`：同步與接收活動告警列表。
   這樣一來，前端只要在 `useWebSocket.js` 裡用一個簡單的 `switch (parsed.cmd)` 做分流路由就好，保持職責分離，後續加新指令也很好擴充。
3. **把 WebSocket 邏輯與 Router 抽離**：
   我讓 FastAPI 的 Router (如 `alerts.py`) 只做最乾淨的 REST API 接口（如點擊關閉時打的 `POST /alerts/{id}/dismiss`）。核心判定與 WebSocket 的 `broadcast` 實作全都寫在 `AlertService` 與 `ConnectionManager` 內，路由層完全不碰業務細節，這樣代碼最乾淨、也極好寫單元測試。
4. **擁有完整的告警日誌 (Log) 可供查閱**：
   在 `AlertService` 與 `ConnectionManager` 裡，我加上了統一格式的 `[ALERT LOG]` 列印功能。無論是「新增告警」、「自動解除」、「手動消除」或是「連線握手時的告警同步」，都會印出帶有精確時間戳的 Log，讓系統在背景運行時極其好排查和調試。

---

[狀態設計 (State Design)]

為了讓告警狀態在 WebSocket 重新連線時能順利留存（Survive reconnect），我採用了「雙端狀態映射」：

* **後端狀態 (In-Memory State)**：
  在 `AlertService` 維護了三個核心變數：
  * `active_alerts`: dict，用 `"{drone_id}-{type}"` 作為鍵，儲存當前活動中、還沒被消除的告警物件。
  * `dismissed_alerts`: set，記錄已被操作員點擊關閉的告警 ID。這解決了「手動消除後，同一次異常不會重複彈出」的問題（直到無人機狀態恢復正常，該 ID 才會被移出 dismissed 集合，下次異常才能再度觸發）。
  * `offline_start_times`: dict，記錄每台無人機開始 offline 的時間戳，用來精確判定是否超過 5 秒。
* **前端狀態 (Redux Store)**：
  在 `alertSlice` 的 state 裡，只有一個極簡的 `list: []`。
  前端直接訂閱這個 `list` 陣列進行渲染，不維護複雜的 local 狀態。當 WebSocket 重新連線、或收到新的 `cmd: "alerts"` 封包時，後端會把最新 active list 直接打過來覆蓋前端 state。這樣設計確保了前端 UI 永遠是以「後端發過來的最新狀態」為唯一的 Single Source of Truth，絕不會出現同步差錯。

### Feature 4 — Command queue

[設計決定]
1. **異步佇列排隊 (FIFO Queue)**：
   當前端發送 `POST /drones/{drone_id}/command` 時，後端 API 在進行基本的狀態檢查後，會立刻生成隨機 `command_id` 並將其塞入該無人機專屬的 `pending` 佇列，隨後**立即回傳 accepted 狀態**。這樣設計能確保 API 的呼叫是非阻塞（Non-blocking）的，前端不需等待執行完成。
2. **背景協程調度 (Background Runner)**：
   在後端，為每台無人機啟動一個異步的背景任務協程。只要 `pending` 佇列內有指令，協程就會按順序取出、將狀態標記為「進行中 (`command_executing`)」並透過 WebSocket 廣播，接著使用 `asyncio.sleep` 模擬執行 2~4 秒。執行完畢後廣播「完成 (`command_completed`)」，再接續執行下一個，直到佇列清空。
3. **更細緻的 WebSocket 廣播分流**：
   我把 WebSocket 的指令狀態廣播拆細，分成：
   * `command_executing` (進行中)：前端收到後會展示該指令狀態，並在 DroneCard 狀態欄中套用呼吸漸變動畫。
   * `command_completed` (完成)：前端收到後亮起綠色提示列。
   * `command_cancelled` (取消)：前端收到後亮起紅色提示列。
4. **離線自動清空與中斷 (Offline Drain)**：
   將 `command_service.process_frame` 訂閱至 telemetry 遙測數據流。一旦接收到無人機狀態轉為 `offline`：
   * **清空 pending 佇列**：避免無人機離線時還留有待執行指令。
   * **中止當前任務**：主動呼叫背景任務的 `.cancel()` 協程，強制中斷正在運行的 sleep 模擬，不浪費等待時間。
   * **廣播取消狀態**：針對「當前執行中」與「所有排隊中」的指令，一併向 WebSocket 廣播 `command_cancelled` 狀態，讓所有在線操作員能即時同步得知任務已被取消，畫面不會卡死。
5. **前端 2.5 秒自動消失與「中斷防禦」設計 (Timer Management)**：
   * **自動隱藏**：前端收到完成或取消狀態時，會啟動一個 2.5 秒的計時器，倒數結束後自動清除狀態提示。
   * **中斷與清理 (useEffect Cleanup)**：在 React 的 `useEffect` 裡，將 `setTimeout` 的 timer ID 儲存起來。一旦在 2.5 秒倒數結束前，無人機又重新上線並快速發送了新指令（狀態變回 `command_executing`），`useEffect` 就會觸發清理機制呼叫 `clearTimeout(timer)` 把舊的計時器中斷並銷毀。這確保了新指令狀態能完美覆蓋舊提示，不會被上一輪未結束的舊計時器誤抹除。

---

[狀態設計 (State Design)]
* **後端狀態 (In-Memory State)**：
  在 `CommandService` 內部使用 `self._queues[drone_id]` 維持各無人機狀態：
  * `executing`：當前執行中的 `QueuedCommand` 對象。
  * `pending`：排隊等待中的 `QueuedCommand` 列表。
  * `task`：負責背景調度的 `asyncio.Task` 引用。
  在 API 層只在無人機在線時允許下發指令。若無人機離線，打 `GET /drones/{drone_id}/commands/pending` 會因為 offline drain 第一時間被清空而正確回傳空的佇列狀態（200 OK），不阻塞前端 UI 的加載。
* **前端狀態 (Redux Store)**：
  在 `commandSlice` 裡只維護一個極簡的 `byDroneId` 字典映射。前端直接透過 `useWebSocket` 即時監聽後端廣播的單向狀態（進行中、完成、取消）來驅動 UI，不維護複雜的本地邏輯，確保百分之百與後端同步。
