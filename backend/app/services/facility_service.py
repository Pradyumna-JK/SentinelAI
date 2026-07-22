"""Facility hierarchy: Factory -> Site -> Building -> Zone.

Every one of these models mixes in `TenantScoped` (app/core/tenancy.py), so
every SELECT and `session.get()` below is automatically filtered to the
caller's organization by the ORM-level event listener — there is no
explicit `.where(organization_id == ...)` anywhere in this file, and that's
deliberate: demonstrating that removing the manual filter is exactly the
point of that mechanism. The one place `organization_id` has to be set
explicitly is on INSERT — there's nothing to filter on a row that doesn't
exist yet.

Validating a parent id (e.g. "does this factory_id actually belong to the
caller?") gets the same protection for free: `session.get(Factory, some_
other_orgs_id)` returns `None` — indistinguishable from "doesn't exist" —
because the loader criteria applies to `get()` too. That's why
`ParentNotFoundError` and `NotFoundError` are the same 404 either way: a
client that owns neither the parent nor a same-ID row in another
organization cannot tell those two cases apart, which is the correct,
non-leaking behavior.
"""

import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.facility import Building, Factory, Site, Zone


class NotFoundError(Exception):
    pass


class ParentNotFoundError(Exception):
    pass


class FactoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_factories(self) -> list[Factory]:
        result = await self._db.execute(select(Factory).order_by(Factory.name))
        return list(result.scalars())

    async def get_factory(self, factory_id: uuid.UUID) -> Factory:
        factory = await self._db.get(Factory, factory_id)
        if factory is None:
            raise NotFoundError()
        return factory

    async def create_factory(self, organization_id: uuid.UUID, name: str, code: str) -> Factory:
        factory = Factory(organization_id=organization_id, name=name, code=code)
        self._db.add(factory)
        await self._db.flush()
        return factory


class SiteService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_sites(self) -> list[Site]:
        result = await self._db.execute(select(Site).order_by(Site.name))
        return list(result.scalars())

    async def get_site(self, site_id: uuid.UUID) -> Site:
        site = await self._db.get(Site, site_id)
        if site is None:
            raise NotFoundError()
        return site

    async def create_site(
        self, organization_id: uuid.UUID, factory_id: uuid.UUID, name: str, code: str, address: str | None
    ) -> Site:
        if await self._db.get(Factory, factory_id) is None:
            raise ParentNotFoundError()
        site = Site(organization_id=organization_id, factory_id=factory_id, name=name, code=code, address=address)
        self._db.add(site)
        await self._db.flush()
        return site


class BuildingService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_buildings(self) -> list[Building]:
        result = await self._db.execute(select(Building).order_by(Building.name))
        return list(result.scalars())

    async def get_building(self, building_id: uuid.UUID) -> Building:
        building = await self._db.get(Building, building_id)
        if building is None:
            raise NotFoundError()
        return building

    async def create_building(
        self, organization_id: uuid.UUID, site_id: uuid.UUID, name: str, code: str, floor_count: int | None
    ) -> Building:
        if await self._db.get(Site, site_id) is None:
            raise ParentNotFoundError()
        building = Building(
            organization_id=organization_id, site_id=site_id, name=name, code=code, floor_count=floor_count
        )
        self._db.add(building)
        await self._db.flush()
        return building


class ZoneService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_zones(self) -> list[Zone]:
        result = await self._db.execute(select(Zone).order_by(Zone.name))
        return list(result.scalars())

    async def get_zone(self, zone_id: uuid.UUID) -> Zone:
        zone = await self._db.get(Zone, zone_id)
        if zone is None:
            raise NotFoundError()
        return zone

    async def create_zone(
        self, organization_id: uuid.UUID, building_id: uuid.UUID, name: str, code: str, zone_type: str | None
    ) -> Zone:
        if await self._db.get(Building, building_id) is None:
            raise ParentNotFoundError()
        zone = Zone(
            organization_id=organization_id, building_id=building_id, name=name, code=code, zone_type=zone_type
        )
        self._db.add(zone)
        await self._db.flush()
        return zone


def get_factory_service(db: AsyncSession = Depends(get_db)) -> FactoryService:
    return FactoryService(db)


def get_site_service(db: AsyncSession = Depends(get_db)) -> SiteService:
    return SiteService(db)


def get_building_service(db: AsyncSession = Depends(get_db)) -> BuildingService:
    return BuildingService(db)


def get_zone_service(db: AsyncSession = Depends(get_db)) -> ZoneService:
    return ZoneService(db)
