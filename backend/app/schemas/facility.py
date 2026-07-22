import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FactoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50, description="Short identifier, unique within your organization")


class FactoryRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    code: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FactoryListResponse(BaseModel):
    items: list[FactoryRead]


class SiteCreate(BaseModel):
    factory_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50, description="Short identifier, unique within the factory")
    address: str | None = Field(None, max_length=300)


class SiteRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    factory_id: uuid.UUID
    name: str
    code: str
    address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SiteListResponse(BaseModel):
    items: list[SiteRead]


class BuildingCreate(BaseModel):
    site_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50, description="Short identifier, unique within the site")
    floor_count: int | None = Field(None, ge=1)


class BuildingRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    site_id: uuid.UUID
    name: str
    code: str
    floor_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BuildingListResponse(BaseModel):
    items: list[BuildingRead]


class ZoneCreate(BaseModel):
    building_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50, description="Short identifier, unique within the building")
    zone_type: str | None = Field(None, max_length=50, examples=["loading_dock", "assembly_line", "storage"])


class ZoneRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    building_id: uuid.UUID
    name: str
    code: str
    zone_type: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ZoneListResponse(BaseModel):
    items: list[ZoneRead]
