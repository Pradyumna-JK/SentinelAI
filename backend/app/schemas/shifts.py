import uuid
from datetime import datetime, time

from pydantic import BaseModel, Field


class ShiftRead(BaseModel):
    id: uuid.UUID
    factory_id: uuid.UUID
    name: str
    start_time: time
    end_time: time
    created_at: datetime


class ShiftListResponse(BaseModel):
    items: list[ShiftRead]


class ShiftCreateRequest(BaseModel):
    factory_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=100)
    start_time: time
    end_time: time


class ShiftChangeoverEventRead(BaseModel):
    id: uuid.UUID
    factory_id: uuid.UUID
    shift_id: uuid.UUID
    shift_name: str
    changeover_at: datetime
    created_at: datetime


class ShiftChangeoverEventListResponse(BaseModel):
    items: list[ShiftChangeoverEventRead]


class ShiftChangeoverEventCreateRequest(BaseModel):
    shift_id: uuid.UUID
    changeover_at: datetime
