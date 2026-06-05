import { useSelector, useDispatch } from "react-redux";
import DroneCard from "./DroneCard";
import { sendCommand } from "../api/commandApi";

// -----------------------------------------------------------------------
// BUG #1 — This component has a React re-render performance problem.
//
// Symptom: open React DevTools Profiler and observe that every time ANY
// single drone's telemetry updates, ALL DroneCard components re-render,
// even if their data has not changed.
//
// Your task (see ASSIGNMENT.md Task 1):
//   Find the root cause(s) and fix them without changing the visible
//   behaviour of the dashboard.
// -----------------------------------------------------------------------

function FleetDashboard() {
  const dispatch = useDispatch();

  const drones = useSelector((state) => state.drones);

  const droneList = drones.ids.map((id) => drones.byId[id]);

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Valtec GCS — Fleet Dashboard</h1>
        <span style={styles.subtitle}>{droneList.length} drones connected</span>
      </header>

      <div style={styles.grid}>
        {droneList.map((drone) => (
          <DroneCard
            key={drone.drone_id}
            drone={drone}
            onCommand={(droneId, type) => sendCommand(droneId, type)}
          />
        ))}
      </div>
    </div>
  );
}

const styles = {
  container: { padding: "24px 32px", maxWidth: 1200, margin: "0 auto" },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "baseline",
    marginBottom: 24,
  },
  title: { fontSize: 22, fontWeight: 500, margin: 0 },
  subtitle: { fontSize: 14, color: "#888" },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
    gap: 16,
  },
};

export default FleetDashboard;
