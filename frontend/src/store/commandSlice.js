import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  // Keyed by drone_id: { command_id, type, status: "executing" | "completed" | "cancelled" | "failed", created_at }
  byDroneId: {},
};

const TERMINAL_STATES = ["completed", "cancelled", "failed"];

// Helper to handle command state updates with guard checks
const updateCommandState = (state, action, defaultStatus) => {
  const { drone_id, command_id, type, created_at, started_at, completed_at, status, error_message } = action.payload;
  const current = state.byDroneId[drone_id];
  const resolvedStatus = status || defaultStatus;

  if (current) {
    // 🛡️ Same-command guard: cannot roll back once terminal state is reached
    if (current.command_id === command_id && TERMINAL_STATES.includes(current.status)) {
      return;
    }
    // 🛡️ Cross-command guard: if the newly received command creation time is older than the currently displayed one, discard it directly.
    if (current.command_id !== command_id && new Date(created_at) < new Date(current.created_at)) {
      return;
    }
  }

  // 🛡️ Guard: Terminal states can only be set if the command matches the current executing command
  if (TERMINAL_STATES.includes(resolvedStatus)) {
    if (!current || current.command_id !== command_id) {
      return;
    }
  }

  state.byDroneId[drone_id] = {
    command_id,
    type,
    status: resolvedStatus,
    created_at: created_at || (current ? current.created_at : null),
    started_at: started_at || (current ? current.started_at : null),
    completed_at: completed_at || (current ? current.completed_at : null),
    ...(error_message !== undefined ? { error_message } : {}),
  };
};

const commandSlice = createSlice({
  name: "commands",
  initialState,
  reducers: {
    setCommandPending(state, action) {
      updateCommandState(state, action, "pending");
    },
    setCommandExecuting(state, action) {
      updateCommandState(state, action, "executing");
    },
    setCommandCompleted(state, action) {
      updateCommandState(state, action, "completed");
    },
    setCommandCancelled(state, action) {
      updateCommandState(state, action, "cancelled");
    },
    setCommandFailed(state, action) {
      updateCommandState(state, action, "failed");
    },
    clearCommandState(state, action) {
      const { drone_id, command_id } = action.payload;
      const current = state.byDroneId[drone_id];
      // Defensive guard: Only clear if the active command_id still matches the one being dismissed
      if (current && current.command_id === command_id) {
        delete state.byDroneId[drone_id];
      }
    },
  },
});

export const {
  setCommandPending,
  setCommandExecuting,
  setCommandCompleted,
  setCommandCancelled,
  setCommandFailed,
  clearCommandState,
} = commandSlice.actions;

// Selectors
export const selectActiveCommandByDroneId = (drone_id) => (state) =>
  state.commands.byDroneId[drone_id];

export default commandSlice.reducer;
