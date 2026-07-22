"""Incidents: structured, audit-ready reports with a draft -> approved ->
closed lifecycle. `detail` holds the evidence bundle a report was drafted
from (contributing risk events, sensor readings, matched emergency
protocol) — kept as JSONB rather than normalized tables since it's a
point-in-time snapshot for audit purposes, not data anything else queries
relationally. Phase 6's Emergency Response Orchestrator is the first real
writer of that field; until then it's populated by whoever creates the
incident (manually, via `POST /incidents`).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tenancy import TenantScoped
from app.models.base import Base, str_enum
from app.models.enums import AlertSeverity, IncidentStatus


class Incident(Base, TenantScoped):
    __tablename__ = "incidents"
    __table_args__ = (Index("ix_incidents_zone_created_at", "zone_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(str_enum(AlertSeverity, 20), nullable=False)
    status: Mapped[IncidentStatus] = mapped_column(
        str_enum(IncidentStatus, 20), nullable=False, default=IncidentStatus.DRAFT
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
