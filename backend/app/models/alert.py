"""Alerts: the central notification sink every detection subsystem writes
into (vision, risk, and — from Phase 2/3/6 onward — the compound-risk
correlation engine, the permit intelligence agent, and the emergency
response orchestrator). One table, one `source` column, rather than a
separate alerts table per subsystem — a dashboard/UI needs one unified
feed to page through, not five.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tenancy import TenantScoped
from app.models.base import Base, str_enum
from app.models.enums import AlertSeverity, AlertSource


class Alert(Base, TenantScoped):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_zone_created_at", "zone_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[AlertSource] = mapped_column(str_enum(AlertSource, 20), nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(str_enum(AlertSeverity, 20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
