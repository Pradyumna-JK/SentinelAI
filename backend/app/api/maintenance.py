import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.core.permissions import MAINTENANCE_READ, MAINTENANCE_WRITE
from app.db.session import get_db
from app.models.facility import Zone
from app.models.maintenance import Equipment
from app.schemas.auth import AuthenticatedUser
from app.schemas.maintenance import (
    EquipmentCreateRequest,
    EquipmentListResponse,
    EquipmentRead,
    MaintenanceRecordCreateRequest,
    MaintenanceRecordListResponse,
    MaintenanceRecordRead,
)
from app.services.maintenance_service import MaintenanceService, NotFoundError, get_maintenance_service

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


def _to_record_read(record, equipment_name: str, zone_id: uuid.UUID) -> MaintenanceRecordRead:
    return MaintenanceRecordRead(
        id=record.id, equipment_id=record.equipment_id, equipment_name=equipment_name, zone_id=zone_id,
        status=record.status, technician=record.technician, window_start=record.window_start,
        window_end=record.window_end, created_at=record.created_at,
    )


@router.get(
    "/equipment",
    response_model=EquipmentListResponse,
    summary="List registered equipment",
    description="Requires the 'maintenance:read' permission.",
)
async def list_equipment(
    _current_user: AuthenticatedUser = Depends(require_permission(MAINTENANCE_READ)),
    service: MaintenanceService = Depends(get_maintenance_service),
) -> EquipmentListResponse:
    rows = await service.list_equipment()
    return EquipmentListResponse(
        items=[
            EquipmentRead(
                id=e.id, zone_id=e.zone_id, zone_name=zone_name, name=e.name,
                equipment_type=e.equipment_type, criticality=e.criticality, created_at=e.created_at,
            )
            for e, zone_name in rows
        ]
    )


@router.post(
    "/equipment",
    response_model=EquipmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register equipment",
    description="Requires the 'maintenance:write' permission.",
)
async def create_equipment(
    request: EquipmentCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission(MAINTENANCE_WRITE)),
    service: MaintenanceService = Depends(get_maintenance_service),
    db: AsyncSession = Depends(get_db),
) -> EquipmentRead:
    try:
        equipment = await service.create_equipment(
            organization_id=current_user.organization_id, zone_id=request.zone_id,
            name=request.name, equipment_type=request.equipment_type, criticality=request.criticality,
        )
    except NotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "zone_id does not exist")
    zone = await db.get(Zone, equipment.zone_id)
    return EquipmentRead(
        id=equipment.id, zone_id=equipment.zone_id, zone_name=zone.name, name=equipment.name,
        equipment_type=equipment.equipment_type, criticality=equipment.criticality,
        created_at=equipment.created_at,
    )


@router.get(
    "/records",
    response_model=MaintenanceRecordListResponse,
    summary="List maintenance records",
    description="Requires the 'maintenance:read' permission.",
)
async def list_records(
    _current_user: AuthenticatedUser = Depends(require_permission(MAINTENANCE_READ)),
    service: MaintenanceService = Depends(get_maintenance_service),
) -> MaintenanceRecordListResponse:
    rows = await service.list_records()
    return MaintenanceRecordListResponse(
        items=[_to_record_read(r, equipment_name, zone_id) for r, equipment_name, zone_id in rows]
    )


@router.post(
    "/records",
    response_model=MaintenanceRecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Log a maintenance activity window",
    description="Requires the 'maintenance:write' permission.",
)
async def create_record(
    request: MaintenanceRecordCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission(MAINTENANCE_WRITE)),
    service: MaintenanceService = Depends(get_maintenance_service),
    db: AsyncSession = Depends(get_db),
) -> MaintenanceRecordRead:
    try:
        record = await service.create_record(
            organization_id=current_user.organization_id, equipment_id=request.equipment_id,
            technician=request.technician, window_start=request.window_start, window_end=request.window_end,
        )
    except NotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "equipment_id does not exist")
    equipment = await db.get(Equipment, record.equipment_id)
    return _to_record_read(record, equipment.name, equipment.zone_id)


@router.post(
    "/records/{record_id}/complete",
    response_model=MaintenanceRecordRead,
    summary="Mark a maintenance record complete",
    description="Requires the 'maintenance:write' permission.",
)
async def complete_record(
    record_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(require_permission(MAINTENANCE_WRITE)),
    service: MaintenanceService = Depends(get_maintenance_service),
    db: AsyncSession = Depends(get_db),
) -> MaintenanceRecordRead:
    try:
        record = await service.complete_record(record_id)
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Maintenance record not found")
    equipment = await db.get(Equipment, record.equipment_id)
    return _to_record_read(record, equipment.name, equipment.zone_id)
