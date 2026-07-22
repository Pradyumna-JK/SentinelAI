"""Compliance Copilot persistence: uploaded source documents, chat
sessions, and their turns.

Three tables, all TenantScoped (tenant-isolated the same way as every
other business table — see app/core/tenancy.py):

- ComplianceDocument: one row per uploaded PDF. Tracks the background
  ingestion worker's progress (app/ai/compliance/worker.py) through
  `status`; the actual extracted chunks/embeddings live in ChromaDB, not
  here — this table is the source-of-truth for "what was uploaded and did
  it ingest successfully", Chroma is the source-of-truth for "what's
  retrievable".
- ComplianceChatSession: one row per conversation thread.
- ComplianceChatMessage: one row per turn (user question or assistant
  answer) — this is what makes conversation memory durable across
  restarts/replicas instead of an in-process cache (see
  app/ai/compliance/memory.py).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tenancy import TenantScoped
from app.models.base import Base, str_enum
from app.models.enums import ChatRole, DocumentStatus


class ComplianceDocument(Base, TenantScoped):
    __tablename__ = "compliance_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # MinIO object key, e.g. "compliance/{organization_id}/{document_id}/{filename}"
    # — the raw PDF stays in object storage; Postgres never holds the bytes.
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/pdf")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[DocumentStatus] = mapped_column(
        str_enum(DocumentStatus, 20), nullable=False, default=DocumentStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ComplianceChatSession(Base, TenantScoped):
    __tablename__ = "compliance_chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Set from the first question once answered — nullable until then rather
    # than eagerly derived, since deriving it costs an extra LLM call this
    # module has no other reason to make.
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ComplianceChatMessage(Base, TenantScoped):
    __tablename__ = "compliance_chat_messages"
    __table_args__ = (Index("ix_compliance_chat_messages_session_created_at", "session_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("compliance_chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[ChatRole] = mapped_column(str_enum(ChatRole, 20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Populated on assistant messages only (the classify_intent graph node's
    # output) — null on user messages.
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # [{"document_id": "...", "title": "...", "chunk_index": 0, "similarity": 0.82}, ...]
    # Always [] on user messages and on "insufficient information" answers.
    citations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
