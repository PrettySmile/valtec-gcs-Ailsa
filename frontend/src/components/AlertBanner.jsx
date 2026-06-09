import React, { useState, useMemo } from "react";
import { useSelector } from "react-redux";
import { selectActiveAlerts } from "../store/alertSlice";
import { dismissAlert } from "../api/alertApi";

export default function AlertBanner() {
  const alerts = useSelector(selectActiveAlerts);
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const handleDismiss = async (alertId) => {
    try {
      await dismissAlert(alertId);
    } catch (err) {
      console.error("Failed to dismiss alert:", err);
    }
  };

  // Filter alerts by drone ID or message based on search input (great for scale)
  const filteredAlerts = useMemo(() => {
    if (!alerts) return [];
    return alerts.filter((alert) =>
      alert.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alert.id.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [alerts, searchQuery]);

  // Aggregate stats by type
  const stats = useMemo(() => {
    if (!alerts) return { offline: 0, battery: 0, total: 0 };
    const offline = alerts.filter((a) => a.type === "offline").length;
    const battery = alerts.filter((a) => a.type === "battery").length;
    return { offline, battery, total: alerts.length };
  }, [alerts]);

  // When system is completely nominal, render a matching green status bar to avoid layout shifting (CLS)
  if (!alerts || alerts.length === 0) {
    return (
      <div style={styles.healthyContainer}>
        <div style={styles.summaryHeader}>
          <div style={styles.summaryLeft}>
            <span style={styles.healthyBadge}>🟢 All Systems Nominal</span>
            <span style={styles.summaryText}>
              No active alerts. All connected drones are performing as expected.
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Summary Header (Always compact, occupies single-row height regardless of scale) */}
      <div style={styles.summaryHeader}>
        <div style={styles.summaryLeft}>
          <span style={styles.alertCountBadge}>🚨 {stats.total} Active Alerts</span>
          <span style={styles.summaryText}>
            ({stats.battery} low battery, {stats.offline} offline)
          </span>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="alert-toggle-btn"
          title={isExpanded ? "Collapse details" : "Expand details"}
        >
          {isExpanded ? "Collapse ▲" : "Expand Details ▼"}
        </button>
      </div>

      {/* Expanded detailed scrollable list (Compiles with Task 3 rules) */}
      {isExpanded && (
        <div style={styles.detailsArea}>
          <div style={styles.searchBarContainer}>
            <input
              type="text"
              placeholder="🔍 Search drone ID or alert message..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="alert-search-input"
            />
          </div>

          <div style={styles.scrollableList}>
            {filteredAlerts.length === 0 ? (
              <div style={styles.noMatch}>No matching alerts found</div>
            ) : (
              filteredAlerts.map((alert) => {
                const isOffline = alert.type === "offline";
                const alertRowStyle = isOffline ? styles.alertOffline : styles.alertBattery;
                const icon = isOffline ? "📡" : "⚠️";

                return (
                  <div key={alert.id} className="alert-row-item" style={alertRowStyle}>
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
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    background: "rgba(220, 53, 69, 0.06)", // Delicate soft glassmorphism red
    border: "1px solid rgba(220, 53, 69, 0.2)",
    borderRadius: "12px",
    marginBottom: "20px",
    overflow: "hidden",
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
    boxShadow: "0 4px 15px rgba(0, 0, 0, 0.05)",
    transition: "all 0.3s ease",
    width: "100%",
  },
  healthyContainer: {
    background: "rgba(40, 167, 69, 0.06)", // Delicate soft glassmorphism green
    border: "1px solid rgba(40, 167, 69, 0.2)",
    borderRadius: "12px",
    marginBottom: "20px",
    overflow: "hidden",
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
    boxShadow: "0 4px 15px rgba(0, 0, 0, 0.05)",
    transition: "all 0.3s ease",
    width: "100%",
  },
  summaryHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 18px",
  },
  summaryLeft: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  alertCountBadge: {
    background: "#d32f2f",
    color: "#ffffff",
    padding: "3px 10px",
    borderRadius: "20px",
    fontSize: "12px",
    fontWeight: "600",
    letterSpacing: "0.3px",
  },
  healthyBadge: {
    background: "#28a745",
    color: "#ffffff",
    padding: "3px 10px",
    borderRadius: "20px",
    fontSize: "12px",
    fontWeight: "600",
    letterSpacing: "0.3px",
  },
  summaryText: {
    fontSize: "13px",
    color: "#5f6368",
    fontWeight: "500",
  },
  detailsArea: {
    borderTop: "1px solid rgba(220, 53, 69, 0.15)",
    padding: "14px 18px",
    background: "rgba(255, 255, 255, 0.65)",
    backdropFilter: "blur(10px)",
  },
  searchBarContainer: {
    marginBottom: "12px",
  },
  scrollableList: {
    maxHeight: "220px", // Defensive scroll boundary for 100+ items
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    paddingRight: "4px", // Padding to prevent scrollbar overlap
  },
  alertBattery: {
    background: "rgba(220, 53, 69, 0.08)", // Red glassmorphism
    color: "#b71c1c",
    borderColor: "rgba(220, 53, 69, 0.15)",
  },
  alertOffline: {
    background: "rgba(255, 152, 0, 0.08)", // Orange glassmorphism
    color: "#e65100",
    borderColor: "rgba(255, 152, 0, 0.15)",
  },
  icon: {
    marginRight: "10px",
    fontSize: "14px",
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
    fontSize: "18px",
    cursor: "pointer",
    padding: "0 4px",
    lineHeight: "1",
    opacity: "0.6",
    transition: "opacity 0.2s ease",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginLeft: "10px",
  },
  noMatch: {
    textAlign: "center",
    color: "#70757a",
    fontSize: "13px",
    padding: "16px 0",
    fontStyle: "italic",
  },
};

