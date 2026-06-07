import { useState, useEffect, memo } from "react";
import { useSelector, useDispatch } from "react-redux";
import { selectActiveCommandByDroneId, clearCommandState } from "../store/commandSlice";

const STATUS_STYLES = {
  online: { background: "#e6f4ea", color: "#1e7e34", border: "1px solid #a8d5b0" },
  warning: { background: "#fff8e1", color: "#856404", border: "1px solid #ffd54f" },
  offline: { background: "#fdecea", color: "#b71c1c", border: "1px solid #f5a0a0" },
};

function DroneCard({ id, onCommand }) {
  const dispatch = useDispatch();
  const drone = useSelector(state => state.drones.byId[id]);
  const activeCommand = useSelector(selectActiveCommandByDroneId(id));

  const [sending, setSending] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  // Auto-dismiss Completed or Cancelled status after 2.5 seconds
  useEffect(() => {
    if (activeCommand && (activeCommand.status === "completed" || activeCommand.status === "cancelled")) {
      const timer = setTimeout(() => {
        dispatch(clearCommandState({ drone_id: id }));
      }, 2500);
      return () => clearTimeout(timer);
    }
  }, [activeCommand, id, dispatch]);

  const handleCommand =
    async (type) => {
      setSending(true);
      setLastResult(null);
      try {
        const result = await onCommand(id, type);
        setLastResult({ ok: true, message: result.message });
      } catch (err) {
        setLastResult({ ok: false, message: err.message });
      } finally {
        setSending(false);
      }
    };

  const renderCommandStatus = () => {
    if (!activeCommand) return null;

    let style = {};
    let text = "";
    let isExecuting = false;

    if (activeCommand.status === "executing") {
      isExecuting = true;
      style = {
        background: "#e8f0fe",
        color: "#1a73e8",
        border: "1px solid #aecbfa",
      };
      text = `⚡ 正在執行: ${activeCommand.type.toUpperCase()}...`;
    } else if (activeCommand.status === "completed") {
      style = {
        background: "#e6f4ea",
        color: "#1e7e34",
        border: "1px solid #a8d5b0",
      };
      text = `🟢 ${activeCommand.type.toUpperCase()} 執行完成`;
    } else if (activeCommand.status === "cancelled") {
      style = {
        background: "#fdecea",
        color: "#b71c1c",
        border: "1px solid #f5a0a0",
      };
      text = `🔴 ${activeCommand.type.toUpperCase()} 任務已取消`;
    }

    return (
      <div
        className={isExecuting ? "pulse-glow" : ""}
        style={{
          ...styles.commandBar,
          ...style,
        }}
      >
        {text}
      </div>
    );
  };

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <span style={styles.droneId}>{drone.drone_id}</span>
        <span style={{ ...styles.badge, ...STATUS_STYLES[drone.status] }}>
          {drone.status}
        </span>
      </div>

      {renderCommandStatus()}

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
  commandBar: {
    padding: "6px 12px",
    borderRadius: 8,
    fontSize: 12,
    fontWeight: 500,
    textAlign: "center",
    marginTop: 4,
    marginBottom: 4,
    transition: "all 0.3s ease",
  },
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

export default memo(DroneCard);
