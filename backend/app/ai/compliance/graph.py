"""LangGraph RAG pipeline: classify_intent -> retrieve.

Deliberately stops short of generation. Streaming the answer token-by-token
to an SSE client is a much better fit for a plain `ChatGoogleGenerativeAI().astream()`
call in app/services/compliance_chat_service.py than for a LangGraph node —
driving token streaming out of `astream_events()` requires matching on
event names/metadata that shift across langchain/langgraph versions, for a
single linear call with no branching benefit from being inside the graph.
LangGraph earns its place here for the part that *does* branch on outcome:
classify the question, retrieve, and — critically — let the caller decide
to skip the LLM call entirely when nothing relevant was retrieved (FR-COMP-002,
docs/11_AI_ARCHITECTURE.md §4: no fabricated answers, ever).
"""

from typing import TypedDict

import structlog
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from app.ai.compliance import prompts
from app.ai.compliance.embeddings import get_embeddings
from app.ai.compliance.types import RetrievedChunk
from app.ai.compliance.vectorstore import query as vector_query
from app.ai.llm_content import extract_text
from app.core.config import get_settings
from app.models.enums import ComplianceIntent

logger = structlog.get_logger("sentinel.compliance.graph")

_INTENT_VALUES = {i.value for i in ComplianceIntent}


class GraphState(TypedDict):
    organization_id: str
    question: str
    intent: str
    retrieved: list[RetrievedChunk]


async def _classify_intent(state: GraphState) -> dict:
    settings = get_settings()
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_chat_model,
        google_api_key=settings.gemini_api_key.get_secret_value(),
        temperature=0,
    )
    try:
        response = await llm.ainvoke(
            [HumanMessage(content=prompts.INTENT_CLASSIFIER_PROMPT.format(question=state["question"]))]
        )
        raw = extract_text(response.content).strip().lower()
    except Exception:  # noqa: BLE001 — classification is an optimization, not a hard requirement
        logger.exception("compliance_intent_classification_failed")
        raw = ComplianceIntent.GENERAL.value
    return {"intent": raw if raw in _INTENT_VALUES else ComplianceIntent.GENERAL.value}


async def _retrieve(state: GraphState) -> dict:
    import anyio

    settings = get_settings()
    embeddings = get_embeddings()
    query_vector = await embeddings.aembed_query(state["question"])
    chunks = await anyio.to_thread.run_sync(
        lambda: vector_query(
            organization_id=state["organization_id"],
            query_embedding=query_vector,
            top_k=settings.compliance_retrieval_top_k,
        )
    )
    relevant = [c for c in chunks if c.similarity >= settings.compliance_min_relevance_score]
    return {"retrieved": relevant}


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("classify_intent", _classify_intent)
    graph.add_node("retrieve", _retrieve)
    graph.set_entry_point("classify_intent")
    graph.add_edge("classify_intent", "retrieve")
    graph.add_edge("retrieve", END)
    return graph.compile()


_graph = None


def get_compliance_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
