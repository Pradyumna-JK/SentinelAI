"""FastAPI dependencies for authentication and authorization.

`get_current_user` decodes the bearer access token and re-fetches the user
row by primary key purely to catch "deactivated since the token was issued"
immediately — roles/permissions themselves are trusted from the token's
claims rather than re-queried on every request, which is the standard
access-token performance/staleness trade-off, bounded by the token's short
TTL (see app/core/config.py's access_token_expire_minutes).
"""

import uuid
from collections.abc import Callable, Coroutine
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthenticatedUser

# auto_error=False so a missing header produces our own 401 message (with
# the WWW-Authenticate header) instead of FastAPI's generic "Not authenticated".
_bearer_scheme = HTTPBearer(auto_error=False, description="Access token from POST /auth/login")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Missing or invalid bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise unauthorized

    try:
        user_id = uuid.UUID(payload["sub"])
        organization_id = uuid.UUID(payload["org_id"])
    except (KeyError, ValueError):
        raise unauthorized

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account is inactive or no longer exists")

    return AuthenticatedUser(
        id=user.id,
        organization_id=organization_id,
        email=user.email,
        roles=payload.get("roles", []),
        permissions=set(payload.get("permissions", [])),
    )


def require_permission(
    *required: str,
) -> Callable[[AuthenticatedUser], Coroutine[Any, Any, AuthenticatedUser]]:
    """Dependency factory: 403s unless the caller holds every listed permission code."""

    async def _checker(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        missing = [p for p in required if p not in current_user.permissions]
        if missing:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Missing required permission(s): {', '.join(missing)}",
            )
        return current_user

    return _checker


def require_role(
    *allowed_roles: str,
) -> Callable[[AuthenticatedUser], Coroutine[Any, Any, AuthenticatedUser]]:
    """Dependency factory: 403s unless the caller holds at least one listed role."""

    async def _checker(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not set(current_user.roles) & set(allowed_roles):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Requires one of role(s): {', '.join(allowed_roles)}",
            )
        return current_user

    return _checker
