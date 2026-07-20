from pydantic import BaseModel, Field


class ComplianceChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural-language compliance question",
        examples=["What PPE is required in a high-noise zone under OSHA 1910.95?"],
    )
    session_id: str | None = Field(
        None, description="Optional identifier to continue a prior conversation"
    )


class ComplianceCitation(BaseModel):
    document_id: str = Field(..., description="Identifier of the source compliance document")
    title: str = Field(..., description="Title of the source compliance document")
    chunk_index: int = Field(..., ge=0, description="Index of the cited chunk within the document")


class ComplianceChatResponse(BaseModel):
    answer: str | None = Field(None, description="Answer text, or null if no relevant document was found")
    citations: list[ComplianceCitation]
    insufficient_info: bool = Field(
        ..., description="True when no relevant document could be found to answer the question"
    )
    session_id: str = Field(..., description="Session identifier for this conversation")

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "This is a placeholder response. The Compliance Copilot agent is not yet implemented.",
                "citations": [],
                "insufficient_info": True,
                "session_id": "session-001",
            }
        }
    }
