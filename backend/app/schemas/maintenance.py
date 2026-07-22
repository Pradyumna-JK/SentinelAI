import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import EquipmentCriticality, MaintenanceStatus


class EquipmentRead(BaseModel):
    id: uuid.UUID
    zone_id: uuid.UUID
    zone_name: str
    name: str
    equipment_type: str
    criticality: EquipmentCriticality
    created_at: datetime


class EquipmentListResponse(BaseModel):
    items: list[EquipmentRead]


class EquipmentCreateRequest(BaseModel):
    zone_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=200)
    equipment_type: str = Field(..., min_length=1, max_length=100)
    criticality: EquipmentCriticality = EquipmentCriticality.MEDIUM


class MaintenanceRecordRead(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    equipment_name: str
    zone_id: uuid.UUID
    status: MaintenanceStatus
    technician: str | None
    window_start: datetime
    window_end: datetime
    created_at: datetime


class MaintenanceRecordListResponse(BaseModel):
    items: list[MaintenanceRecordRead]


class MaintenanceRecordCreateRequest(BaseModel):
    equipment_id: uuid.UUID
    technician: str | None = None
    window_start: datetime
    window_end: datetime
