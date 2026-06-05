import { useState, useCallback } from "react";
import { sendCommand } from "../api/commandApi";

const STATUS_STYLES = {
  online: { background: "#e6f4ea", color: "#1e7e34", border: "1px solid #a8d5b0" },
  warning: { background: "#fff8e1", color: "#856404", border: "1px solid #ffd54f" },
  offline: { background: "#fdecea", color: "#b71c1c", border: "1px solid #f5a0a0" },
};

function DroneCard({ drone, onCommand }) {
  const [sending, setSending] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  const handleCommand = useCallback(
    async (type) => {
      setSending(true);
      setLastResult(null);
      try {
        const result = await onCommand(drone.drone_id, type);
        setLastResult({ ok: true, message: result.message });
      } catch (err) {
        setLastResult({ ok: false, message: err.message });
      } finally {
        setSending(false);
      }
    },
    [drone.drone_id, onCommand]
  );

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <span style={styles.droneId}>{drone.drone_id}</span>
        <span style={{ ...styles.badge, ...STATUS_STYLES[drone.status] }}>
          {drone.status}
        </span>
      </div>

      <div style={styles.grid}>
        <Stat label="Battery" value={`${drone.battery}%`} warn={drone.battery < 20} />
        <Stat label="Altitude" value={`${drone.gps?.alt ?? "—"} m`} />
        <Stat label="Speed" value={`${drone.speed} m/s`} />
        <Stat label="Heading" value={`${drone.heading}°`} />
        <Stat label="Lat" value={drone.gps?.lat?.toFixed(5) ?? "—"} />
        <Stat label="Lng" value={drone.gps?.lng?.toFixed(5) ?? "—"} />
      </div>

      <div style={styles.actions}>
        <button
          style={styles.button}
          disabled={sending || drone.status === "offline"}
          onClick={() => handleCommand("hover")}
        >
          Hover
        </button>
        <button
          style={styles.button}
          disabled={sending || drone.status === "offline"}
          onClick={() => handleCommand("return_home")}
        >
          RTH
        </button>
        <button
          style={{ ...styles.button, ...styles.dangerButton }}
          disabled={sending}
          onClick={() => handleCommand("emergency_land")}
        >
          Emergency land
        </button>
      </div>

      {lastResult && (
        <p style={{ ...styles.result, color: lastResult.ok ? "#1e7e34" : "#b71c1c" }}>
          {lastResult.message}
        </p>
      )}
    </div>
  );
}

function Stat({ label, value, warn }) {
  return (
    <div style={styles.stat}>
      <span style={styles.statLabel}>{label}</span>
      <span style={{ ...styles.statValue, color: warn ? "#b71c1c" : "inherit" }}>
        {value}
      </span>
    </div>
  );
}

const styles = {
  card: {
    background: "#fff",
    border: "1px solid #e0e0e0",
    borderRadius: 12,
    padding: "16px 20px",
    display: "flex",
    flexDirection: "column",
    gap: 12,
    minWidth: 280,
  },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  droneId: { fontWeight: 500, fontSize: 15 },
  badge: { fontSize: 12, fontWeight: 500, padding: "2px 10px", borderRadius: 20 },
  grid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 12px" },
  stat: { display: "flex", flexDirection: "column", gap: 2 },
  statLabel: { fontSize: 11, color: "#888" },
  statValue: { fontSize: 14, fontWeight: 500 },
  actions: { display: "flex", gap: 8, flexWrap: "wrap" },
  button: {
    padding: "6px 12px",
    borderRadius: 6,
    border: "1px solid #ccc",
    background: "#fafafa",
    cursor: "pointer",
    fontSize: 13,
  },
  dangerButton: {
    borderColor: "#f5a0a0",
    background: "#fff5f5",
    color: "#b71c1c",
  },
  result: { fontSize: 12, margin: 0 },
};

export default DroneCard;
