from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AlertSeverity, IncidentStatus


class Incident(BaseModel):
    id: str = Field(..., description="Unique identifier of the incident report")
    title: str = Field(..., description="Short incident title")
    zone_id: str = Field(..., description="Identifier of the zone the incident occurred in")
    zone_name: str = Field(..., description="Name of the zone the incident occurred in")
    category: str = Field(..., description="Incident category, e.g. 'fire', 'ppe_violation'")
    severity: AlertSeverity = Field(..., description="Severity level of the incident")
    status: IncidentStatus = Field(..., description="Lifecycle status of the incident report")
    summary: str = Field(..., description="Auto-generated summary of the incident")
    created_at: datetime = Field(..., description="Timestamp the incident was created")
    approved_by: str | None = Field(None, description="User id who approved the report, if any")


class IncidentListResponse(BaseModel):
    total: int = Field(..., ge=0)
    draft_count: int = Field(..., ge=0)
    approved_count: int = Field(..., ge=0)
    items: list[Incident]

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 1,
                "draft_count": 1,
                "approved_count": 0,
                "items": [
                    {
                        "id": "incident-001",
                        "title": "PPE Violation - Loading Dock A",
                        "zone_id": "zone-001",
                        "zone_name": "Loading Dock A",
                        "category": "ppe_violation",
                        "severity": "High",
                        "status": "draft",
                        "summary": "Worker detected without hard hat near active forklift zone at 10:15 UTC.",
                        "created_at": "2026-07-20T10:15:06Z",
                        "approved_by": None,
                    }
                ],
            }
        }
    }
