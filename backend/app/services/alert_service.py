import logging
from datetime import datetime, timezone
from app.models.drone import TelemetryFrame
from app.models.alert import Alert

logger = logging.getLogger("app.alert_service")
logger.setLevel(logging.INFO)

if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class AlertService:
    # 告警臨界值設定
    BATTERY_LOW_THRESHOLD = 20
    OFFLINE_TIMEOUT_SECONDS = 5

    def __init__(self):
        self.active_alerts: dict[str, Alert] = {}
        self.dismissed_alerts: set[str] = set()
        self.offline_start_times: dict[str, datetime] = {}
        self.on_alerts_update = None

    async def process_frame(self, frame: TelemetryFrame):
        """處理單一 TelemetryFrame，評估所有告警規則"""
        # 規則清單：未來若有新告警規則，直接加進此列表即可，下方的調度迴圈完全不用改動
        rules = [
            self._evaluate_battery,
            self._evaluate_connection,
        ]

        any_rule_changed = False
        for rule_evaluator in rules:
            if rule_evaluator(frame):
                any_rule_changed = True

        # 全部規則檢查完畢後，進行一次性的廣播更新
        if any_rule_changed and self.on_alerts_update:
            await self.on_alerts_update({
                "cmd": "alerts",
                "data": [
                    alert.model_dump(mode="json")
                    for alert in self.get_active_alerts()
                ],
            })

    def _evaluate_battery(self, frame: TelemetryFrame) -> bool:
        """評估電量告警規則"""
        battery_alert_id = f"{frame.drone_id}-low_battery"

        # 觸發告警：電量低於臨界值
        if frame.battery < self.BATTERY_LOW_THRESHOLD:
            if (
                battery_alert_id not in self.active_alerts
                and battery_alert_id not in self.dismissed_alerts
            ):
                alert = Alert(
                    id=battery_alert_id,
                    drone_id=frame.drone_id,
                    type="low_battery",
                    message=f"無人機 {frame.drone_id} 電量過低 (<{self.BATTERY_LOW_THRESHOLD}%)",
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                self.active_alerts[battery_alert_id] = alert
                self._log_alert(
                    "新增告警",
                    battery_alert_id,
                    f"{frame.drone_id} 電量過低 (<{self.BATTERY_LOW_THRESHOLD}%)",
                )
                return True
        # 解除告警：電量恢復正常
        else:
            if self._resolve_alert(battery_alert_id):
                self._log_alert(
                    "自動解除",
                    battery_alert_id,
                    f"{frame.drone_id} 電量恢復 ({frame.battery}%)",
                )
                return True

        return False

    def _evaluate_connection(self, frame: TelemetryFrame) -> bool:
        """評估離線連線告警規則"""
        offline_alert_id = f"{frame.drone_id}-offline"

        # 觸發告警：狀態為 offline
        if frame.status == "offline":
            if frame.drone_id not in self.offline_start_times:
                self.offline_start_times[frame.drone_id] = frame.timestamp
            else:
                elapsed = (
                    frame.timestamp - self.offline_start_times[frame.drone_id]
                ).total_seconds()
                if elapsed > self.OFFLINE_TIMEOUT_SECONDS:
                    if (
                        offline_alert_id not in self.active_alerts
                        and offline_alert_id not in self.dismissed_alerts
                    ):
                        alert = Alert(
                            id=offline_alert_id,
                            drone_id=frame.drone_id,
                            type="offline",
                            message=f"無人機 {frame.drone_id} 離線已超過 {self.OFFLINE_TIMEOUT_SECONDS} 秒",
                            created_at=frame.timestamp.isoformat(),
                        )
                        self.active_alerts[offline_alert_id] = alert
                        self._log_alert(
                            "新增告警",
                            offline_alert_id,
                            f"{frame.drone_id} 離線已超過 {self.OFFLINE_TIMEOUT_SECONDS} 秒",
                        )
                        return True
        # 解除告警：連線恢復正常
        else:
            # 移除離線計時器
            self.offline_start_times.pop(frame.drone_id, None)
            # 移除告警狀態
            if self._resolve_alert(offline_alert_id):
                self._log_alert(
                    "自動解除", offline_alert_id, f"{frame.drone_id} 恢復連線"
                )
                return True

        return False

    def _resolve_alert(self, alert_id: str) -> bool:
        """嘗試解除指定的警報。如果確實有警報被移除，回傳 True；否則回傳 False"""
        has_changed = False

        # 1. 如果警報在「活動中警報」裡，將其移除
        if alert_id in self.active_alerts:
            self.active_alerts.pop(alert_id)
            has_changed = True

        # 2. 如果警報在「已手動消除的歷史」裡，也將其移除（如此一來下次異常時才能再次觸發）
        if alert_id in self.dismissed_alerts:
            self.dismissed_alerts.remove(alert_id)
            has_changed = True

        return has_changed

    def _log_alert(self, action_type: str, alert_id: str, message: str):
        """統一的警報 Log 格式化工具"""
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(
            f"[ALERT LOG] {timestamp_str} | 廣播：[{action_type}] id={alert_id} | {message}"
        )

    async def dismiss_alert(self, alert_id: str):
        """手動消除告警"""
        if alert_id in self.active_alerts:
            self.active_alerts.pop(alert_id)
            self.dismissed_alerts.add(alert_id)
            self._log_alert("手動消除", alert_id, "操作員消除告警")
            if self.on_alerts_update:
                await self.on_alerts_update({
                    "cmd": "alerts",
                    "data": [
                        alert.model_dump(mode="json")
                        for alert in self.get_active_alerts()
                    ],
                })

    def get_active_alerts(self) -> list[Alert]:
        return list(self.active_alerts.values())


alert_service = AlertService()
