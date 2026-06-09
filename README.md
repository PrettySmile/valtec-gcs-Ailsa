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

### Bug 1 — Re-render fix (React 效能優化)

[問題分析與效能量測]
- **現況量測 (Measure First)**：
  題目指出每次單一無人機資料更新時，三個 `DroneCard` 都會重新 render。我首先使用 `React Developer Tools` 的 Profiler 觀察渲染耗時與重繪原因，確認當 WebSocket 接收到遙測資料時，會觸發 `FleetDashboard` 及其子組件 `DroneCard` 的全面性無效重新渲染。

[第一階段優化：組件層級快取與引用穩定 (Memoization)]
1. **穩定 Function Reference**：將 `FleetDashboard` 傳遞給 `DroneCard` 的 `handleCommand` 採用 `useCallback` 進行封裝，確保在 Parent re-render 時，傳遞給 Child 的 props 函數引用不變，避免 Child 被誤判需要重繪。
2. **組件快取 (Component Memoization)**：為 `DroneCard` 加上 `React.memo` 進行淺層 props 比較（Shallow Comparison）。在 props 沒變的情況下，不重新 render 組件。
3. **優化成果**：成功將「單一資料變動引發的三個組件全面渲染」限縮至「僅重繪受影響之組件」。

[第二階段優化：細粒度狀態訂閱模式 (Fine-grained Subscription)]
- **目標**：實現「單一無人機更新時，僅重新渲染該 `DroneCard`，完全不觸發 `FleetDashboard` 重新渲染」，將整體渲染複雜度自 $O(N)$ 降低至 $O(1)$ 的局部更新。
- **優化步驟**：
  1. **狀態細分與解耦**：將 `DroneCard` 改為**「自主訂閱模式」**。各無人機組件內部各自使用 `useSelector` 訂閱對應 ID 的狀態，而非由 Parent 統一傳入。
  2. **避免 Parent 牽動**：將 `FleetDashboard` 重新設計，使其**僅訂閱無人機的 `ids` 列表**（而非整個 `byId` 對象）。由於無人機的「數量或 ID 順序」極少變動，當某台無人機的遙測數據（例如電量、座標）更新時，`ids` 陣列引用維持不變，因此 `FleetDashboard` 完全不會被牽動重繪，完美實現 $O(1)$ 局部更新架構。


### Bug 2 — API error handling (API 錯誤合約與架構規範)

為了確保後端 API 的穩定性、可觀測性以及強健的程式設計架構，我實施了以下系統級的重構與修正：

- **[發現問題1] 邊界防禦與業務檢查 (Domain Boundary Defense)**
  - **問題**：後端收到 API 請求時，首要任務是進行參數與狀態檢查，確保不會讓無效的請求繼續執行後續流程。
  - **修正**：在 `command_service.py` 執行 `execute` 時，嚴格校驗無人機狀態。若無人機不存在，拋出特定的領域異常 `DroneNotFoundError`。
- **[發現問題2] 領域異常與傳輸協議解耦 (Domain & Transport Separation)**
  - **問題**：發生異常時，API 需要回傳對應且正確的 HTTP 狀態碼與 JSON 結構，且應避免直接洩漏內部 Exception 堆疊。
  - **修正**：在 `handlers.py` 中建立全域異常處理器（Global Exception Handler），將特定的業務異常（Domain Exception）映射至標準 HTTP 狀態碼（如 `DroneNotFoundError` $\rightarrow$ `404 Not Found`），回傳標準且一致的錯誤合約。
- **[發現問題3] 商業邏輯之合理狀態回傳**
  - **問題**：當無人機為離線狀態（Offline）時，這屬於自動模擬的正常物理現象，若返回代表發送成功的 `accepted` 或拋出 409、500 Exception 皆不合理。
  - **修正**：無人機週期性短暫離線為正常現象，因此不該噴 Exception。API 應回傳 `200 OK`，並將狀態 status 標記為 `rejected`，符合商業規則邏輯。
- **[發現問題4] SOLID 依賴倒置原則 (Dependency Inversion Principle)**
  - **問題**：原本的 `commands.py` 直接實例化 `CommandService`，導致代碼高度耦合、難以進行單元測試。
  - **修正**：引入 FastAPI 的 `Depends` 控制反轉（IoC）與依賴注入（Dependency Injection）機制，將服務與路由層解耦，大幅提升代碼的可測試性與維護性。
- **[發現問題5] 自動化測試覆蓋與邊界模擬 (Automated Testing with Mocks)**
  - **問題**：需要保障後端 API 的穩定性與邊界案例正確性。
  - **修正**：在 `test_commands.py` 中補上完整測試案例（涵蓋正常、不存在、格式錯誤、離線、未預期異常等情境），並使用 `unittest.mock.patch` 進行狀態模擬，打造完備的自動化測試防禦網。
- **[發現問題6] 資源生命週期生命周期管理 (FastAPI Lifespan Upgrade)**
  - **問題**：執行單元測試時出現 Deprecation Warning，原因為 `@app.on_event` 在 FastAPI 中已過時。
  - **修正**：改用 FastAPI 官方推薦最新的 `lifespan` 異步上下文管理器，使測試輸出更乾淨，並確保系統資源能更安全、優雅地初始化與關閉（Clean Shutdown）。
- **[發現問題7] 錯誤碼集中化管理 (Type Safety and Error Schema)**
  - **問題**：錯誤代碼（ErrorCode）若使用純字串容易拼寫錯誤，且難以進行合約定義。
  - **修正**：新增 `ErrorCode` Enum 集中管理常數，並定義 `ErrorResponse` Pydantic Model，確保全站錯誤回傳格式強型別化（Type-safe）且一致。


### Feature 3 — Alert system (警報系統架構設計)

在設計這項功能時，我的架構理念是：儀表板系統（Dashboard）作為控制台，**多個操作員（Multi-operator）看到的畫面必須是完全一致且即時同步的**。因此，我不打算在前端維護複雜的 local state 或本地規則判定，而是採取**「單一事實來源 (Single Source of Truth, SSOT) 與後端控制狀態與廣播」**的核心架構。

[核心設計決策]
1. **單一事實來源與後端規則引擎 (Backend-Driven Rules Engine)**：
   - 所有的告警判定（電量低於 20%、離線超過 5 秒）及手動消除狀態，均由後端 `AlertService` 單例統一控制與維護。
   - 新用戶連線（WebSocket Handshake）時，後端會將當前所有 active 告警事件打包發送，用以初始化前端畫面。
   - 不論有多少使用者同時開著網頁，只要任一操作員消除警報，後端即時更新狀態並發送 WebSocket 廣播通知所有人。此設計保證了多操作員情境下，Dashboard 畫面百分之百同步（No state drift）。
2. **靈活的通訊協議 (Protocol Routing & Multiplexing)**：
   - 設計了 `{"cmd": "...", "data": ...}` 的 WebSocket 封包結構：
     - `cmd: "telemetry"`：向前端發送遙測資料（2 Hz）。
     - `cmd: "alerts"`：向前端發送告警通知。
   - 前端在 `useWebSocket.js` 裡僅需透過一個簡單的 Switch-case 做分流路由，保持職責分離（SRP），後續新增業務指令也極具擴充性。
3. **架構分層與職責分離 (Domain & Transport Separation)**：
   - 保持 FastAPI Router 層（如 `alerts.py`）極致乾淨，路由層僅處理最純粹的傳輸協定，不碰業務細節，所有的業務邏輯一律封裝在 Service 層。
   - 新增 `AlertService` 與 `ConnectionManager`，前者專注處理告警的核心商業邏輯，後者則專注於 WebSocket 連線生命週期生命周期管理與廣播機制。
4. **系統可觀測性與審計日誌 (Observability & Audit Trail)**：
   - 在關鍵業務切點（新增告警、自動解除、手動消除、連線同步）皆加上了統一格式的 `[ALERT LOG]` 輸出，包含精確的時間戳與無人機 ID，讓系統在背景運行時具備極高的可觀測性與排查效率。
5. **UI 設計的可擴充性 (UX Scalability)**：
   - 考量到當無人機規模提升至數百或數千台時，若將警報完全展開會嚴重擠壓介面。
   - 採用「統計聚合與收合」設計，操作員預設看到精簡指標與分類統計，需要時再展開查閱詳細滾動面板，兼顧視覺簡潔度、運維實用性與大規模監控的高擴充性。

---

[狀態設計 (State Design)]

**後端狀態 (Backend State)**
- `AlertService` 的 4 個核心變數（每個 Alert 使用 `{drone_id}-{type}` 作為唯一識別鍵值）：
  1. `active_alerts`: 儲存當前活動中、尚未被消除的所有告警物件。
  2. `dismissed_alerts`: 儲存已被操作員點擊消除的警報識別鍵值。用於滿足「手動消除後，同一次異常不會重複彈出」的題目需求。當無人機狀態恢復正常，該識別鍵會被移出，使下一次異常發生時能再度觸發。
  3. `offline_start_times`: 記錄每台無人機開始離線的時間戳，用以精確判定是否超時 5 秒。
  4. `on_alerts_update`: 依賴注入 callback，將 WebSocket 廣播功能與告警服務解耦。
- **Alert 物件屬性**：
  1. `id` (唯一識別鍵)
  2. `drone_id` (無人機 id)
  3. `type` (告警種類，如: "low_battery" | "offline")
  4. `message` (告警原因及詳細資訊)
  5. `created_at` (告警建立時間)。

**前端狀態 (Frontend State - Redux Store)**
- 保持前端狀態極簡，在 Redux `alertSlice` 中僅維護單一的 `list: []`，不維護複雜的本地判定狀態。
- 當收到最新的 `cmd: "alerts"` 封包時，直接以最簡單、零副作用的覆蓋方式（Overwrite）更新 Redux Store。這確保了前端 View 的呈現永遠與後端 SSOT 狀態同步。


### Feature 4 — Command queue (非阻塞指令佇列與並發控制)

在設計指令佇列時，我著重解決兩個分散式系統的經典問題：**預防隊頭阻塞 (Head-of-Line Blocking Prevention)** 與 **並發任務的優雅中斷 (Asynchronous Graceful Interruption)**。

[設計核心決策]
1. **單機獨立佇列與非阻塞呼叫 (Per-Drone FIFO Queue & Non-Blocking API)**：
   - 當後端收到 `POST /drones/{drone_id}/command` 時，會立刻生成 `Command` 物件並推入該無人機專屬的 `pending` 佇列，然後立即回傳 `200 OK (accepted)`。這能確保 API 的呼叫為非阻塞式，前端不需等待指令執行完畢。
   - 承上，若無人機處於 `offline` 狀態，則立即回傳 `200 OK (rejected)` 給前端。
   - 當後端收到 `GET /drones/{drone_id}/commands/pending` 時，若無人機當下狀態為 `offline`，會因為佇列中的任務第一時間被清空，而正確回傳 `空的佇列` 狀態。
   - **預防隊頭阻塞 (HoL Blocking)**：每台無人機擁有獨立的 `CommandQueue`。這樣設計確保了即使 A 無人機因為離線或執行指令卡住，B 無人機的指令發送與執行完全不受干擾。
2. **協程背景排程器 (Coroutine Background Worker)**：
   - 後端為每台無人機啟動一個異步背景協程（Task Loop）。只要其佇列中有任務，便按順序取出執行，並透過 WebSocket 廣播狀態。
   - 4 種 WebSocket 廣播說明:
      1. `command_executing` (進行中)：前端收到後會展示該指令狀態，並在 DroneCard 狀態欄中套用呼吸漸變動畫。
      2. `command_completed` (完成)：前端收到後亮起綠色提示列。
      3. `command_cancelled` (取消)：前端收到後亮起紅色提示列。
      4. `command_failed` (失敗/錯誤)：當執行或發送出現錯誤、或無人機離線、或請求失敗時，廣播此狀態，前端亮起黃色或紅色警告提示列，確保異常流程可追溯。
3. **Command 的五大狀態 (5  States)**：
   - 後端在 `COMMAND` 模型上嚴謹定義了 5 種狀態的 Literals：
     `status: Literal["pending", "executing", "completed", "cancelled", "failed"] = "pending"`，確保所有指令在系統生命週期中（排隊中、執行中、完成、取消、失敗）皆有跡可循。
4. **離線自動清空與任務中斷機制 (Offline Drain & Cancelation)**：
   - 當無人機狀態轉為 `offline` 時，系統自動觸發以下機制：
     1. **佇列清空 (Drain Pending)**：立刻清空 `pending` 佇列。
     2. **主動任務中斷 (Task Interruption)**：呼叫正在運行的背景協程之 `.cancel()`，強行中斷執行中任務（不浪費模擬等待時間）。
     3. **全域狀態同步 (Broadcast Cancelled)**：將當前執行中與排隊中的指令一併向 WebSocket 廣播 `command_cancelled`，確保所有在線操作員的畫面狀態同步，無任何卡死（Hanging）現象。
5. **前端計時器優化與網路頻寬節省 (Client-Side Simulated Ticker)**：
   - 前端接收到後端傳來的 `started_at` 伺服器時間戳，使用 React 定時器自主以 100ms 頻率即時計算動態的任務執行中秒數。
   - 這避免了後端必須透過高頻 WebSocket 重複傳送時間增量，大幅降低傳輸帶寬與延遲造成的顯示不精準問題。
6. **前端的防禦性競爭條件防護 (React Timer & State Cleanup)**：
   - 任務非 `executing` 的終止狀態僅保留 2 秒顯示時間，倒數完畢後自動隱藏。
   - 為了解決「指令快速連續下達時，前一個指令的倒數定時器會誤抹除新指令狀態」的 Race Condition。我在 `useEffect` 裡將 `setTimeout` 的 timer ID 儲存，並在下一次 effect 執行或組件卸載時，呼叫 `clearTimeout` 清理舊定時器，確保新指令狀態能完美、正確地覆蓋舊提示。

---

[數據結構設計]

**後端 Queue 結構 (backend/app/services/command_service.py)**
- 設計 `QueueStateResponse`，以符合題目要求的 http response schema。
- 每個 `Command` 物件包含：
   1. `command_id` (唯一任務 id、UUID)
   2. `type` (任務種類，Literal["land", "return_home", "hover", "emergency_land"])
   3. `status` (任務狀態，Literal["pending", "executing", "completed", "cancelled", "failed"])
   4. `created_at` (任務的建立時間)
   5. `started_at` (任務的開始執行時間)
   6. `completed_at` (任務的完成時間、取消時間、失敗時間)
   7. `error_message` (任務執行失敗的錯誤訊息)
- 每個無人機專屬 `CommandQueue`：
  - `executing`: 當前執行中的任務 `(Command)` 物件。
  - `pending`: 排隊等待中的任務列表。
  - `task`: 負責推動並執行該佇列背景迴圈的協程。

**前端狀態與安全更新機制 (frontend/src/store/commandSlice.js)**
- 前端只維護極簡的 `byDroneId` 字典映射，接收 WS 廣播動態更新狀態。
- **安全更新防禦過濾 (Race Condition Defense)**：
  1. 若該任務在前端已處於終止狀態 (completed, cancelled, failed)，則不可再被任何過期訊息變更狀態。
  2. 相同任務的廣播訊息，若比前端目前已接收到的時間戳更舊，則予以忽略，防止網路封包時序混亂。
  3. 唯有當前廣播之 UUID 與前端當前呈現任務 UUID 吻合時，才被允許更新狀態，徹底杜絕多指令間的狀態干擾。

