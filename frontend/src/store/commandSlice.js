import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  // Keyed by drone_id: { command_id, type, status: "executing" | "completed" | "cancelled", created_at }
  byDroneId: {},
};

const commandSlice = createSlice({
  name: "commands",
  initialState,
  reducers: {
    setCommandExecuting(state, action) {
      const { drone_id, command_id, type, created_at } = action.payload;
      state.byDroneId[drone_id] = {
        command_id,
        type,
        status: "executing",
        created_at,
      };
    },
    setCommandCompleted(state, action) {
      const { drone_id, command_id, type, created_at } = action.payload;
      // Ensure we only update if it matches the current executing command
      const current = state.byDroneId[drone_id];
      if (current && current.command_id === command_id) {
        state.byDroneId[drone_id] = {
          command_id,
          type,
          status: "completed",
          created_at: created_at || current.created_at,
        };
      }
    },
    setCommandCancelled(state, action) {
      const { drone_id, command_id, type, created_at } = action.payload;
      const current = state.byDroneId[drone_id];
      if (current && current.command_id === command_id) {
        state.byDroneId[drone_id] = {
          command_id,
          type,
          status: "cancelled",
          created_at: created_at || current.created_at,
        };
      }
    },
    clearCommandState(state, action) {
      const { drone_id } = action.payload;
      delete state.byDroneId[drone_id];
    },
  },
});

export const {
  setCommandExecuting,
  setCommandCompleted,
  setCommandCancelled,
  clearCommandState,
} = commandSlice.actions;

// Selectors
export const selectActiveCommandByDroneId = (drone_id) => (state) =>
  state.commands.byDroneId[drone_id];

export default commandSlice.reducer;
