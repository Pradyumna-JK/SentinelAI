import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import SensorType


class SensorDeviceRead(BaseModel):
    id: uuid.UUID
    zone_id: uuid.UUID
    zone_name: str
    sensor_type: SensorType
    name: str
    unit: str
    baseline_min: float
    baseline_max: float
    latest_value: float | None = Field(None, description="Most recent reading, or null if none yet")
    latest_recorded_at: datetime | None = None
    is_anomaly: bool = Field(False, description="Whether the most recent reading is out of baseline range")


class SensorDeviceListResponse(BaseModel):
    items: list[SensorDeviceRead]


class SensorReadingPoint(BaseModel):
    value: float
    is_anomaly: bool
    recorded_at: datetime


class SensorReadingHistoryResponse(BaseModel):
    sensor_id: uuid.UUID
    readings: list[SensorReadingPoint]


class SensorDeviceCreateRequest(BaseModel):
    zone_id: uuid.UUID
    sensor_type: SensorType
    name: str = Field(..., min_length=1, max_length=200)
    unit: str = Field(..., min_length=1, max_length=20, examples=["ppm"])
    baseline_min: float
    baseline_max: float
