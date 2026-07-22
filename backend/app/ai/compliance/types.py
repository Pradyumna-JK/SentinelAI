"""Pure data types shared across the Compliance Copilot's AI modules.

No DB, no HTTP, no LangChain/LangGraph imports here on purpose — these are
the plain values that cross the boundary between app/ai/compliance's
internals and app/services/compliance_*.py.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    title: str
    chunk_index: int
    text: str
    similarity: float


@dataclass(frozen=True)
class ChatTurn:
    role: str  # "user" | "assistant"
    content: str
