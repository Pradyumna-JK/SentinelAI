from fastapi import APIRouter, Depends

from app.core.deps import require_permission
from app.core.permissions import DASHBOARD_READ
from app.schemas.auth import AuthenticatedUser
from app.schemas.dashboard import DashboardOverview
from app.services.dashboard_service import DashboardService, get_dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "",
    response_model=DashboardOverview,
    summary="Get dashboard overview",
    description=(
        "Returns the live risk state (Risk Intelligence Engine), active alert "
        "counts, and real AI agent health across all monitored sites and "
        "zones. Requires the 'dashboard:read' permission."
    ),
)
async def read_dashboard(
    current_user: AuthenticatedUser = Depends(require_permission(DASHBOARD_READ)),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardOverview:
    return await service.get_overview(current_user.organization_id)
