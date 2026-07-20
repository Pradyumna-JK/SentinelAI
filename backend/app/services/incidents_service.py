"""Business logic for the Incidents module.

Currently returns static dummy data. Will be backed by the Incident Report
Generator's persisted reports once implemented.
"""

from functools import lru_cache

from app.models.enums import AlertSeverity, IncidentStatus
from app.schemas.incidents import Incident, IncidentListResponse
from app.utils.generators import utc_now


class IncidentsService:
    """Provides structured incident reports across monitored zones."""

    def __init__(self) -> None:
        self._incidents = [
            Incident(
                id="incident-001",
                title="PPE Violation - Loading Dock A",
                zone_id="zone-001",
                zone_name="Loading Dock A",
                category="ppe_violation",
                severity=AlertSeverity.HIGH,
                status=IncidentStatus.DRAFT,
                summary="Worker detected without hard hat near active forklift zone at 10:15 UTC.",
                created_at=utc_now(),
                approved_by=None,
            ),
            Incident(
                id="incident-002",
                title="Vibration Anomaly - Assembly Line 3",
                zone_id="zone-002",
                zone_name="Assembly Line 3",
                category="equipment_anomaly",
                severity=AlertSeverity.MEDIUM,
                status=IncidentStatus.APPROVED,
                summary="Conveyor motor vibration exceeded baseline for 12 consecutive minutes.",
                created_at=utc_now(),
                approved_by="user-017",
            ),
        ]

    def list_incidents(self) -> IncidentListResponse:
        draft_count = sum(1 for incident in self._incidents if incident.status == IncidentStatus.DRAFT)
        approved_count = sum(1 for incident in self._incidents if incident.status == IncidentStatus.APPROVED)
        return IncidentListResponse(
            total=len(self._incidents),
            draft_count=draft_count,
            approved_count=approved_count,
            items=self._incidents,
        )


@lru_cache
def get_incidents_service() -> IncidentsService:
    return IncidentsService()
