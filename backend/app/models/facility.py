"""Physical facility hierarchy: Factory -> Site -> Building -> Zone.

Every level carries the owning organization's id directly (denormalized),
in addition to its immediate parent FK. Two reasons:

1. Performance: filtering through Zone -> Building -> Site -> Factory ->
   Organization on every query would mean four extra joins just to answer
   "does this belong to my organization?" A direct, indexed
   `organization_id` column answers that with one predicate.
2. Security: this is the exact column app/core/tenancy.py's automatic ORM
   filter and the PostgreSQL Row-Level Security policies both key off (see
   alembic/versions/*_tenant_isolation_rls.py). Both defenses need a column
   directly on the table being queried — a filter that only exists
   transitively through a chain of joins is a filter that's easy to
   accidentally omit from one of those joins.

`code` is a short, stable, human-assigned identifier ("DOCK-A"), distinct
from the free-text `name` ("Loading Dock A") — unique scoped to the
immediate parent, not globally, so two different sites can each have their
own "BLDG-1" without colliding.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.tenancy import TenantScoped
from app.models.base import Base


class Factory(Base, TenantScoped):
    """A manufacturing facility owned by an organization — the top of the
    physical hierarchy. An organization can operate several."""

    __tablename__ = "factories"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_factories_org_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sites: Mapped[list["Site"]] = relationship(back_populates="factory", cascade="all, delete-orphan")


class Site(Base, TenantScoped):
    """A physical campus/address within a factory. A factory can span
    multiple sites — e.g. a manufacturing division with several plants."""

    __tablename__ = "sites"
    __table_args__ = (UniqueConstraint("factory_id", "code", name="uq_sites_factory_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    factory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    factory: Mapped["Factory"] = relationship(back_populates="sites")
    buildings: Mapped[list["Building"]] = relationship(back_populates="site", cascade="all, delete-orphan")


class Building(Base, TenantScoped):
    __tablename__ = "buildings"
    __table_args__ = (UniqueConstraint("site_id", "code", name="uq_buildings_site_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    floor_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Abstract 2D floorplan grid dimensions (arbitrary units, not real-world
    # scale) — an indoor plant has no lat/long, so the geospatial heatmap
    # (Phase 4) positions Zones/Equipment/Cameras as rectangles within this
    # grid instead of on a real map.
    floor_width: Mapped[float | None] = mapped_column(nullable=True)
    floor_height: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    site: Mapped["Site"] = relationship(back_populates="buildings")
    zones: Mapped[list["Zone"]] = relationship(back_populates="building", cascade="all, delete-orphan")


class Zone(Base, TenantScoped):
    """The finest-grained unit — matches the "zone" concept already used by
    the dashboard/alerts/risk/incidents modules (e.g. "Loading Dock A")."""

    __tablename__ = "zones"
    __table_args__ = (UniqueConstraint("building_id", "code", name="uq_zones_building_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    zone_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # This zone's rectangle within its Building's floor_width x floor_height
    # grid — see Building.floor_width's docstring.
    layout_x: Mapped[float | None] = mapped_column(nullable=True)
    layout_y: Mapped[float | None] = mapped_column(nullable=True)
    layout_width: Mapped[float | None] = mapped_column(nullable=True)
    layout_height: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    building: Mapped["Building"] = relationship(back_populates="zones")
