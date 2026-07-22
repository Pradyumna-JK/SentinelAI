"""Role catalog endpoint.

Read-only: the 5 system roles are seeded via Alembic, not created through
the API. See app/services/role_service.py.
"""

from fastapi import APIRouter, Depends

from app.core.deps import require_permission
from app.core.permissions import ROLES_READ
from app.schemas.auth import AuthenticatedUser
from app.schemas.role import RoleListResponse, RoleRead
from app.services.role_service import RoleService, get_role_service

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=RoleListResponse, summary="List all roles and their permissions")
async def list_roles(
    _current_user: AuthenticatedUser = Depends(require_permission(ROLES_READ)),
    service: RoleService = Depends(get_role_service),
) -> RoleListResponse:
    roles = await service.list_roles()
    return RoleListResponse(items=[RoleRead.model_validate(r) for r in roles])
