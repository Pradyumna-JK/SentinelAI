from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.core.permissions import SHIFTS_READ, SHIFTS_WRITE
from app.db.session import get_db
from app.models.shift import Shift
from app.schemas.auth import AuthenticatedUser
from app.schemas.shifts import (
    ShiftChangeoverEventCreateRequest,
    ShiftChangeoverEventListResponse,
    ShiftChangeoverEventRead,
    ShiftCreateRequest,
    ShiftListResponse,
    ShiftRead,
)
from app.services.shifts_service import NotFoundError, ShiftsService, get_shifts_service

router = APIRouter(prefix="/shifts", tags=["Shifts"])


@router.get("", response_model=ShiftListResponse, summary="List shift templates")
async def list_shifts(
    _current_user: AuthenticatedUser = Depends(require_permission(SHIFTS_READ)),
    service: ShiftsService = Depends(get_shifts_service),
) -> ShiftListResponse:
    shifts = await service.list_shifts()
    return ShiftListResponse(
        items=[
            ShiftRead(
                id=s.id, factory_id=s.factory_id, name=s.name,
                start_time=s.start_time, end_time=s.end_time, created_at=s.created_at,
            )
            for s in shifts
        ]
    )


@router.post(
    "", response_model=ShiftRead, status_code=status.HTTP_201_CREATED,
    summary="Define a shift", description="Requires the 'shifts:write' permission.",
)
async def create_shift(
    request: ShiftCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission(SHIFTS_WRITE)),
    service: ShiftsService = Depends(get_shifts_service),
) -> ShiftRead:
    try:
        shift = await service.create_shift(
            organization_id=current_user.organization_id, factory_id=request.factory_id,
            name=request.name, start_time=request.start_time, end_time=request.end_time,
        )
    except NotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "factory_id does not exist")
    return ShiftRead(
        id=shift.id, factory_id=shift.factory_id, name=shift.name,
        start_time=shift.start_time, end_time=shift.end_time, created_at=shift.created_at,
    )


@router.get(
    "/changeovers", response_model=ShiftChangeoverEventListResponse,
    summary="List recent shift changeover events",
)
async def list_changeovers(
    _current_user: AuthenticatedUser = Depends(require_permission(SHIFTS_READ)),
    service: ShiftsService = Depends(get_shifts_service),
) -> ShiftChangeoverEventListResponse:
    rows = await service.list_changeovers()
    return ShiftChangeoverEventListResponse(
        items=[
            ShiftChangeoverEventRead(
                id=e.id, factory_id=e.factory_id, shift_id=e.shift_id, shift_name=shift_name,
                changeover_at=e.changeover_at, created_at=e.created_at,
            )
            for e, shift_name in rows
        ]
    )


@router.post(
    "/changeovers", response_model=ShiftChangeoverEventRead, status_code=status.HTTP_201_CREATED,
    summary="Log a shift changeover event", description="Requires the 'shifts:write' permission.",
)
async def create_changeover(
    request: ShiftChangeoverEventCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission(SHIFTS_WRITE)),
    service: ShiftsService = Depends(get_shifts_service),
    db: AsyncSession = Depends(get_db),
) -> ShiftChangeoverEventRead:
    try:
        event = await service.create_changeover(
            organization_id=current_user.organization_id, shift_id=request.shift_id,
            changeover_at=request.changeover_at,
        )
    except NotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "shift_id does not exist")
    shift = await db.get(Shift, event.shift_id)
    return ShiftChangeoverEventRead(
        id=event.id, factory_id=event.factory_id, shift_id=event.shift_id, shift_name=shift.name,
        changeover_at=event.changeover_at, created_at=event.created_at,
    )
