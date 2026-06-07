import React from "react";
import { useSelector } from "react-redux";
import { selectActiveAlerts } from "../store/alertSlice";
import { dismissAlert } from "../api/alertApi";

export default function AlertBanner() {
  const alerts = useSelector(selectActiveAlerts);

  if (!alerts || alerts.length === 0) return null;

  const handleDismiss = async (alertId) => {
    try {
      await dismissAlert(alertId);
    } catch (err) {
      console.error("Failed to dismiss alert:", err);
    }
  };

  return (
    <div style={styles.container}>
      {alerts.map((alert) => {
        const isOffline = alert.type === "offline";
        const alertStyle = isOffline ? styles.alertOffline : styles.alertBattery;
        const icon = isOffline ? "📡" : "⚠️";

        return (
          <div key={alert.id} style={{ ...styles.alert, ...alertStyle }}>
            <span style={styles.icon}>{icon}</span>
            <span style={styles.message}>{alert.message}</span>
            <button
              onClick={() => handleDismiss(alert.id)}
              style={styles.closeButton}
              title="Dismiss alert"
            >
              &times;
            </button>
          </div>
        );
      })}
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    marginBottom: 20,
    width: "100%",
  },
  alert: {
    display: "flex",
    alignItems: "center",
    padding: "12px 18px",
    borderRadius: "10px",
    fontSize: "14px",
    fontWeight: "500",
    border: "1px solid rgba(255, 255, 255, 0.2)",
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
    boxShadow: "0 4px 15px rgba(0, 0, 0, 0.05)",
    transition: "all 0.3s ease",
  },
  alertBattery: {
    background: "rgba(220, 53, 69, 0.12)", // Red glassmorphism
    color: "#b71c1c",
    borderColor: "rgba(220, 53, 69, 0.25)",
  },
  alertOffline: {
    background: "rgba(255, 152, 0, 0.12)", // Orange glassmorphism
    color: "#e65100",
    borderColor: "rgba(255, 152, 0, 0.25)",
  },
  icon: {
    marginRight: "10px",
    fontSize: "16px",
    display: "flex",
    alignItems: "center",
  },
  message: {
    flexGrow: 1,
    lineHeight: "1.4",
  },
  closeButton: {
    background: "transparent",
    border: "none",
    color: "inherit",
    fontSize: "20px",
    cursor: "pointer",
    padding: "0 5px",
    lineHeight: "1",
    opacity: "0.6",
    transition: "opacity 0.2s ease",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
};
