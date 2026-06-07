import { configureStore } from "@reduxjs/toolkit";
import droneReducer from "./droneSlice";
import alertReducer from "./alertSlice";
import commandReducer from "./commandSlice";

export const store = configureStore({
  reducer: {
    drones: droneReducer,
    alerts: alertReducer,
    commands: commandReducer,
  },
});

