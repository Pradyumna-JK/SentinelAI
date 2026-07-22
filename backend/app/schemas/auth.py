import uuid

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

    model_config = {"json_schema_extra": {"example": {"email": "admin@sentinelai.demo", "password": "••••••••"}}}


class TokenPair(BaseModel):
    access_token: str = Field(..., description="Short-lived JWT — send as 'Authorization: Bearer <token>'")
    refresh_token: str = Field(..., description="Long-lived opaque token — presented only to POST /auth/refresh")
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds")


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., description="The refresh token whose session should be ended")


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    message: str


class AuthenticatedUser(BaseModel):
    """The identity resolved from a validated access token.

    Deliberately not the ORM `User` model: routers and dependencies should
    depend on this stable, request-scoped shape, not on persistence
    internals. `permissions` is a set for O(1) membership checks in
    `require_permission`.
    """

    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    roles: list[str]
    permissions: set[str]
