import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.alert_service import alert_service
from app.models.alert import Alert


@pytest.mark.asyncio
async def test_dismiss_alert():
    alert_id = "drone-1-offline"
    alert = Alert(
        id=alert_id,
        drone_id="drone-1",
        type="offline",
        message="Drone drone-1 offline for 5s",
        created_at="2026-06-07T00:00:00Z",
    )
    alert_service.active_alerts[alert_id] = alert
    if alert_id in alert_service.dismissed_alerts:
        alert_service.dismissed_alerts.remove(alert_id)

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.post(f"/alerts/{alert_id}/dismiss")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert alert_id not in alert_service.active_alerts
    assert alert_id in alert_service.dismissed_alerts
