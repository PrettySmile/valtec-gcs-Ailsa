import { useCallback } from "react";
import { useSelector } from "react-redux";
import DroneCard from "./DroneCard";
import AlertBanner from "./AlertBanner";
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
  console.log("FleetDashboard render");
  
  const droneIds = useSelector((state) => state.drones.ids);
  const handleCommand = useCallback((droneId, type) => sendCommand(droneId, type), []);

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Valtec GCS — Fleet Dashboard</h1>
        <span style={styles.subtitle}>{droneIds.length} drones connected</span>
      </header>

      <AlertBanner />

      <div style={styles.grid}>
        {droneIds.map((id) => (
          <DroneCard
            key={id}
            id={id}
            onCommand={handleCommand}
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
