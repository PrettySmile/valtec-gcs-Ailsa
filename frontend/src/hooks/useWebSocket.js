import { useEffect, useRef } from "react";
import { useDispatch } from "react-redux";
import { upsertTelemetry } from "../store/droneSlice";

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";
const RECONNECT_DELAY_MS = 3000;

export function useWebSocket() {
  const dispatch = useDispatch();
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(`${WS_URL}/ws/telemetry`);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const frame = JSON.parse(event.data);
          dispatch(upsertTelemetry(frame));
        } catch {
          // malformed frame — ignore
        }
      };

      ws.onclose = () => {
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [dispatch]);
}
