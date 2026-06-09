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

### Bug 1 — Re-render fix (React Performance Optimization)

[Problem Analysis and Performance Measurement]
- **Measure First (Profiling)**:
  The assignment description states that every time a single drone's data updates, all three `DroneCard` components re-render. I first used the `React Developer Tools` Profiler to analyze the render times and identify the causes of re-rendering. I confirmed that when the WebSocket receives telemetry data, it triggers a full, redundant re-render of both `FleetDashboard` and all three `DroneCard` components.

[Phase 1 Optimization: Component-Level Caching and Stable Reference (Memoization)]
1. **Stable Function Reference**: Wrapped the `handleCommand` function passed from `FleetDashboard` to `DroneCard` with the `useCallback` hook. This ensures that the function reference remains constant when the parent re-renders, preventing the child component from incorrectly identifying props changes and triggering unnecessary re-renders.
2. **Component Caching (Memoization)**: Wrapped `DroneCard` with `React.memo` to perform a shallow comparison of its props. If the props do not change, the component will not re-render.
3. **Optimization Result**: Successfully restricted the rendering scope from "all three components re-rendering on a single data update" to "only re-rendering the specific component that actually had data changes."

[Phase 2 Optimization: Fine-grained Subscription Pattern]
- **Goal**: Achieve a setup where "when a single drone updates, only its corresponding `DroneCard` re-renders, without triggering a re-render of `FleetDashboard` at all." This reduces the overall rendering complexity from $O(N)$ to $O(1)$ local updates.
- **Optimization Steps**:
  1. **State Fine-Graining and Decoupling**: Refactored `DroneCard` to a self-subscribing model. Each drone component now uses the `useSelector` hook to subscribe directly to its own state by ID, rather than receiving the state passed down from its parent.
  2. **Eliminating Parent Involvement**: Redesigned `FleetDashboard` to subscribe only to the list of drone `ids` (rather than the entire `byId` object). Since the number of drones and their ID ordering rarely change, when a drone's telemetry (e.g., battery, coordinates) updates, the reference to the `ids` array remains unchanged. Thus, the parent `FleetDashboard` is not triggered to re-render, perfectly achieving an $O(1)$ local update architecture.


### Bug 2 — API error handling (API Error Contract and Architecture Standards)

To ensure the stability, observability, and robust architecture of the backend API, I implemented the following system-level refactoring and fixes:

- **[Issue 1] Domain Boundary Defense and Business Checks**
  - **Problem**: When the backend receives an API request, the first priority is to perform parameter and state validation to prevent invalid requests from proceeding further.
  - **Fix**: Implemented strict validation of drone status within `execute` in `command_service.py`. If a drone does not exist, it throws a specific domain exception: `DroneNotFoundError`.
- **[Issue 2] Domain and Transport Separation**
  - **Problem**: When an exception occurs, the API must return the correct and matching HTTP status code and JSON structure, while avoiding direct exposure of internal stack traces.
  - **Fix**: Created a Global Exception Handler in `handlers.py` to map specific domain exceptions to standard HTTP status codes (e.g., `DroneNotFoundError` $\rightarrow$ `404 Not Found`), thereby returning a standardized and consistent error contract.
- **[Issue 3] Reasonable Status Response for Business Logic**
  - **Problem**: When a drone is offline, this is a normal simulated behavior. It is unreasonable to return an `accepted` status representing successful command delivery, or to throw a 409 or 500 exception.
  - **Fix**: Since periodic brief offline states are normal drone behaviors, they should not trigger an exception. Instead, the API returns a `200 OK` response with the command status set to `rejected`, aligning with the business logic.
- **[Issue 4] SOLID Dependency Inversion Principle**
  - **Problem**: Originally, `commands.py` directly instantiated `CommandService`, resulting in high coupling and making unit testing difficult.
  - **Fix**: Introduced FastAPI's `Depends` for Dependency Injection (DI) and Inversion of Control (IoC), decoupling the route handlers from the business services. This significantly improves code testability and maintainability.
- **[Issue 5] Automated Testing with Mocks**
  - **Problem**: Ensuring the reliability of the backend API and verifying edge cases is critical.
  - **Fix**: Added comprehensive test cases in `test_commands.py` (covering success, non-existent drones, invalid schemas, offline drones, and unexpected exceptions) and utilized `unittest.mock.patch` for state mocking, building a robust automated test suite.
- **[Issue 6] Lifecycle Resource Management (FastAPI Lifespan)**
  - **Problem**: Running unit tests generated deprecation warnings because `@app.on_event` is deprecated in FastAPI.
  - **Fix**: Migrated to the modern FastAPI-recommended `lifespan` asynchronous context manager, cleaning up test output and ensuring system resources are initialized and cleaned up safely and gracefully (Clean Shutdown).
- **[Issue 7] Centralized Error Code Management (Type Safety and Error Schema)**
  - **Problem**: Using plain strings for `ErrorCode` leads to spelling typos and lacks a structured contract definition.
  - **Fix**: Introduced an `ErrorCode` Enum to centralize error constants, and defined an `ErrorResponse` Pydantic model to guarantee typed, consistent error responses across the entire application.


### Feature 3 — Alert system (Alert System Architecture Design)

When designing this feature, my architectural philosophy was: as a control dashboard, the screen seen by multiple operators (multi-operator setup) must be fully identical and synchronized in real-time. Therefore, I avoided maintaining complex local state or local rule-checking on the frontend, and instead adopted a centralized architecture based on a **Single Source of Truth (SSOT)** with **Backend-Driven State and Broadcast**.

[Core Design Decisions]
1. **Single Source of Truth and Backend-Driven Rules Engine**:
   - All alert evaluations (battery under 20%, offline for over 5 seconds) and operator dismissals are centrally managed and maintained by the backend `AlertService` singleton.
   - When a new user connects (WebSocket Handshake), the backend packages all currently active alert events and sends them to initialize the user's frontend screen.
   - No matter how many operators have the dashboard open simultaneously, when any operator dismisses an alert, the backend updates the state immediately and broadcasts it via WebSockets. This ensures 100% synchronization among all operators without state drift (No state drift).
2. **Flexible Communication Protocol (Protocol Routing & Multiplexing)**:
   - Designed a unified WebSocket packet structure: `{"cmd": "...", "data": ...}`:
     - `cmd: "telemetry"`: Stream telemetry data to the frontend (at 2 Hz).
     - `cmd: "alerts"`: Stream alert notifications to the frontend.
   - On the frontend, `useWebSocket.js` only needs a simple Switch-case to route incoming messages, maintaining Single Responsibility Principle (SRP) and making it extremely easy to scale for new commands in the future.
3. **Architectural Layering and Separation of Concerns (Domain & Transport Separation)**:
   - Kept the FastAPI Router layer (e.g., `alerts.py`) extremely clean. Routers only manage network transport and do not touch business details. All business logic is encapsulated in the Service layer.
   - Added `AlertService` and `ConnectionManager`. The former focuses solely on the core business logic of alerts, while the latter manages WebSocket connection lifecycles and broadcast mechanisms.
4. **System Observability and Audit Trail**:
   - Added standardized `[ALERT LOG]` outputs with precise timestamps and drone IDs at critical business checkpoints (new alerts, auto-resolves, manual dismissals, connection handshakes). This provides high observability and diagnostic efficiency during system background execution.
5. **UX Scalability**:
   - Anticipating scenarios where scaling to hundreds or thousands of drones could result in an overwhelming number of active alerts, rendering them in a fully expanded list would compress the interface.
   - Adopted a "Collapsible Metric Aggregation" UI pattern. Operators default to a high-level summary count and categories, and can expand it to scroll through detailed alerts. This balances UI cleanliness, operator usability, and high scalability for large fleets monitored by operators.

---

[State Design]

**Backend State**
- The `AlertService` manages 4 core variables (using `{drone_id}-{type}` as a unique identification key for each alert):
  1. `active_alerts`: Stores all currently active and undismissed alert objects.
  2. `dismissed_alerts`: Stores the unique keys of alerts manually dismissed by operators. This satisfies the requirement that "once dismissed, the same alert will not pop up again during the same incident." Once a drone returns to normal, its key is removed from this set, allowing future anomalies to trigger alerts again.
  3. `offline_start_times`: Records the starting timestamp when a drone goes offline, used to determine whether the 5-second offline threshold is exceeded.
  4. `on_alerts_update`: A dependency-injected callback that decouples the WebSocket broadcasting function from the Alert Service.
- **Alert Object Properties**:
  1. `id` (Unique key)
  2. `drone_id` (Drone ID)
  3. `type` (Alert type: `"low_battery" | "offline"`)
  4. `message` (Alert reason and details)
  5. `created_at` (Alert creation timestamp)

**Frontend State (Redux Store)**
- Keeps frontend state minimal. The Redux `alertSlice` only maintains a flat `list: []`, avoiding complex local state or validation logic.
- When the frontend receives a `cmd: "alerts"` packet, it overwrites the Redux list directly in a stateless, side-effect-free manner. This guarantees that the UI is always perfectly in sync with the backend SSOT.


### Feature 4 — Command queue (Non-Blocking Command Queue and Concurrency Control)

When designing the command queue, I focused on resolving two classic distributed system problems: **Head-of-Line (HoL) Blocking Prevention** and **Graceful Asynchronous Task Interruption**.

[Core Design Decisions]
1. **Per-Drone FIFO Queue and Non-Blocking Calls**:
   - When the backend receives `POST /drones/{drone_id}/command`, it immediately creates a `Command` object, pushes it into that drone's dedicated `pending` queue, and returns `200 OK (accepted)`. This ensures that API calls are non-blocking, so the client does not wait for command execution.
   - Similarly, if the drone is currently `offline`, it immediately returns `200 OK (rejected)` to the frontend.
   - When the backend receives `GET /drones/{drone_id}/commands/pending` and the drone is `offline`, it correctly returns an empty queue status since the queue is drained immediately upon offline detection.
   - **Head-of-Line (HoL) Blocking Prevention**: Each drone has its own independent `CommandQueue`. This isolates issues, ensuring that even if Drone A gets stuck or goes offline, Drone B's command queue and execution proceed completely unaffected.
2. **Coroutine Background Worker**:
   - The backend runs an asynchronous background coroutine (Task Loop) for each drone. As long as there are tasks in the queue, it processes them sequentially and broadcasts their status over WebSockets.
   - **4 WebSocket Broadcast Types**:
     1. `command_executing` (Executing): Indicates execution is underway. The frontend renders the command details and applies a pulsing animation in the `DroneCard` status bar.
     2. `command_completed` (Completed): Indicates success. The frontend displays a green success status.
     3. `command_cancelled` (Cancelled): Indicates cancellation. The frontend displays a red cancelled status.
     4. `command_failed` (Failed/Error): Indicates a failure. If an execution error occurs, or connection fails, the backend broadcasts this state, causing a yellow or red warning status to show on the UI, ensuring full traceability of exceptions.
3. **The 5 Command States**:
   - The backend strictly defines a 5-state lifecycle model for commands using Python typing Literals:
     `status: Literal["pending", "executing", "completed", "cancelled", "failed"] = "pending"` to ensure every command is traceable throughout its entire lifecycle (pending, executing, completed, cancelled, failed).
4. **Offline Drain and Cancellation Mechanism**:
   - When a drone transitions to `offline`, the system automatically triggers:
     1. **Drain Pending**: Immediately flushes the entire `pending` queue.
     2. **Asynchronous Task Interruption**: Calls `.cancel()` on the active background coroutine to gracefully but immediately terminate the currently executing command (without wasting simulation sleep time).
     3. **Broadcasting Cancellations**: Broadcasts `command_cancelled` for both the running and queued commands to ensure all connected operators' screens sync instantly without UI lockups or hanging state indicators.
5. **Client-Side Simulated Ticker (Network Bandwidth Optimization)**:
   - The frontend reads the `started_at` server timestamp and runs a local React ticker updating every 100ms to compute and render the elapsed execution time.
   - This avoids high-frequency WebSocket updates from the backend merely to tick a timer, drastically reducing network bandwidth and avoiding UI lagging/jitter caused by network latency.
6. **Client-Side Defensive Race Condition Protection (React Timer and State Cleanup)**:
   - Finished commands (completed, cancelled, or failed) only remain visible on screen for 2 seconds before being automatically cleared.
   - To prevent the race condition where rapidly sending consecutive commands causes the timer of a previous command to clear the UI status of a newly started command, I store the `setTimeout` reference. In the React `useEffect` cleanup (or when the component unmounts), I clear the timer via `clearTimeout(timer)`. This ensures that subsequent command states cleanly overwrite previous ones without being prematurely erased.

---

[Data Structure Design]

**Backend Queue Structure (backend/app/services/command_service.py)**
- Designed `QueueStateResponse` to match the exact HTTP response schema required by the assignment.
- Each `Command` object contains:
  1. `command_id` (Unique task ID, UUID)
  2. `type` (Task type: `Literal["land", "return_home", "hover", "emergency_land"]`)
  3. `status` (Task status: `Literal["pending", "executing", "completed", "cancelled", "failed"]`)
  4. `created_at` (Command creation timestamp)
  5. `started_at` (Command execution start timestamp)
  6. `completed_at` (Command completion/cancellation/failure timestamp)
  7. `error_message` (Detailed error message if the command fails)
- Each drone has an isolated `CommandQueue` composed of:
  - `executing`: The currently active `Command` object.
  - `pending`: A list of queued `Command` objects waiting for execution.
  - `task`: The background coroutine (`asyncio.Task`) that drives the queue loop.

**Frontend State & Safe Update Controls (frontend/src/store/commandSlice.js)**
- The frontend maintains a minimal `byDroneId` dictionary mapping in the Redux store, updating dynamically based on incoming WebSocket broadcasts.
- **Race Condition Defensive Filtering**:
  1. **Strict Lifecycle Locks**: Once a command reaches a terminal state (completed, cancelled, or failed), its state on the UI can no longer be modified by any delayed network messages.
  2. **Timestamp Validation**: Incoming WebSocket broadcasts with timestamps older than the currently displayed state are ignored to prevent out-of-order network packets from reverting state.
  3. **ID Matching**: Updates are allowed only if the incoming packet's UUID matches the active command's UUID in the frontend store, preventing multiple commands from corrupting each other's states.

