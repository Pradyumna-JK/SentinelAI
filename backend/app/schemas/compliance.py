import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ChatRole, DocumentStatus


class ComplianceDocumentRead(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    page_count: int | None
    chunk_count: int
    error_message: str | None
    created_at: datetime
    processed_at: datetime | None


class ComplianceDocumentListResponse(BaseModel):
    items: list[ComplianceDocumentRead]


class ComplianceSessionRead(BaseModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ComplianceSessionListResponse(BaseModel):
    items: list[ComplianceSessionRead]


class ComplianceCitation(BaseModel):
    document_id: str = Field(..., description="Identifier of the source compliance document")
    title: str = Field(..., description="Title of the source compliance document")
    chunk_index: int = Field(..., ge=0, description="Index of the cited chunk within the document")
    similarity: float = Field(..., description="Cosine similarity of this chunk to the question, 0-1")


class ComplianceMessageRead(BaseModel):
    id: uuid.UUID
    role: ChatRole
    content: str
    intent: str | None
    citations: list[ComplianceCitation]
    created_at: datetime


class ComplianceHistoryResponse(BaseModel):
    session_id: uuid.UUID
    messages: list[ComplianceMessageRead]


class ComplianceChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural-language compliance question",
        examples=["What PPE is required in a high-noise zone under OSHA 1910.95?"],
    )
    session_id: uuid.UUID | None = Field(
        None, description="Continue an existing session; omit to start a new one"
    )


class ExplainCompoundRiskRequest(BaseModel):
    zone_id: uuid.UUID = Field(..., description="Zone whose current compound risk finding to explain")
    session_id: uuid.UUID | None = Field(
        None, description="Continue an existing session; omit to start a new one"
    )
