import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.compound_risk.graph import run_for_zone
from app.core.deps import require_permission
from app.core.permissions import RISK_READ
from app.db.session import get_db
from app.models.facility import Zone
from app.schemas.auth import AuthenticatedUser
from app.schemas.compound_risk import CompoundRiskExplanation

router = APIRouter(prefix="/compound-risk", tags=["Compound Risk"])


@router.get(
    "/zones/{zone_id}",
    response_model=CompoundRiskExplanation,
    summary="Explain the current compound risk finding for a zone",
    description=(
        "Runs the Compound Risk Intelligence Engine's signal-fusion graph "
        "live (gas sensors, permits, maintenance, shift changeovers) and "
        "reports which signals are currently coinciding and why — the "
        "explainability endpoint for 'data present, but nothing correlates "
        "it' (this is the read path; the background scheduler is what "
        "persists findings into the Risk Intelligence Engine). Requires "
        "the 'risk:read' permission."
    ),
)
async def explain_zone(
    zone_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(require_permission(RISK_READ)),
    db: AsyncSession = Depends(get_db),
) -> CompoundRiskExplanation:
    if await db.get(Zone, zone_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")
    finding = await run_for_zone(db, zone_id=zone_id)
    return CompoundRiskExplanation(
        zone_id=zone_id,
        combined=finding.combined,
        severity=finding.severity,
        hazard_class=finding.hazard_class,
        dominant_signals=finding.dominant_signals,
        rationale=finding.rationale,
    )
