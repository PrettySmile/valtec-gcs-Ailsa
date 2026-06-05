import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  // Keyed by drone_id for O(1) lookup
  byId: {},
  ids: [],
};

const droneSlice = createSlice({
  name: "drones",
  initialState,
  reducers: {
    upsertTelemetry(state, action) {
      const frame = action.payload;
      if (!state.ids.includes(frame.drone_id)) {
        state.ids.push(frame.drone_id);
      }
      state.byId[frame.drone_id] = frame;
    },
    setDroneOffline(state, action) {
      const id = action.payload;
      if (state.byId[id]) {
        state.byId[id].status = "offline";
      }
    },
  },
});

export const { upsertTelemetry, setDroneOffline } = droneSlice.actions;

// Selectors
export const selectDroneIds = (state) => state.drones.ids;
export const selectDroneById = (id) => (state) => state.drones.byId[id];
export const selectAllDrones = (state) =>
  state.drones.ids.map((id) => state.drones.byId[id]);

export default droneSlice.reducer;
