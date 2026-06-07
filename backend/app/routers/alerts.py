from fastapi import APIRouter
from app.services.alert_service import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/{alert_id}/dismiss")
async def dismiss_alert(alert_id: str):
    await alert_service.dismiss_alert(alert_id)
    return {"status": "success", "message": f"Alert {alert_id} dismissed"}
