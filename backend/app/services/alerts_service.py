"""Business logic for the Alerts module.

Currently returns static dummy data. Will be backed by the `alerts` table,
populated by the Compound Risk Engine, once implemented.
"""

from functools import lru_cache

from app.models.enums import AlertSeverity
from app.schemas.alerts import Alert, AlertListResponse
from app.utils.generators import utc_now


class AlertsService:
    """Provides severity-ranked alerts across monitored zones."""

    def __init__(self) -> None:
        self._alerts = [
            Alert(
                id="alert-001",
                zone_id="zone-001",
                zone_name="Loading Dock A",
                severity=AlertSeverity.CRITICAL,
                message="PPE violation detected correlated with elevated gas reading",
                acknowledged=False,
                acknowledged_by=None,
                created_at=utc_now(),
            ),
            Alert(
                id="alert-002",
                zone_id="zone-002",
                zone_name="Assembly Line 3",
                severity=AlertSeverity.MEDIUM,
                message="Unusual vibration pattern detected on conveyor motor",
                acknowledged=True,
                acknowledged_by="user-042",
                created_at=utc_now(),
            ),
            Alert(
                id="alert-003",
                zone_id="zone-001",
                zone_name="Loading Dock A",
                severity=AlertSeverity.LOW,
                message="Restricted zone intrusion - low confidence detection",
                acknowledged=False,
                acknowledged_by=None,
                created_at=utc_now(),
            ),
        ]

    def list_alerts(self) -> AlertListResponse:
        unacknowledged = sum(1 for alert in self._alerts if not alert.acknowledged)
        return AlertListResponse(
            total=len(self._alerts),
            unacknowledged_count=unacknowledged,
            items=self._alerts,
        )


@lru_cache
def get_alerts_service() -> AlertsService:
    return AlertsService()
