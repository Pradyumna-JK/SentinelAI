"""Risk Intelligence Engine persistence: hazard events and computed
risk-score snapshots.

Two tables, two different grains, both TenantScoped (tenant-isolated the
same way as every other business table — see app/core/tenancy.py):

- RiskEvent: one row per interpreted hazard (app/ai/risk/catalog.py turning
  raw vision detections into "fire" or "ppe_violation_helmet"). The finest
  grain — this is the raw material risk computation reads.
- RiskScoreSnapshot: one row per (zone, computation run) — the engine's
  OUTPUT, persisted every time app/ai/risk/scheduler.py or an on-demand API
  call recomputes a zone's risk. This is what makes "historical analysis"
  and "rolling averages" genuinely queryable as a time series instead of
  requiring every raw event ever ingested to be re-aggregated on each read.

`level`/`severity`/`trend` use `native_enum=False` (a plain VARCHAR, not a
real Postgres CREATE TYPE enum) — adding a new risk level or trend value
later is a normal migration, not an ALTER TYPE ADD VALUE, which can't run
inside a transaction in older Postgres and is generally more operationally
awkward than it's worth for a 3-4 value scale.

`values_callable` matters here and isn't decorative — see app/models/base.py's
`str_enum` docstring for why plain `SAEnum(...)` silently breaks on read.
Found live, the first time the background scheduler tried to read the
demo-seeded history.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tenancy import TenantScoped
from app.models.base import Base, str_enum
from app.models.enums import RiskLevel, Trend


class RiskEvent(Base, TenantScoped):
    __tablename__ = "risk_events"
    __table_args__ = (Index("ix_risk_events_zone_detected_at", "zone_id", "detected_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    camera_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    hazard_class: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(nullable=False)
    severity: Mapped[float] = mapped_column(nullable=False)

    # Normalized 0..1 (fraction of frame width/height) — comparable across
    # cameras with different resolutions. Nullable: a future non-vision
    # hazard source (e.g. a gas sensor) wouldn't have a bounding box at all.
    bbox_x1: Mapped[float | None] = mapped_column(nullable=True)
    bbox_y1: Mapped[float | None] = mapped_column(nullable=True)
    bbox_x2: Mapped[float | None] = mapped_column(nullable=True)
    bbox_y2: Mapped[float | None] = mapped_column(nullable=True)

    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskScoreSnapshot(Base, TenantScoped):
    __tablename__ = "risk_score_snapshots"
    __table_args__ = (Index("ix_risk_score_snapshots_zone_computed_at", "zone_id", "computed_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True
    )

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    raw_score: Mapped[float] = mapped_column(nullable=False)
    score: Mapped[float] = mapped_column(nullable=False)
    level: Mapped[RiskLevel] = mapped_column(str_enum(RiskLevel, 20), nullable=False)
    severity: Mapped[RiskLevel] = mapped_column(str_enum(RiskLevel, 20), nullable=False)
    dominant_hazard_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    predicted_score: Mapped[float | None] = mapped_column(nullable=True)
    trend: Mapped[Trend] = mapped_column(str_enum(Trend, 20), nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    contributing_event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
