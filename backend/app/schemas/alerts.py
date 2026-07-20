from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AlertSeverity


class Alert(BaseModel):
    id: str = Field(..., description="Unique identifier of the alert")
    zone_id: str = Field(..., description="Identifier of the zone the alert was raised in")
    zone_name: str = Field(..., description="Name of the zone the alert was raised in")
    severity: AlertSeverity = Field(..., description="Severity level of the alert")
    message: str = Field(..., description="Human-readable alert description")
    acknowledged: bool = Field(..., description="Whether the alert has been acknowledged")
    acknowledged_by: str | None = Field(None, description="User id who acknowledged the alert, if any")
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
                        "id": "alert-001",
                        "zone_id": "zone-001",
                        "zone_name": "Loading Dock A",
                        "severity": "Critical",
                        "message": "PPE violation detected correlated with elevated gas reading",
                        "acknowledged": False,
                        "acknowledged_by": None,
                        "created_at": "2026-07-20T10:15:05Z",
                    }
                ],
            }
        }
    }
