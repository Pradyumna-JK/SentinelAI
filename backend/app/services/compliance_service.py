"""Business logic for the Compliance module.

Thin orchestration layer over the Compliance Copilot (app/ai/compliance) —
passes the validated request through. Contains no answer-generation logic
of its own.
"""

from fastapi import Depends

from app.ai.compliance.copilot import ComplianceCopilot, get_compliance_copilot
from app.schemas.compliance import ComplianceChatRequest, ComplianceChatResponse


class ComplianceService:
    """Delegates compliance chat questions to the Compliance Copilot."""

    def __init__(self, copilot: ComplianceCopilot) -> None:
        self._copilot = copilot

    def chat(self, request: ComplianceChatRequest) -> ComplianceChatResponse:
        return self._copilot.answer(request.question, request.session_id)


def get_compliance_service(
    copilot: ComplianceCopilot = Depends(get_compliance_copilot),
) -> ComplianceService:
    return ComplianceService(copilot)
