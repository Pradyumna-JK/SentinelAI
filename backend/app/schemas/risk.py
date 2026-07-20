from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import RiskLevel


class RiskScore(BaseModel):
    id: str = Field(..., description="Unique identifier of the risk score entry")
    zone_id: str = Field(..., description="Identifier of the zone this score applies to")
    zone_name: str = Field(..., description="Name of the zone this score applies to")
    score: float = Field(..., ge=0, le=100, description="Compound risk score (0-100)")
    level: RiskLevel = Field(..., description="Categorical risk level derived from the score")
    rationale: str = Field(..., description="Human-readable explanation of what drove this score")
    confidence: str = Field(..., description="Confidence qualifier for the score, e.g. 'full', 'partial'")
    created_at: datetime = Field(..., description="Timestamp the score was computed")


class RiskResponse(BaseModel):
    average_score: float = Field(..., ge=0, le=100)
    highest_risk_zone: str = Field(..., description="Name of the zone with the highest current score")
    scores: list[RiskScore]

    model_config = {
        "json_schema_extra": {
            "example": {
                "average_score": 58.3,
                "highest_risk_zone": "Loading Dock A",
                "scores": [
                    {
                        "id": "risk-001",
                        "zone_id": "zone-001",
                        "zone_name": "Loading Dock A",
                        "score": 82.0,
                        "level": "High",
                        "rationale": "Elevated due to PPE violation correlated with gas sensor reading 40% above baseline.",
                        "confidence": "full",
                        "created_at": "2026-07-20T10:15:04Z",
                    }
                ],
            }
        }
    }
