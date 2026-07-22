"""Facility hierarchy endpoints: /factories, /sites, /buildings, /zones.

Four small, structurally-identical routers grouped in one file (matching
how the models and service live in one file each) rather than four nearly-
empty ones. Every read is automatically tenant-scoped by app/core/tenancy.py
— these routers never pass an organization filter into a query themselves;
`current_user.organization_id` is used only where a value must be written
(creating a row), never to filter a read.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import require_permission
from app.core.permissions import (
    BUILDINGS_READ,
    BUILDINGS_WRITE,
    FACTORIES_READ,
    FACTORIES_WRITE,
    SITES_READ,
    SITES_WRITE,
    ZONES_READ,
    ZONES_WRITE,
)
from app.schemas.auth import AuthenticatedUser
from app.schemas.facility import (
    BuildingCreate,
    BuildingListResponse,
    BuildingRead,
    FactoryCreate,
    FactoryListResponse,
    FactoryRead,
    SiteCreate,
    SiteListResponse,
    SiteRead,
    ZoneCreate,
    ZoneListResponse,
    ZoneRead,
)
from app.services.facility_service import (
    BuildingService,
    FactoryService,
    NotFoundError,
    ParentNotFoundError,
    SiteService,
    ZoneService,
    get_building_service,
    get_factory_service,
    get_site_service,
    get_zone_service,
)

factories_router = APIRouter(prefix="/factories", tags=["Facilities"])
sites_router = APIRouter(prefix="/sites", tags=["Facilities"])
buildings_router = APIRouter(prefix="/buildings", tags=["Facilities"])
zones_router = APIRouter(prefix="/zones", tags=["Facilities"])


@factories_router.get("", response_model=FactoryListResponse, summary="List factories in your organization")
async def list_factories(
    _current_user: AuthenticatedUser = Depends(require_permission(FACTORIES_READ)),
    service: FactoryService = Depends(get_factory_service),
) -> FactoryListResponse:
    return FactoryListResponse(items=[FactoryRead.model_validate(f) for f in await service.list_factories()])


@factories_router.get("/{factory_id}", response_model=FactoryRead, summary="Get a factory")
async def get_factory(
    factory_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(require_permission(FACTORIES_READ)),
    service: FactoryService = Depends(get_factory_service),
) -> FactoryRead:
    try:
        return FactoryRead.model_validate(await service.get_factory(factory_id))
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Factory not found")


@factories_router.post(
    "", response_model=FactoryRead, status_code=status.HTTP_201_CREATED, summary="Create a factory"
)
async def create_factory(
    payload: FactoryCreate,
    current_user: AuthenticatedUser = Depends(require_permission(FACTORIES_WRITE)),
    service: FactoryService = Depends(get_factory_service),
) -> FactoryRead:
    factory = await service.create_factory(current_user.organization_id, payload.name, payload.code)
    return FactoryRead.model_validate(factory)


@sites_router.get("", response_model=SiteListResponse, summary="List sites in your organization")
async def list_sites(
    _current_user: AuthenticatedUser = Depends(require_permission(SITES_READ)),
    service: SiteService = Depends(get_site_service),
) -> SiteListResponse:
    return SiteListResponse(items=[SiteRead.model_validate(s) for s in await service.list_sites()])


@sites_router.get("/{site_id}", response_model=SiteRead, summary="Get a site")
async def get_site(
    site_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(require_permission(SITES_READ)),
    service: SiteService = Depends(get_site_service),
) -> SiteRead:
    try:
        return SiteRead.model_validate(await service.get_site(site_id))
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Site not found")


@sites_router.post("", response_model=SiteRead, status_code=status.HTTP_201_CREATED, summary="Create a site")
async def create_site(
    payload: SiteCreate,
    current_user: AuthenticatedUser = Depends(require_permission(SITES_WRITE)),
    service: SiteService = Depends(get_site_service),
) -> SiteRead:
    try:
        site = await service.create_site(
            current_user.organization_id, payload.factory_id, payload.name, payload.code, payload.address
        )
    except ParentNotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "factory_id does not exist")
    return SiteRead.model_validate(site)


@buildings_router.get("", response_model=BuildingListResponse, summary="List buildings in your organization")
async def list_buildings(
    _current_user: AuthenticatedUser = Depends(require_permission(BUILDINGS_READ)),
    service: BuildingService = Depends(get_building_service),
) -> BuildingListResponse:
    return BuildingListResponse(items=[BuildingRead.model_validate(b) for b in await service.list_buildings()])


@buildings_router.get("/{building_id}", response_model=BuildingRead, summary="Get a building")
async def get_building(
    building_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(require_permission(BUILDINGS_READ)),
    service: BuildingService = Depends(get_building_service),
) -> BuildingRead:
    try:
        return BuildingRead.model_validate(await service.get_building(building_id))
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Building not found")


@buildings_router.post(
    "", response_model=BuildingRead, status_code=status.HTTP_201_CREATED, summary="Create a building"
)
async def create_building(
    payload: BuildingCreate,
    current_user: AuthenticatedUser = Depends(require_permission(BUILDINGS_WRITE)),
    service: BuildingService = Depends(get_building_service),
) -> BuildingRead:
    try:
        building = await service.create_building(
            current_user.organization_id, payload.site_id, payload.name, payload.code, payload.floor_count
        )
    except ParentNotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "site_id does not exist")
    return BuildingRead.model_validate(building)


@zones_router.get("", response_model=ZoneListResponse, summary="List zones in your organization")
async def list_zones(
    _current_user: AuthenticatedUser = Depends(require_permission(ZONES_READ)),
    service: ZoneService = Depends(get_zone_service),
) -> ZoneListResponse:
    return ZoneListResponse(items=[ZoneRead.model_validate(z) for z in await service.list_zones()])


@zones_router.get("/{zone_id}", response_model=ZoneRead, summary="Get a zone")
async def get_zone(
    zone_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(require_permission(ZONES_READ)),
    service: ZoneService = Depends(get_zone_service),
) -> ZoneRead:
    try:
        return ZoneRead.model_validate(await service.get_zone(zone_id))
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")


@zones_router.post("", response_model=ZoneRead, status_code=status.HTTP_201_CREATED, summary="Create a zone")
async def create_zone(
    payload: ZoneCreate,
    current_user: AuthenticatedUser = Depends(require_permission(ZONES_WRITE)),
    service: ZoneService = Depends(get_zone_service),
) -> ZoneRead:
    try:
        zone = await service.create_zone(
            current_user.organization_id, payload.building_id, payload.name, payload.code, payload.zone_type
        )
    except ParentNotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "building_id does not exist")
    return ZoneRead.model_validate(zone)
