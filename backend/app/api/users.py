"""User management endpoints (organization-scoped)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import require_permission
from app.core.permissions import ROLES_MANAGE, USERS_READ, USERS_WRITE
from app.schemas.auth import AuthenticatedUser
from app.schemas.user import UserCreate, UserListResponse, UserRead, UserUpdate
from app.services.user_service import (
    EmailAlreadyExistsError,
    RoleNotFoundError,
    UserNotFoundError,
    UserService,
    get_user_service,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListResponse, summary="List users in your organization")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(require_permission(USERS_READ)),
    service: UserService = Depends(get_user_service),
) -> UserListResponse:
    users, total = await service.list_users(current_user.organization_id, page=page, limit=limit)
    return UserListResponse(total=total, items=[UserRead.model_validate(u) for u in users])


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user in your organization",
)
async def create_user(
    payload: UserCreate,
    current_user: AuthenticatedUser = Depends(require_permission(USERS_WRITE)),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    try:
        user = await service.create_user(current_user.organization_id, payload)
    except EmailAlreadyExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, "A user with this email already exists")
    except RoleNotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "One or more role_names do not exist")
    return UserRead.model_validate(user)


@router.get("/{user_id}", response_model=UserRead, summary="Get a single user")
async def get_user(
    user_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_permission(USERS_READ)),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    try:
        user = await service.get_user(current_user.organization_id, user_id)
    except UserNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead, summary="Update a user")
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: AuthenticatedUser = Depends(require_permission(USERS_WRITE)),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    try:
        user = await service.update_user(current_user.organization_id, user_id, payload)
    except UserNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return UserRead.model_validate(user)


@router.post("/{user_id}/roles/{role_name}", response_model=UserRead, summary="Assign a role to a user")
async def assign_role(
    user_id: uuid.UUID,
    role_name: str,
    current_user: AuthenticatedUser = Depends(require_permission(ROLES_MANAGE)),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    try:
        user = await service.assign_role(current_user.organization_id, user_id, role_name)
    except UserNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    except RoleNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Role '{role_name}' does not exist")
    return UserRead.model_validate(user)


@router.delete("/{user_id}/roles/{role_name}", response_model=UserRead, summary="Revoke a role from a user")
async def revoke_role(
    user_id: uuid.UUID,
    role_name: str,
    current_user: AuthenticatedUser = Depends(require_permission(ROLES_MANAGE)),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    try:
        user = await service.revoke_role(current_user.organization_id, user_id, role_name)
    except UserNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return UserRead.model_validate(user)
