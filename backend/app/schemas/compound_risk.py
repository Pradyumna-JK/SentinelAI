import uuid

from pydantic import BaseModel, Field


class CompoundRiskExplanation(BaseModel):
    zone_id: uuid.UUID
    combined: bool = Field(..., description="Whether at least two independent signals coincided")
    severity: float = Field(..., ge=0, le=100)
    hazard_class: str
    dominant_signals: list[str] = Field(..., description="Which signals contributed, e.g. ['gas_anomaly', 'dangerous_permit']")
    rationale: str = Field(..., description="Human-readable explanation of why this finding fired")
