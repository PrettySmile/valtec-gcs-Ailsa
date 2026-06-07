import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  list: [],
};

const alertSlice = createSlice({
  name: "alerts",
  initialState,
  reducers: {
    setAlerts(state, action) {
      state.list = action.payload;
    },
  },
});

export const { setAlerts } = alertSlice.actions;

// Selectors
export const selectActiveAlerts = (state) => state.alerts.list;

export default alertSlice.reducer;
