"""User account management: organization-scoped CRUD and role assignment."""

import uuid

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class EmailAlreadyExistsError(Exception):
    pass


class RoleNotFoundError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_users(
        self, organization_id: uuid.UUID, *, page: int, limit: int
    ) -> tuple[list[User], int]:
        total = (
            await self._db.execute(
                select(func.count()).select_from(User).where(User.organization_id == organization_id)
            )
        ).scalar_one()

        result = await self._db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.organization_id == organization_id)
            .order_by(User.created_at)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return list(result.scalars()), total

    async def get_user(self, organization_id: uuid.UUID, user_id: uuid.UUID) -> User:
        result = await self._db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id, User.organization_id == organization_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise UserNotFoundError()
        return user

    async def create_user(self, organization_id: uuid.UUID, payload: UserCreate) -> User:
        existing = await self._db.execute(select(User).where(User.email == payload.email.lower()))
        if existing.scalar_one_or_none() is not None:
            raise EmailAlreadyExistsError()

        roles: list[Role] = []
        if payload.role_names:
            result = await self._db.execute(select(Role).where(Role.name.in_(payload.role_names)))
            roles = list(result.scalars())
            if len(roles) != len(set(payload.role_names)):
                raise RoleNotFoundError()

        user = User(
            organization_id=organization_id,
            email=payload.email.lower(),
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            roles=roles,
        )
        self._db.add(user)
        await self._db.flush()
        return user

    async def update_user(self, organization_id: uuid.UUID, user_id: uuid.UUID, payload: UserUpdate) -> User:
        user = await self.get_user(organization_id, user_id)
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.is_active is not None:
            user.is_active = payload.is_active
        await self._db.flush()
        return user

    async def assign_role(self, organization_id: uuid.UUID, user_id: uuid.UUID, role_name: str) -> User:
        user = await self.get_user(organization_id, user_id)
        result = await self._db.execute(select(Role).where(Role.name == role_name))
        role = result.scalar_one_or_none()
        if role is None:
            raise RoleNotFoundError()
        if role not in user.roles:
            user.roles.append(role)
            await self._db.flush()
        return user

    async def revoke_role(self, organization_id: uuid.UUID, user_id: uuid.UUID, role_name: str) -> User:
        user = await self.get_user(organization_id, user_id)
        user.roles = [r for r in user.roles if r.name != role_name]
        await self._db.flush()
        return user


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)
