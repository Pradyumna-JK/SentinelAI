import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AlertSeverity, IncidentStatus


class Incident(BaseModel):
    id: uuid.UUID = Field(..., description="Unique identifier of the incident report")
    title: str = Field(..., description="Short incident title")
    zone_id: uuid.UUID = Field(..., description="Identifier of the zone the incident occurred in")
    zone_name: str = Field(..., description="Name of the zone the incident occurred in")
    category: str = Field(..., description="Incident category, e.g. 'fire', 'ppe_violation'")
    severity: AlertSeverity = Field(..., description="Severity level of the incident")
    status: IncidentStatus = Field(..., description="Lifecycle status of the incident report")
    summary: str = Field(..., description="Summary of the incident")
    detail: dict = Field(default_factory=dict, description="Structured evidence bundle backing this report")
    created_at: datetime = Field(..., description="Timestamp the incident was created")
    approved_by: uuid.UUID | None = Field(None, description="User id who approved the report, if any")
    approved_at: datetime | None = Field(None, description="Timestamp the report was approved, if any")
    closed_at: datetime | None = Field(None, description="Timestamp the incident was closed, if any")


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
                        "id": "b3f2a1e0-0000-4000-8000-000000000002",
                        "title": "PPE Violation - Loading Dock A",
                        "zone_id": "b3f2a1e0-0000-4000-8000-000000000000",
                        "zone_name": "Loading Dock A",
                        "category": "ppe_violation",
                        "severity": "High",
                        "status": "draft",
                        "summary": "Worker detected without hard hat near active forklift zone at 10:15 UTC.",
                        "detail": {},
                        "created_at": "2026-07-20T10:15:06Z",
                        "approved_by": None,
                        "approved_at": None,
                        "closed_at": None,
                    }
                ],
            }
        }
    }


class IncidentCreateRequest(BaseModel):
    zone_id: uuid.UUID = Field(..., description="Zone the incident occurred in")
    title: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=50)
    severity: AlertSeverity = Field(...)
    summary: str = Field(..., min_length=1)
    detail: dict = Field(default_factory=dict)
