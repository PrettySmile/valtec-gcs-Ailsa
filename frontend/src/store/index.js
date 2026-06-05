import { configureStore } from "@reduxjs/toolkit";
import droneReducer from "./droneSlice";

export const store = configureStore({
  reducer: {
    drones: droneReducer,
  },
});
