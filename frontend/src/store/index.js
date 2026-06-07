import { configureStore } from "@reduxjs/toolkit";
import droneReducer from "./droneSlice";
import alertReducer from "./alertSlice";

export const store = configureStore({
  reducer: {
    drones: droneReducer,
    alerts: alertReducer,
  },
});

