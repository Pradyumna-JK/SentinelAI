"""Cameras: registered CCTV stream metadata, real FK'd to a zone.

`layout_x`/`layout_y` place the camera within its zone's floorplan
rectangle (see the `Zone` spatial columns added alongside this migration
in app/models/facility.py) — added now rather than deferred to Phase 4 so
the geospatial heatmap doesn't need a second migration touching this table.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tenancy import TenantScoped
from app.models.base import Base, str_enum
from app.models.enums import CameraStatus


class Camera(Base, TenantScoped):
    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stream_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[CameraStatus] = mapped_column(
        str_enum(CameraStatus, 20), nullable=False, default=CameraStatus.ACTIVE
    )
    resolution: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    layout_x: Mapped[float | None] = mapped_column(nullable=True)
    layout_y: Mapped[float | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
