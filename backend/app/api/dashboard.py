from fastapi import APIRouter, Depends

from app.schemas.dashboard import DashboardOverview
from app.services.dashboard_service import DashboardService, get_dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "",
    response_model=DashboardOverview,
    summary="Get dashboard overview",
    description=(
        "Returns the live risk state, active alert counts, and AI agent health "
        "across all monitored sites and zones. Backed by dummy data until the "
        "Compound Risk Engine is implemented."
    ),
)
def read_dashboard(service: DashboardService = Depends(get_dashboard_service)) -> DashboardOverview:
    return service.get_overview()
