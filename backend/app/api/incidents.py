import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.core.permissions import INCIDENTS_READ, INCIDENTS_WRITE
from app.db.session import get_db
from app.models.enums import IncidentStatus
from app.models.facility import Zone
from app.schemas.auth import AuthenticatedUser
from app.schemas.incidents import Incident, IncidentCreateRequest, IncidentListResponse
from app.services.incidents_service import (
    IncidentsService,
    InvalidTransitionError,
    NotFoundError,
    get_incidents_service,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def _to_incident_read(incident, zone_name: str) -> Incident:
    return Incident(
        id=incident.id,
        title=incident.title,
        zone_id=incident.zone_id,
        zone_name=zone_name,
        category=incident.category,
        severity=incident.severity,
        status=incident.status,
        summary=incident.summary,
        detail=incident.detail,
        created_at=incident.created_at,
        approved_by=incident.approved_by,
        approved_at=incident.approved_at,
        closed_at=incident.closed_at,
    )


@router.get(
    "",
    response_model=IncidentListResponse,
    summary="List incident reports",
    description=(
        "Returns structured incident reports across all monitored zones. "
        "Requires the 'incidents:read' permission."
    ),
)
async def read_incidents(
    _current_user: AuthenticatedUser = Depends(require_permission(INCIDENTS_READ)),
    service: IncidentsService = Depends(get_incidents_service),
) -> IncidentListResponse:
    incidents, zone_names = await service.list_incidents()
    return IncidentListResponse(
        total=len(incidents),
        draft_count=sum(1 for i in incidents if i.status == IncidentStatus.DRAFT),
        approved_count=sum(1 for i in incidents if i.status == IncidentStatus.APPROVED),
        items=[_to_incident_read(i, zone_names[i.zone_id]) for i in incidents],
    )


@router.post(
    "",
    response_model=Incident,
    status_code=status.HTTP_201_CREATED,
    summary="File a new incident report",
    description="Created with status='draft'. Requires the 'incidents:write' permission.",
)
async def create_incident(
    request: IncidentCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission(INCIDENTS_WRITE)),
    service: IncidentsService = Depends(get_incidents_service),
    db: AsyncSession = Depends(get_db),
) -> Incident:
    try:
        incident = await service.create(
            organization_id=current_user.organization_id,
            zone_id=request.zone_id,
            title=request.title,
            category=request.category,
            severity=request.severity,
            summary=request.summary,
            detail=request.detail,
            created_by=current_user.id,
        )
    except NotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "zone_id does not exist")
    zone = await db.get(Zone, incident.zone_id)
    return _to_incident_read(incident, zone.name)


@router.post(
    "/{incident_id}/approve",
    response_model=Incident,
    summary="Approve a draft incident report",
    description="Requires the 'incidents:write' permission.",
)
async def approve_incident(
    incident_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_permission(INCIDENTS_WRITE)),
    service: IncidentsService = Depends(get_incidents_service),
    db: AsyncSession = Depends(get_db),
) -> Incident:
    try:
        incident = await service.approve(incident_id, approved_by=current_user.id)
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Incident not found")
    except InvalidTransitionError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only a draft incident can be approved")
    zone = await db.get(Zone, incident.zone_id)
    return _to_incident_read(incident, zone.name)


@router.post(
    "/{incident_id}/close",
    response_model=Incident,
    summary="Close an approved incident report",
    description="Requires the 'incidents:write' permission.",
)
async def close_incident(
    incident_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(require_permission(INCIDENTS_WRITE)),
    service: IncidentsService = Depends(get_incidents_service),
    db: AsyncSession = Depends(get_db),
) -> Incident:
    try:
        incident = await service.close(incident_id)
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Incident not found")
    except InvalidTransitionError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only an approved incident can be closed")
    zone = await db.get(Zone, incident.zone_id)
    return _to_incident_read(incident, zone.name)
