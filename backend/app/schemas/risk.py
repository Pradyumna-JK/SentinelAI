import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import RiskLevel, Trend


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


class ZoneRiskRead(BaseModel):
    """Full output of the Risk Intelligence Engine for one zone — the rich
    shape; GET /risk (above) intentionally stays a smaller, stable shape
    for existing consumers."""

    zone_id: uuid.UUID
    zone_name: str
    raw_score: float = Field(..., description="This instant's aggregated score, before rolling-average smoothing")
    score: float = Field(..., ge=0, le=100, description="Rolling-average-smoothed score — the official one")
    level: RiskLevel = Field(..., description="Banded level of the smoothed score")
    severity: RiskLevel = Field(..., description="Banded severity of the single worst currently-live hazard")
    dominant_hazard_class: str | None = Field(None, description="Hazard class with the largest contribution")
    predicted_score: float | None = Field(None, description="Forecast score at the configured prediction horizon")
    trend: Trend
    recommended_action: str
    contributing_event_count: int = Field(..., ge=0)
    computed_at: datetime


class ZoneHistoryPoint(BaseModel):
    computed_at: datetime
    score: float
    level: RiskLevel
    trend: Trend


class ZoneHistoryResponse(BaseModel):
    zone_id: uuid.UUID
    points: list[ZoneHistoryPoint]


class TemporalHeatmapBucket(BaseModel):
    hour: int = Field(..., ge=0, le=23, description="Hour of day, 0-23, UTC")
    avg_score: float
    sample_count: int


class TemporalHeatmapResponse(BaseModel):
    zone_id: uuid.UUID
    buckets: list[TemporalHeatmapBucket]


class SpatialHeatmapCell(BaseModel):
    row: int
    col: int
    event_count: int
    avg_severity: float
    dominant_hazard_class: str


class SpatialHeatmapResponse(BaseModel):
    zone_id: uuid.UUID
    grid_size: int
    cells: list[SpatialHeatmapCell]


class FactoryRiskResponse(BaseModel):
    factory_id: uuid.UUID
    factory_name: str
    average_score: float
    highest_risk_zone: str | None
    zone_count: int
    zones: list[ZoneRiskRead]


class OrganizationRiskResponse(BaseModel):
    organization_id: uuid.UUID
    average_score: float
    highest_risk_zone: str | None
    highest_risk_factory: str | None
    zone_count: int
    factory_averages: dict[str, float]
    zones: list[ZoneRiskRead]


class DetectionIn(BaseModel):
    """One detection to ingest — pixel-space box; the server normalizes
    using the frame dimensions on RiskIngestRequest."""

    class_name: str = Field(..., examples=["person", "helmet", "fire", "smoke"])
    confidence: float = Field(..., ge=0, le=1)
    x1: float
    y1: float
    x2: float
    y2: float


class RiskIngestRequest(BaseModel):
    zone_id: uuid.UUID
    camera_id: str = Field(..., min_length=1, max_length=100)
    frame_width: float = Field(..., gt=0)
    frame_height: float = Field(..., gt=0)
    detections: list[DetectionIn]
    source_id: str | None = Field(None, description="Vision-engine source_id, for traceability")
    detected_at: datetime | None = Field(None, description="Defaults to now if omitted")


class IngestedHazard(BaseModel):
    hazard_class: str
    confidence: float
    severity: float


class RiskIngestResponse(BaseModel):
    hazard_events_created: int
    hazards: list[IngestedHazard]
