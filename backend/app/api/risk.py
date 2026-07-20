from fastapi import APIRouter, Depends

from app.schemas.risk import RiskResponse
from app.services.risk_service import RiskService, get_risk_service

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.get(
    "",
    response_model=RiskResponse,
    summary="List compound risk scores",
    description=(
        "Returns the current compound risk score per zone, with rationale. "
        "Backed by dummy data until the Compound Risk Engine is implemented."
    ),
)
def read_risk_scores(service: RiskService = Depends(get_risk_service)) -> RiskResponse:
    return service.list_scores()
