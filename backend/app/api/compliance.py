from fastapi import APIRouter, Depends

from app.schemas.compliance import ComplianceChatRequest, ComplianceChatResponse
from app.services.compliance_service import ComplianceService, get_compliance_service

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.post(
    "/chat",
    response_model=ComplianceChatResponse,
    summary="Chat with the Compliance Copilot",
    description=(
        "Ask a natural-language safety/compliance question. Returns a deterministic "
        "placeholder response until the RAG-based Compliance Copilot agent is implemented."
    ),
)
def chat(
    request: ComplianceChatRequest,
    service: ComplianceService = Depends(get_compliance_service),
) -> ComplianceChatResponse:
    return service.chat(request)
