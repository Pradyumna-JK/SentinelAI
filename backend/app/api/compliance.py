"""Compliance Copilot endpoints: document upload/management, conversation
sessions, and the streaming RAG chat turn.

`POST /compliance/chat` is Server-Sent Events (`text/event-stream`), not a
JSON response — the point of streaming is the client starts rendering
tokens before the full answer exists. Event types: `citations` (once, only
when context was found — the retrieved chunks the answer will be grounded
in, sent before any tokens so a client can render "sources" immediately),
`token` (repeated, one per generated token, or the whole insufficient-info
message as a single token event), and `done` (once, terminal — carries
`session_id`/`intent`/`insufficient_info` so the client can persist/route
without re-parsing the stream). No `response_model` on that endpoint:
FastAPI's response_model machinery is for JSON bodies, not event streams.
"""

import json
import uuid

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.compound_risk.graph import run_for_zone
from app.core.deps import require_permission
from app.core.permissions import COMPLIANCE_READ, COMPLIANCE_WRITE
from app.db.session import get_db
from app.models.compliance import ComplianceChatMessage, ComplianceChatSession, ComplianceDocument
from app.models.facility import Zone
from app.schemas.auth import AuthenticatedUser
from app.schemas.compliance import (
    ComplianceChatRequest,
    ComplianceCitation,
    ComplianceDocumentListResponse,
    ComplianceDocumentRead,
    ComplianceHistoryResponse,
    ComplianceMessageRead,
    ComplianceSessionListResponse,
    ComplianceSessionRead,
    ExplainCompoundRiskRequest,
)
from app.services.compliance_chat_service import (
    ComplianceChatService,
    SessionNotFoundError,
    get_compliance_chat_service,
)
from app.services.compliance_ingest_service import (
    ComplianceIngestService,
    DocumentNotFoundError,
    InvalidDocumentError,
    get_compliance_ingest_service,
)

router = APIRouter(prefix="/compliance", tags=["Compliance"])
logger = structlog.get_logger("sentinel.compliance.api")


def _to_document_read(document: ComplianceDocument) -> ComplianceDocumentRead:
    return ComplianceDocumentRead(
        id=document.id,
        filename=document.filename,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        status=document.status,
        page_count=document.page_count,
        chunk_count=document.chunk_count,
        error_message=document.error_message,
        created_at=document.created_at,
        processed_at=document.processed_at,
    )


def _to_session_read(session: ComplianceChatSession) -> ComplianceSessionRead:
    return ComplianceSessionRead(
        id=session.id, title=session.title, created_at=session.created_at, updated_at=session.updated_at
    )


def _to_message_read(message: ComplianceChatMessage) -> ComplianceMessageRead:
    return ComplianceMessageRead(
        id=message.id,
        role=message.role,
        content=message.content,
        intent=message.intent,
        citations=[ComplianceCitation(**c) for c in message.citations],
        created_at=message.created_at,
    )


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _stream_chat_response(
    service: ComplianceChatService,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    session_id: uuid.UUID | None,
    question: str,
) -> StreamingResponse:
    """Shared by /chat and /explain-compound-risk — both are just different
    ways of arriving at a `question` for the same RAG pipeline."""

    async def _event_stream():
        try:
            async for event in service.stream_chat(
                organization_id=organization_id, user_id=user_id, session_id=session_id, question=question,
            ):
                event_type = event.pop("type")
                yield _sse(event_type, event)
        except SessionNotFoundError:
            yield _sse("error", {"detail": "Session not found"})
        except Exception as exc:  # noqa: BLE001 — an upstream (Gemini/Chroma) failure mid-stream
            # must reach the client as a clean terminal event, not a silently
            # dropped connection — headers are already sent by this point,
            # so an HTTPException here would do nothing useful.
            logger.exception("compliance_chat_stream_failed")
            yield _sse("error", {"detail": f"{type(exc).__name__}: {exc}"[:200]})

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


# ------------------------------------------------------------- documents


@router.post(
    "/documents",
    response_model=ComplianceDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a compliance PDF for background ingestion",
    description=(
        "Stores the PDF in object storage and queues it for the background "
        "ingestion worker (extract -> chunk -> embed -> upsert into "
        "ChromaDB). Returns immediately with status=pending; poll "
        "GET /compliance/documents/{id} for status. Requires 'compliance:write'."
    ),
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(require_permission(COMPLIANCE_WRITE)),
    service: ComplianceIngestService = Depends(get_compliance_ingest_service),
) -> ComplianceDocumentRead:
    data = await file.read()
    try:
        document = await service.upload_document(
            organization_id=current_user.organization_id,
            uploaded_by=current_user.id,
            filename=file.filename or "document.pdf",
            content_type=file.content_type or "application/pdf",
            data=data,
        )
    except InvalidDocumentError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    return _to_document_read(document)


@router.get(
    "/documents",
    response_model=ComplianceDocumentListResponse,
    summary="List uploaded compliance documents and their ingestion status",
)
async def list_documents(
    _current_user: AuthenticatedUser = Depends(require_permission(COMPLIANCE_READ)),
    service: ComplianceIngestService = Depends(get_compliance_ingest_service),
) -> ComplianceDocumentListResponse:
    documents = await service.list_documents()
    return ComplianceDocumentListResponse(items=[_to_document_read(d) for d in documents])


@router.get(
    "/documents/{document_id}",
    response_model=ComplianceDocumentRead,
    summary="Get one document's ingestion status",
)
async def get_document(
    document_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(require_permission(COMPLIANCE_READ)),
    service: ComplianceIngestService = Depends(get_compliance_ingest_service),
) -> ComplianceDocumentRead:
    try:
        document = await service.get_document(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return _to_document_read(document)


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its ingested chunks",
)
async def delete_document(
    document_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(require_permission(COMPLIANCE_WRITE)),
    service: ComplianceIngestService = Depends(get_compliance_ingest_service),
) -> None:
    try:
        await service.delete_document(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")


# ------------------------------------------------------------- sessions


@router.post(
    "/sessions",
    response_model=ComplianceSessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new conversation",
)
async def create_session(
    current_user: AuthenticatedUser = Depends(require_permission(COMPLIANCE_WRITE)),
    service: ComplianceChatService = Depends(get_compliance_chat_service),
) -> ComplianceSessionRead:
    session = await service.create_session(organization_id=current_user.organization_id, user_id=current_user.id)
    return _to_session_read(session)


@router.get(
    "/sessions",
    response_model=ComplianceSessionListResponse,
    summary="List your conversations",
)
async def list_sessions(
    current_user: AuthenticatedUser = Depends(require_permission(COMPLIANCE_READ)),
    service: ComplianceChatService = Depends(get_compliance_chat_service),
) -> ComplianceSessionListResponse:
    sessions = await service.list_sessions(user_id=current_user.id)
    return ComplianceSessionListResponse(items=[_to_session_read(s) for s in sessions])


@router.get(
    "/sessions/{session_id}/messages",
    response_model=ComplianceHistoryResponse,
    summary="Full message history for one conversation",
)
async def get_session_history(
    session_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_permission(COMPLIANCE_READ)),
    service: ComplianceChatService = Depends(get_compliance_chat_service),
) -> ComplianceHistoryResponse:
    try:
        messages = await service.get_history(session_id, user_id=current_user.id)
    except SessionNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return ComplianceHistoryResponse(session_id=session_id, messages=[_to_message_read(m) for m in messages])


# ------------------------------------------------------------- chat


@router.post(
    "/chat",
    summary="Ask the Compliance Copilot a question (streams the answer)",
    description=(
        "Server-Sent Events stream. Classifies the question's intent (safety "
        "rule lookup / incident explanation / compliance recommendation / "
        "general), retrieves grounding context from ingested documents, and "
        "streams a generated answer token-by-token — or, if nothing relevant "
        "was found, an explicit insufficient-information message with no LLM "
        "call made. Conversation memory is loaded automatically from prior "
        "turns in the session. Requires 'compliance:write'."
    ),
)
async def chat(
    request: ComplianceChatRequest,
    current_user: AuthenticatedUser = Depends(require_permission(COMPLIANCE_WRITE)),
    service: ComplianceChatService = Depends(get_compliance_chat_service),
) -> StreamingResponse:
    return _stream_chat_response(
        service,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        session_id=request.session_id,
        question=request.question,
    )


@router.post(
    "/explain-compound-risk",
    summary="Ask the Compliance Copilot to explain a zone's current compound risk finding",
    description=(
        "Runs the Compound Risk Intelligence Engine's signal-fusion graph "
        "live for the zone, then asks the *same* RAG pipeline `/chat` uses "
        "to ground an explanation of why that combination is dangerous in "
        "the ingested regulatory corpus (OISD/Factory Act/SOPs) — no "
        "separate AI system, just a question constructed from the fused "
        "signals instead of typed by hand. Streams like /chat. Requires "
        "'compliance:write'."
    ),
)
async def explain_compound_risk(
    request: ExplainCompoundRiskRequest,
    current_user: AuthenticatedUser = Depends(require_permission(COMPLIANCE_WRITE)),
    service: ComplianceChatService = Depends(get_compliance_chat_service),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    zone = await db.get(Zone, request.zone_id)
    if zone is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")

    finding = await run_for_zone(db, zone_id=request.zone_id)
    if finding.severity <= 0:
        question = (
            f"No compound risk signals (gas anomalies, work permits, maintenance, shift changeovers) "
            f"are currently coinciding in the '{zone.name}' zone. In general, what does the ingested "
            f"safety documentation say about routine monitoring requirements for this kind of zone?"
        )
    else:
        question = (
            f"In the '{zone.name}' zone, these safety conditions are currently coinciding: "
            f"{finding.rationale} Contributing factors: {', '.join(finding.dominant_signals)}. "
            "Explain why this specific combination is dangerous, and cite the relevant safety "
            "regulations, standards, or SOPs that apply."
        )

    return _stream_chat_response(
        service,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        session_id=request.session_id,
        question=question,
    )
