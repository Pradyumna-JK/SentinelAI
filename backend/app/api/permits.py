import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.core.permissions import PERMITS_READ, PERMITS_WRITE
from app.db.session import get_db
from app.models.facility import Zone
from app.schemas.auth import AuthenticatedUser
from app.schemas.permits import WorkPermitCreateRequest, WorkPermitListResponse, WorkPermitRead
from app.services.permits_service import NotFoundError, PermitsService, get_permits_service

router = APIRouter(prefix="/permits", tags=["Permits"])


def _to_read(permit, zone_name: str) -> WorkPermitRead:
    return WorkPermitRead(
        id=permit.id,
        zone_id=permit.zone_id,
        zone_name=zone_name,
        permit_type=permit.permit_type,
        status=permit.status,
        description=permit.description,
        issued_by=permit.issued_by,
        valid_from=permit.valid_from,
        valid_to=permit.valid_to,
        created_at=permit.created_at,
    )


@router.get(
    "",
    response_model=WorkPermitListResponse,
    summary="List work permits",
    description="Requires the 'permits:read' permission.",
)
async def list_permits(
    _current_user: AuthenticatedUser = Depends(require_permission(PERMITS_READ)),
    service: PermitsService = Depends(get_permits_service),
) -> WorkPermitListResponse:
    rows = await service.list_permits()
    return WorkPermitListResponse(items=[_to_read(p, zone_name) for p, zone_name in rows])


@router.post(
    "",
    response_model=WorkPermitRead,
    status_code=status.HTTP_201_CREATED,
    summary="Issue a work permit",
    description=(
        "Created with status='active' immediately (no separate request/approval "
        "step for this demo). Requires the 'permits:write' permission."
    ),
)
async def create_permit(
    request: WorkPermitCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission(PERMITS_WRITE)),
    service: PermitsService = Depends(get_permits_service),
    db: AsyncSession = Depends(get_db),
) -> WorkPermitRead:
    try:
        permit = await service.create(
            organization_id=current_user.organization_id,
            zone_id=request.zone_id,
            permit_type=request.permit_type,
            description=request.description,
            valid_from=request.valid_from,
            valid_to=request.valid_to,
            issued_by=current_user.id,
        )
    except NotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "zone_id does not exist")
    zone = await db.get(Zone, permit.zone_id)
    return _to_read(permit, zone.name)


@router.post(
    "/{permit_id}/close",
    response_model=WorkPermitRead,
    summary="Close a work permit",
    description="Requires the 'permits:write' permission.",
)
async def close_permit(
    permit_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(require_permission(PERMITS_WRITE)),
    service: PermitsService = Depends(get_permits_service),
    db: AsyncSession = Depends(get_db),
) -> WorkPermitRead:
    try:
        permit = await service.close(permit_id)
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Permit not found")
    zone = await db.get(Zone, permit.zone_id)
    return _to_read(permit, zone.name)
