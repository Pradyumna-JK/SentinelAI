import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RoleBrief(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=200)
    role_names: list[str] = Field(
        default_factory=list, description="System role names to assign at creation, e.g. ['Operator']"
    )


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=200)
    is_active: bool | None = None


class UserRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    roles: list[RoleBrief]
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    items: list[UserRead]
