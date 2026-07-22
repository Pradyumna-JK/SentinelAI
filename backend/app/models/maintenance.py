"""Equipment and maintenance activity — the third correlated signal in the
Compound Risk Intelligence Engine's combination matrix (e.g. maintenance
work plus a shift changeover plus an active permit in the same zone).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tenancy import TenantScoped
from app.models.base import Base, str_enum
from app.models.enums import EquipmentCriticality, MaintenanceStatus


class Equipment(Base, TenantScoped):
    __tablename__ = "equipment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    equipment_type: Mapped[str] = mapped_column(String(100), nullable=False)
    criticality: Mapped[EquipmentCriticality] = mapped_column(
        str_enum(EquipmentCriticality, 20), nullable=False, default=EquipmentCriticality.MEDIUM
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MaintenanceRecord(Base, TenantScoped):
    __tablename__ = "maintenance_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[MaintenanceStatus] = mapped_column(
        str_enum(MaintenanceStatus, 20), nullable=False, default=MaintenanceStatus.SCHEDULED
    )
    technician: Mapped[str | None] = mapped_column(String(200), nullable=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
