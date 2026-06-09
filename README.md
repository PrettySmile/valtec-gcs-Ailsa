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
2. 為 DroneCard 加上 React.memo。
讓 React 在 props 沒變的情況下，不要重新 render component。
3. 上述兩點，解決了單一無人機資料更新時，三個 DroneCard 都會被重新渲染的問題。

[發現問題2]
後來我用 React Developer Tools 看 render 情況，發現 FleetDashboard 也會一直 re-render，而且耗時挺高。

目標：單一無人機更新時，只更新對應的 DroneCard，不要影響 FleetDashboard。
優化步驟：
1. DroneCard 改成自己 useSelector。
讓每個 DroneCard，只訂閱自己那台 drone 的資料，而不是整個 fleet。
2. FleetDashboard 改成只訂閱 ids，而不是整個 byId。
這樣當某一台 drone 更新時，不會讓 FleetDashboard 被牽動 re-render。


### Bug 2 — API error handling

_List each issue you found and how you fixed it._

[發現問題1]
- 問題: 後端收到 API 的第一件事是進行參數與狀態檢查，確保不會讓無效的請求繼續執行後續流程。
- 修正: 在 command_service.py execute 執行時，檢查無人機狀態，並在無人機不存在時，拋出對應的 DroneNotFoundError。

[發現問題2]
- 問題: 發生異常時，API 需要回傳對應且正確的 HTTP 狀態碼與結構。
- 修正: 透過 handlers.py 全域異常處理器，將 DroneNotFoundError 映射至 404 Not Found，回傳標準化錯誤訊息。

[發現問題3]
- 問題: 商務邏輯檢查，當無人機狀態為 offline 時，不應該返回代表發送成功的 accepted 狀態。
- 修正: 無人機會週期性地短暫離線，這是正常現象，所以不該噴 Exception，而是應該回傳 200，且狀態 status 改為 rejected。

[發現問題4]
- 問題: commands.py 原本直接實例化 CommandService 服務，導致代碼耦合度高，不便於未來替換或測試。
- 修正: 引入 FastAPI 的 Depends 機制進行依賴注入（Dependency Injection），實現解耦。

[發現問題5]
- 問題: 需要保障後端 API 的穩定性與邊界案例正確性。
- 修正: 在 test_commands.py 中補上完整測試案例（包含正常、不存在、格式錯誤、離線、未預期異常等情境），並使用 unittest.mock.patch 進行狀態模擬。

[發現問題6]
- 問題: 盡可能的把問題都妥善處理，執行單元測試時出現 Deprecation Warning，原因為 @app.on_event 在 FastAPI 中已過時。
- 修正: 改用 FastAPI 官方推薦最新的 lifespan 異步上下文管理器，使測試輸出更乾淨，代碼符合最新規範。 

[發現問題7]
- 問題: 錯誤代碼（ErrorCode）若使用純字串易造成拼寫錯誤，且缺乏統一結構。
- 修正: 新增 ErrorCode Enum 集中管理常數，並定義 ErrorResponse Model 確保全站錯誤回傳格式一致。


### Feature 3 — Alert system

_Describe your state design and any decisions you made._

在做這題時，我的想法是：既然是儀表板 (Dashboard) 系統，**多個操作員看到的畫面必須是完全一致且即時同步的**。因此，我不打算在前端用 local state，而是採取**「後端控制狀態與廣播」**的核心架構。

[設計決定]
1. 狀態與廣播全由後端掌握：
   - 所有的告警判斷（電量低於 20%、離線超過 5 秒）、以及手動消除狀態，均由後端 `AlertService` 單例統一控制與維護。
   - 新的使用者打開網頁時，會收到當前所有告警事件的消息，用來初始化該使用者的前端畫面。
   - 不論有多少使用者同時開著網頁，只要有人消除警報或狀態有變，後端就會發送 WebSocket 廣播通知所有人。
   - 這樣做保證了多個使用者看 Dashboard 時，畫面百分之百同步，依然能獲得最即時的通知。
2. 前後端交互的 WebSocket 格式，設計了 `{"cmd": "...", "data": ...}` 的結構：
   - cmd: 用來判斷 前後端交互的命令類型，例如：
      - `cmd: "telemetry"`：向前端發送遙測資料（2 Hz）。
      - `cmd: "alerts"`：向前端發送告警通知。
   - data: 該命令所攜帶的資料。 
   - 這樣一來，前端只要在 `useWebSocket.js` 裡用一個簡單的 switch case 做分流路由就好，保持職責分離，後續加新指令也很好擴充。
3. 讓 Router 層，保持乾淨，無業務邏輯：
   - 讓 FastAPI 的 Router (如 `alerts.py`) 只做最乾淨的 REST API 接口。
   - 商務邏輯一律在services層處理，路由層完全不碰業務細節，這樣代碼最乾淨、也極好寫單元測試。
   - 新增 `AlertService` 與 `ConnectionManager` 兩個業務邏輯，前者只處理跟告警有關的邏輯，而後者只處理跟 WebSocket有關的邏輯。
4. 擁有完整的告警日誌 (Log) 可供查閱：
   - 在 `AlertService` 與 `ConnectionManager` 裡，我加上了統一格式的 `[ALERT LOG]` 列印功能。
   - 無論是「新增告警」、「自動解除」、「手動消除」或是「連線握手時的告警同步」，都會印出帶有精確時間戳的 Log，讓系統在背景運行時極其好排查和調試。
5. 前端畫面編排邏輯：
   - 考慮到未來若有數百台、甚至數千台無人機同時在線，告警訊息在極端情況下數量會非常龐大，若全數展開會嚴重擠壓介面。
   - 因此，我在畫面最上方採用了「收合與統計聚合」的單列精簡顯示（顯示總告警數與分類統計），操作員可自由點擊展開查看詳細的滾動告警面板，兼顧視覺簡潔度、運維實用性與百千台級別無人機的高擴充性。

---

[狀態設計 (State Design)]
**後端狀態**
- `AlertService` 4個核心變數：
  - 每個 alert，都使用 `{drone_id}-{type}`，做為ID鍵值。
  1. `active_alerts`: 儲存當前活動中、還沒被消除的所有告警物件。
  2. `dismissed_alerts`: 儲存已被`操作員點擊`關閉的告警 ID鍵值。(滿足題目(「手動消除後，同一次異常不會重複彈出」)的需求。若無人機狀態恢復正常，該 ID 也會被移出此集合，讓下次異常能再度觸發。
  3. `offline_start_times`: 記錄每台無人機開始 offline 的時間戳，用來精確判定是否超過 5 秒。
  4. `on_alerts_update`: 依賴注入，將 websocket 廣播功能，註冊進此告警服務。
- 每個告警，為一個 Alert 物件，有5個屬性。
   1. id: `{drone_id}-{type}` 唯一鍵值。
   2. drone_id: 無人機id。
   3. type: 告警種類。(ex: "low_battery" | "offline")
   4. message: 告警原因及詳細資訊。
   5. created_at: 告警建立時間。

**前端狀態 (Redux Store)**
- 在 Redux 的 `alertSlice` state 裡，只有一個極簡的 `list: []`。
- 前端直接訂閱這個 `list` 陣列進行渲染，不維護複雜的 local 狀態。
- 當 WebSocket 重新連線、或收到新的 `cmd: "alerts"` 封包時，後端會把最新 active_alerts list 直接打過來覆蓋前端 state。這樣設計確保了前端 UI 永遠是以「後端發過來的最新狀態」，絕不會出現同步差錯。


### Feature 4 — Command queue

_Describe your queue design and how you handle the offline drain case._

[設計決定]
1. 異步佇列排隊 (FIFO Queue)：
   - 當後端收到 `POST /drones/{drone_id}/command` 時，會立刻生成 QueuedCommand 物件，並將它塞往該無人機專屬的 `pending` 佇列，然後立即回傳 http 200，status= accepted 給前端。
      - 這樣設計能確保 API 的呼叫是非阻塞（Non-blocking）的，前端不需等待執行完成。
      - 若無人機處於 offline 狀態，則response 回傳 http 200，status=rejected 給前端。
   - 當後端收到 `GET /drones/{drone_id}/commands/pending` 時，因題目要求，會回傳指令 schema 及其內容。
      - 若無人機當下狀態為 offline，會因為 drain 第一時間被清空，而正確回傳`空的佇列`狀態，http 200，不阻塞前端 UI 的進行。
2. 異步的背景任務執行：
   - 後端為每台無人機啟動一個異步的背景任務協程。
   - 只要 `pending` 佇列內有指令，協程就會按順序取出、將狀態標記為「進行中 (`command_executing`)」並透過 WebSocket 廣播。
   - 任務執行完畢後，WebSocket 廣播「完成 (`command_completed`)」，再接續執行下一個，直到佇列清空。
3. WebSocket 的廣播分流處理，有4種：
   1. `command_executing` (進行中)：前端收到後會展示該指令狀態，並在 DroneCard 狀態欄中套用呼吸漸變動畫。
   2. `command_completed` (完成)：前端收到後亮起綠色提示列。
   3. `command_cancelled` (取消)：前端收到後亮起紅色提示列。
   4. `command_failed` (失敗/錯誤)：當執行或發送出現錯誤、或無人機離線、或請求失敗時，廣播此狀態，前端亮起黃色或紅色警告提示列，確保異常流程可追溯。
   - 除了 `command_executing` 的指令狀態，會持續顯示在畫面上，其他指令狀態僅保留2秒的顯示時間。
   - 若前端收到新的事件廣播，而畫面上仍有舊的狀態(未滿2秒，所以未消失)，此時會強制中止該動畫。
4. 無人機離線自動清空佇列與中斷任務：
   - 讓 `command_service.process_frame` 訂閱遙測數據。一旦接收到無人機狀態轉為 `offline`，則執行以下動作：
      1. **清空 pending 佇列**：避免無人機離線時還留有待執行指令。
      2. **中止當前任務**：主動呼叫背景任務的 `.cancel()` 協程，強制中斷正在運行的 sleep 模擬，不浪費等待時間。
      3. **廣播取消的狀態**：針對「當前執行中」與所有排隊中的指令，一併向 WebSocket 廣播 `command_cancelled` 狀態，讓所有`在線操作員`能即時同步得知任務已被取消，畫面不會卡死。
5. 前端動畫，嚴謹定義「任務進行中、取消、完成、錯誤/失敗」的`動畫顯示`與`動畫消失`的機制：
   1. **自動隱藏**：前端收到廣播狀態時，會啟動一個嚴謹的 2 秒計時器，倒數結束後自動清除狀態提示。
   2. **獨立運作與互不影響**：每個無人機卡片 (DroneCard) 獨立管理自己的計時器，絕不干擾或混淆其他無人機的訊息顯示。
   3. **中斷與清理 (useEffect Cleanup)**：在 React 的 `useEffect` 裡，將 `setTimeout` 的 timer ID 儲存起來。一旦在 2 秒倒數結束前，無人機又重新下發並開始執行新指令，就會觸發清理機制呼叫 `clearTimeout(timer)` 把舊的計時器中斷並銷毀。這確保了新指令狀態能完美覆蓋舊提示，不會被上一輪未結束的舊計時器誤抹除，實現無干擾、可中斷的狀態流轉。
6. 前端自己計時的機制 (Client-Side Running Timer)：
   - 前端透過接收後端傳來的 `started_at` 伺服器時間戳，在前端使用 React 定時器自主以 100ms 頻率即時計算並動態呈現任務已持續執行的秒數。
   - 這避免了後端必須透過高頻 WebSocket 重複傳送時間增量，大幅降低傳輸帶寬與延遲造成的顯示不精準問題。
7. **五大指令狀態生命週期 (5 Command States)**：
   後端與模型層全面新增、支援了 `command_failed` 狀態，並且在 COMMAND 屬性上嚴謹定義了 5 種狀態的 Literals：
   `status: Literal["pending", "executing", "completed", "cancelled", "failed"] = "pending"`
   確保所有指令在系統生命週期中（排隊中、執行中、完成、取消、失敗）皆有跡可循。

---

* 後端設計：
[queue & Command Design]
1. 設計 `QueueStateResponse`，以符合題目需求的 http response schema。
2. 設計 `Command` 為每一任務，這個物件會被加進 queue 中排隊與執行，他有以下屬性。
   - command_id: 唯一任務id，uuid。
   - type: 任務種類，Literal["land", "return_home", "hover", "emergency_land"]。
   - status: 任務狀態，Literal["pending", "executing", "completed", "cancelled", "failed"]
   - created_at: 任務的建立時間。
   - started_at: 任務的開始執行時間。
   - completed_at: 任務的完成時間、取消時間、失敗時間。
   - error_message: 任務執行失敗的錯誤訊息。
3. queue 的設計如下:
   - 在 `CommandService` 內部使用 `self._queues[drone_id]` 維持各無人機狀態。
   - 每個無人機有自己的 queue，型別為 `CommandQueue`，包含以下3種屬性。
      - executing: 當前執行中的任務(Command)對象。
      - pending: 排隊等待中的任務列表。
      - task: 推動佇列狀態的背景任務協程。


* 前端設計：
1. 在 Redux 的 `commandSlice` state 裡，只有一個極簡的 `byDroneId` 字典映射。
   - 前端直接透過即時監聽後端廣播的單向狀態（進行中、完成、取消、失敗）來驅動 UI，利用接收到的開始時間戳自主動態累加計算`任務持續秒數`，配合 `2 秒自動清理機制`，不維護複雜的本地狀態，確保百分之百與後端同步。
2. 接收來自後端的廣播訊息時，會排除以下封包：
   1. 若該任務狀態已終止(如:完成、取消、失敗的狀態)，則不可再變更狀態。
   2. 同個任務的廣播訊息，不接收比當下前端收到的訊息，更早的訊息，防止封包送到前端的時間混亂。
   3. 只能與當前任務uuid相同者，才能對該任務進行狀態的變更。
