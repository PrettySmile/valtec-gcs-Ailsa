const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function sendCommand(droneId, commandType, payload = {}) {
  const response = await fetch(`${API_URL}/drones/${droneId}/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type: commandType, payload }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `HTTP ${response.status}`);
  }

  return response.json();
}
