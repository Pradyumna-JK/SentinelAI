import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.core.permissions import ALERTS_READ, ALERTS_WRITE
from app.db.session import get_db
from app.models.facility import Zone
from app.schemas.alerts import Alert, AlertCreateRequest, AlertListResponse
from app.schemas.auth import AuthenticatedUser
from app.services.alerts_service import AlertsService, NotFoundError, get_alerts_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _to_alert_read(alert, zone_name: str) -> Alert:
    return Alert(
        id=alert.id,
        zone_id=alert.zone_id,
        zone_name=zone_name,
        source=alert.source,
        severity=alert.severity,
        message=alert.message,
        acknowledged=alert.acknowledged,
        acknowledged_by=alert.acknowledged_by,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at,
    )


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List alerts",
    description=(
        "Returns real-time, severity-ranked alerts across all monitored zones — "
        "written by the vision engine, risk engine, and (from later phases) the "
        "compound-risk correlation engine, permit intelligence agent, and "
        "emergency response orchestrator. Requires the 'alerts:read' permission."
    ),
)
async def read_alerts(
    _current_user: AuthenticatedUser = Depends(require_permission(ALERTS_READ)),
    service: AlertsService = Depends(get_alerts_service),
) -> AlertListResponse:
    alerts, zone_names = await service.list_alerts()
    unacknowledged = sum(1 for a in alerts if not a.acknowledged)
    return AlertListResponse(
        total=len(alerts),
        unacknowledged_count=unacknowledged,
        items=[_to_alert_read(a, zone_names[a.zone_id]) for a in alerts],
    )


@router.post(
    "",
    response_model=Alert,
    status_code=status.HTTP_201_CREATED,
    summary="Create a manual alert",
    description="Requires the 'alerts:write' permission.",
)
async def create_alert(
    request: AlertCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission(ALERTS_WRITE)),
    service: AlertsService = Depends(get_alerts_service),
    db: AsyncSession = Depends(get_db),
) -> Alert:
    try:
        alert = await service.create(
            organization_id=current_user.organization_id,
            zone_id=request.zone_id,
            severity=request.severity,
            message=request.message,
            source=request.source,
        )
    except NotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "zone_id does not exist")
    zone = await db.get(Zone, alert.zone_id)
    return _to_alert_read(alert, zone.name)


@router.post(
    "/{alert_id}/acknowledge",
    response_model=Alert,
    summary="Acknowledge an alert",
    description="Requires the 'alerts:write' permission.",
)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_permission(ALERTS_WRITE)),
    service: AlertsService = Depends(get_alerts_service),
    db: AsyncSession = Depends(get_db),
) -> Alert:
    try:
        alert = await service.acknowledge(alert_id, acknowledged_by=current_user.id)
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    zone = await db.get(Zone, alert.zone_id)
    return _to_alert_read(alert, zone.name)
