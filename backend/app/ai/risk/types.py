"""Structured types for the Risk Intelligence Engine.

Plain dataclasses, mirroring app/ai/vision/types.py's separation: this
layer has no ORM/HTTP concerns. Services convert to/from these at the
DB and API boundaries.

`RiskLevel` and `Trend` are imported from app.models.enums rather than
redefined here — both are plain value types (`str, Enum`, no ORM/
DeclarativeBase machinery), and app.models.enums is the single foundational
source of truth every layer depends on, never the reverse: app/models/risk.py
(the ORM layer) stores these same two enums as columns, so defining them
here instead would make the persistence layer depend on the intelligence
layer, backwards from every other dependency in this codebase. `RiskLevel`
is used for both `level` (the aggregated, decayed, smoothed score) and
`severity` (the single worst active hazard) — see scoring.py's module
docstring for why those two legitimately diverge.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.models.enums import RiskLevel, Trend

__all__ = [
    "RiskLevel",
    "Trend",
    "NormalizedBBox",
    "RawDetection",
    "HazardEvent",
    "ScoredEvent",
    "RiskComputation",
]


@dataclass(frozen=True)
class NormalizedBBox:
    """Detection box as a 0..1 fraction of frame width/height — makes
    spatial aggregation (heatmaps) comparable across cameras with
    different resolutions."""

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def center(self) -> tuple[float, float]:
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2


@dataclass(frozen=True)
class RawDetection:
    """One vision-engine Detection, as handed to the risk engine's
    ingestion layer — decoupled from app.ai.vision.types.Detection so this
    package has no import-time dependency on the vision engine."""

    class_name: str
    confidence: float
    bbox: NormalizedBBox


@dataclass(frozen=True)
class HazardEvent:
    """A business-meaningful hazard, interpreted from raw detections by
    app/ai/risk/catalog.py — e.g. "person without a helmet", not just
    "helmet detected". This is the unit RiskEvent rows persist."""

    hazard_class: str          # "fire" | "smoke" | "ppe_violation_helmet" | ...
    confidence: float
    severity: float             # 0..100, snapshotted from the catalog at ingestion time
    bbox: NormalizedBBox | None


@dataclass(frozen=True)
class ScoredEvent:
    """A persisted RiskEvent plus its decay-weighted contribution, as used
    internally by scoring.py — not persisted itself."""

    hazard_class: str
    severity: float
    confidence: float
    detected_at: datetime
    contribution: float        # severity * confidence * decay(age)


@dataclass
class RiskComputation:
    """Everything compute_zone_risk() produces for one zone at one instant."""

    zone_id: str
    zone_name: str
    raw_score: float                       # this instant's aggregated score, pre-smoothing
    score: float                           # rolling-average-smoothed score (the "official" one)
    level: RiskLevel
    severity: RiskLevel
    dominant_hazard_class: str | None
    predicted_score: float | None          # forecast `prediction_horizon_minutes` ahead
    trend: Trend
    recommended_action: str
    contributing_event_count: int
    computed_at: datetime
    history_used: int = field(default=0)   # how many prior snapshots fed the rolling average
