"""Compliance Copilot.

The RAG pipeline (ChromaDB + Sentence Transformers) is not implemented yet.
Returns a deterministic placeholder so the API contract and frontend
integration can be built and tested ahead of the real implementation
(docs/11_AI_ARCHITECTURE.md §4).
"""

from functools import lru_cache

from app.schemas.compliance import ComplianceChatResponse
from app.utils.generators import new_uuid


class ComplianceCopilot:
    """Answers natural-language compliance questions."""

    def answer(self, question: str, session_id: str | None = None) -> ComplianceChatResponse:
        return ComplianceChatResponse(
            answer=(
                "This is a placeholder response. The Compliance Copilot AI agent has not "
                "been implemented yet, so no regulatory documents were actually searched."
            ),
            citations=[],
            insufficient_info=True,
            session_id=session_id or new_uuid(),
        )


@lru_cache
def get_compliance_copilot() -> ComplianceCopilot:
    return ComplianceCopilot()
