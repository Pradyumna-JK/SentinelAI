import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import PermitStatus, PermitType


class WorkPermitRead(BaseModel):
    id: uuid.UUID
    zone_id: uuid.UUID
    zone_name: str
    permit_type: PermitType
    status: PermitStatus
    description: str
    issued_by: uuid.UUID | None
    valid_from: datetime
    valid_to: datetime
    created_at: datetime


class WorkPermitListResponse(BaseModel):
    items: list[WorkPermitRead]


class WorkPermitCreateRequest(BaseModel):
    zone_id: uuid.UUID
    permit_type: PermitType
    description: str = Field(..., min_length=1)
    valid_from: datetime
    valid_to: datetime
