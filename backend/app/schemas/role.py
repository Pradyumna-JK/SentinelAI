import uuid

from pydantic import BaseModel


class PermissionRead(BaseModel):
    id: uuid.UUID
    code: str
    description: str

    model_config = {"from_attributes": True}


class RoleRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    permissions: list[PermissionRead]

    model_config = {"from_attributes": True}


class RoleListResponse(BaseModel):
    items: list[RoleRead]
