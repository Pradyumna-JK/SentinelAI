import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AlertSeverity, AlertSource


class Alert(BaseModel):
    id: uuid.UUID = Field(..., description="Unique identifier of the alert")
    zone_id: uuid.UUID = Field(..., description="Identifier of the zone the alert was raised in")
    zone_name: str = Field(..., description="Name of the zone the alert was raised in")
    source: AlertSource = Field(..., description="Which subsystem raised this alert")
    severity: AlertSeverity = Field(..., description="Severity level of the alert")
    message: str = Field(..., description="Human-readable alert description")
    acknowledged: bool = Field(..., description="Whether the alert has been acknowledged")
    acknowledged_by: uuid.UUID | None = Field(None, description="User id who acknowledged the alert, if any")
    acknowledged_at: datetime | None = Field(None, description="Timestamp the alert was acknowledged, if any")
    created_at: datetime = Field(..., description="Timestamp the alert was created")


class AlertListResponse(BaseModel):
    total: int = Field(..., ge=0)
    unacknowledged_count: int = Field(..., ge=0)
    items: list[Alert]

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 2,
                "unacknowledged_count": 1,
                "items": [
                    {
                        "id": "b3f2a1e0-0000-4000-8000-000000000001",
                        "zone_id": "b3f2a1e0-0000-4000-8000-000000000000",
                        "zone_name": "Loading Dock A",
                        "source": "risk",
                        "severity": "Critical",
                        "message": "PPE violation detected correlated with elevated gas reading",
                        "acknowledged": False,
                        "acknowledged_by": None,
                        "acknowledged_at": None,
                        "created_at": "2026-07-20T10:15:05Z",
                    }
                ],
            }
        }
    }


class AlertCreateRequest(BaseModel):
    zone_id: uuid.UUID = Field(..., description="Zone the alert applies to")
    severity: AlertSeverity = Field(..., description="Severity level of the alert")
    message: str = Field(..., min_length=1, max_length=2000, description="Human-readable alert description")
    source: AlertSource = Field(AlertSource.MANUAL, description="Which subsystem raised this alert")
