import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EmergencyProtocolRead(BaseModel):
    id: uuid.UUID
    hazard_type: str
    steps: list[str]
    evacuation_route: str | None
    created_at: datetime


class EmergencyProtocolListResponse(BaseModel):
    items: list[EmergencyProtocolRead]


class EmergencyProtocolCreateRequest(BaseModel):
    hazard_type: str = Field(
        ..., min_length=1, max_length=50, description="Matched against a RiskEvent's hazard_class; use 'general' for the fallback protocol"
    )
    steps: list[str] = Field(..., min_length=1)
    evacuation_route: str | None = Field(None, max_length=300)


class EmergencyTriggerRequest(BaseModel):
    zone_id: uuid.UUID


class EmergencyTriggerResponse(BaseModel):
    triggered: bool
    incident_id: uuid.UUID | None
    message: str
