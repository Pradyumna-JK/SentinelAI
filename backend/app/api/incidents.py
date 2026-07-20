from fastapi import APIRouter, Depends

from app.schemas.incidents import IncidentListResponse
from app.services.incidents_service import IncidentsService, get_incidents_service

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get(
    "",
    response_model=IncidentListResponse,
    summary="List incident reports",
    description=(
        "Returns structured incident reports across all monitored zones. "
        "Backed by dummy data until the Incident Report Generator is implemented."
    ),
)
def read_incidents(service: IncidentsService = Depends(get_incidents_service)) -> IncidentListResponse:
    return service.list_incidents()
