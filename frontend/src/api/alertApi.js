const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function dismissAlert(alertId) {
  const response = await fetch(`${API_URL}/alerts/${alertId}/dismiss`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Failed to dismiss alert: ${response.status}`);
  }

  return response.json();
}
