from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.core.permissions import EMERGENCY_READ, EMERGENCY_WRITE
from app.db.session import get_db
from app.models.enums import RiskLevel
from app.models.facility import Zone
from app.schemas.auth import AuthenticatedUser
from app.schemas.emergency import (
    EmergencyProtocolCreateRequest,
    EmergencyProtocolListResponse,
    EmergencyProtocolRead,
    EmergencyTriggerRequest,
    EmergencyTriggerResponse,
)
from app.services.emergency_protocol_service import EmergencyProtocolService, get_emergency_protocol_service
from app.services.emergency_response_service import EmergencyResponseService
from app.services.risk_engine_service import RiskEngineService

router = APIRouter(prefix="/emergency", tags=["Emergency"])


@router.get(
    "/protocols",
    response_model=EmergencyProtocolListResponse,
    summary="List configured emergency protocols",
    description="Requires the 'emergency:read' permission.",
)
async def list_protocols(
    _current_user: AuthenticatedUser = Depends(require_permission(EMERGENCY_READ)),
    service: EmergencyProtocolService = Depends(get_emergency_protocol_service),
) -> EmergencyProtocolListResponse:
    protocols = await service.list_protocols()
    return EmergencyProtocolListResponse(
        items=[
            EmergencyProtocolRead(
                id=p.id, hazard_type=p.hazard_type, steps=p.steps,
                evacuation_route=p.evacuation_route, created_at=p.created_at,
            )
            for p in protocols
        ]
    )


@router.post(
    "/protocols",
    response_model=EmergencyProtocolRead,
    status_code=status.HTTP_201_CREATED,
    summary="Configure an emergency protocol",
    description=(
        "hazard_type is matched against a RiskEvent's hazard_class exactly; "
        "use hazard_type='general' to configure the fallback protocol used "
        "when nothing more specific matches. Requires 'emergency:write'."
    ),
)
async def create_protocol(
    request: EmergencyProtocolCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission(EMERGENCY_WRITE)),
    service: EmergencyProtocolService = Depends(get_emergency_protocol_service),
) -> EmergencyProtocolRead:
    protocol = await service.create(
        organization_id=current_user.organization_id, hazard_type=request.hazard_type,
        steps=request.steps, evacuation_route=request.evacuation_route,
    )
    return EmergencyProtocolRead(
        id=protocol.id, hazard_type=protocol.hazard_type, steps=protocol.steps,
        evacuation_route=protocol.evacuation_route, created_at=protocol.created_at,
    )


@router.post(
    "/trigger",
    response_model=EmergencyTriggerResponse,
    summary="Manually run the Emergency Response Orchestrator for a zone",
    description=(
        "Recomputes the zone's current risk and, only if it is genuinely at "
        "Critical level right now, runs the same protocol-match -> "
        "incident-draft -> alert flow the background scheduler runs "
        "automatically. Does not fabricate a Critical state — if the zone "
        "isn't actually Critical, reports that plainly instead. Requires "
        "'emergency:write'."
    ),
)
async def trigger(
    request: EmergencyTriggerRequest,
    current_user: AuthenticatedUser = Depends(require_permission(EMERGENCY_WRITE)),
    db: AsyncSession = Depends(get_db),
) -> EmergencyTriggerResponse:
    if await db.get(Zone, request.zone_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")

    risk_engine = RiskEngineService(db)
    computation = await risk_engine.compute_zone_risk(request.zone_id)

    if computation.level != RiskLevel.CRITICAL:
        await db.commit()
        return EmergencyTriggerResponse(
            triggered=False,
            incident_id=None,
            message=f"Zone is not currently at Critical risk (current: {computation.level.value}, score {computation.score}).",
        )

    emergency_service = EmergencyResponseService(db)
    incident = await emergency_service.handle_critical_zone(
        organization_id=current_user.organization_id, zone_id=request.zone_id, computation=computation
    )
    await db.commit()

    if incident is None:
        return EmergencyTriggerResponse(
            triggered=False,
            incident_id=None,
            message="Zone is Critical, but an emergency incident was already created for it within the last 10 minutes (cooldown).",
        )
    return EmergencyTriggerResponse(
        triggered=True, incident_id=incident.id, message="Emergency response triggered."
    )
