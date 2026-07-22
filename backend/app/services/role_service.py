"""Role catalog — read-only from the API's perspective.

The 5 system roles are seeded once via Alembic (see
alembic/versions/*_seed_rbac.py); there is no create/delete-role endpoint
in scope, so this service only lists what already exists.
"""

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.role import Role


class RoleService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_roles(self) -> list[Role]:
        result = await self._db.execute(
            select(Role).options(selectinload(Role.permissions)).order_by(Role.name)
        )
        return list(result.scalars())


def get_role_service(db: AsyncSession = Depends(get_db)) -> RoleService:
    return RoleService(db)
