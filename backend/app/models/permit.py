"""Work permits — the second half of the problem statement's flagship
scenario: a hot-work or confined-space permit active in the same zone as
an elevated gas reading. The Compound Risk Intelligence Engine
(app/ai/compound_risk) reads active WorkPermits per zone to correlate
against sensor anomalies; this model only owns the permit lifecycle itself.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tenancy import TenantScoped
from app.models.base import Base, str_enum
from app.models.enums import PermitStatus, PermitType


class WorkPermit(Base, TenantScoped):
    __tablename__ = "work_permits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permit_type: Mapped[PermitType] = mapped_column(str_enum(PermitType, 30), nullable=False)
    status: Mapped[PermitStatus] = mapped_column(
        str_enum(PermitStatus, 20), nullable=False, default=PermitStatus.ACTIVE
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    issued_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
