"""IoT/SCADA sensor devices and their readings.

This is the signal the problem statement's whole framing turns on: gas
pressure sensors that existed but weren't correlated with anything at the
Vizag coke oven battery. `SensorReading.is_anomaly` is a plain baseline
threshold check computed at write time (matching the never-implemented
Sensor Intelligence Agent spec in docs/11_AI_ARCHITECTURE.md §2) — the
Compound Risk Intelligence Engine (app/ai/compound_risk) is what actually
correlates an anomaly with permits/maintenance/shift activity; this model
only owns "is this single reading out of range."
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tenancy import TenantScoped
from app.models.base import Base, str_enum
from app.models.enums import SensorType


class SensorDevice(Base, TenantScoped):
    __tablename__ = "sensor_devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sensor_type: Mapped[SensorType] = mapped_column(str_enum(SensorType, 20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    baseline_min: Mapped[float] = mapped_column(nullable=False)
    baseline_max: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SensorReading(Base, TenantScoped):
    __tablename__ = "sensor_readings"
    __table_args__ = (Index("ix_sensor_readings_sensor_recorded_at", "sensor_id", "recorded_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sensor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sensor_devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[float] = mapped_column(nullable=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
