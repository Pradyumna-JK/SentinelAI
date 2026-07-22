"""Conversation memory formatting: persisted ComplianceChatMessage rows ->
LangChain message objects for the next generation call.

Backed by Postgres, not an in-process cache — memory must survive a
container restart and stay consistent across replicas, unlike e.g. the
vision engine's in-memory frame queue which has no such requirement. See
app/services/compliance_chat_service.py for where the trailing-N-messages
window (settings.compliance_history_window) is applied before this is called.
"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.ai.compliance.types import ChatTurn


def to_langchain_messages(turns: list[ChatTurn]) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for turn in turns:
        if turn.role == "user":
            messages.append(HumanMessage(content=turn.content))
        else:
            messages.append(AIMessage(content=turn.content))
    return messages
