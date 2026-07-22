"""Site-configured emergency protocols, matched by hazard type — the
never-implemented Emergency Response Agent spec in
docs/11_AI_ARCHITECTURE.md §5. Org-wide (no per-zone assignment): matching
is purely by `hazard_type` string (exact match against a RiskEvent's
`hazard_class`, or the sentinel value "general" as the fallback protocol),
kept this lean since a zone-specific protocol table isn't needed for the
matching logic the problem statement actually asks for.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tenancy import TenantScoped
from app.models.base import Base


class EmergencyProtocol(Base, TenantScoped):
    __tablename__ = "emergency_protocols"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hazard_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    steps: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    evacuation_route: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
