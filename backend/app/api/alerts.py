from fastapi import APIRouter, Depends

from app.schemas.alerts import AlertListResponse
from app.services.alerts_service import AlertsService, get_alerts_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List alerts",
    description=(
        "Returns real-time, severity-ranked alerts across all monitored zones. "
        "Backed by dummy data until the Compound Risk Engine is implemented."
    ),
)
def read_alerts(service: AlertsService = Depends(get_alerts_service)) -> AlertListResponse:
    return service.list_alerts()
