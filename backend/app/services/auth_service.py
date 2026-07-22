"""Authentication: login, token issuance, refresh rotation, logout, and
password reset. Owns all token persistence (refresh + reset tokens) —
routers and other services never touch RefreshToken/PasswordResetToken
directly.

This service runs on its own DB session (`get_auth_db`), connected as the
BYPASSRLS `sentinel_auth` role, because every flow here is definitionally
pre-tenant: looking a user up by email at login, or by a stored token at
refresh/reset, happens *before* the organization context those RLS
policies key on can exist — establishing that context is precisely what
these flows produce. The role's grants are narrowed to auth-domain tables
only (users, tokens, RBAC read) so this exception can't become a general
RLS escape hatch; see the `auth_db_user` docstring in app/core/config.py
and the *_auth_role migration.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    generate_password_reset_token,
    generate_refresh_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.db.session import get_auth_db
from app.models.role import Role
from app.models.token import PasswordResetToken, RefreshToken
from app.models.user import User
from app.schemas.auth import TokenPair

logger = structlog.get_logger("sentinel.auth")


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


class InvalidResetTokenError(Exception):
    pass


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._settings = get_settings()

    async def _get_user_with_rbac(
        self, *, email: str | None = None, user_id: uuid.UUID | None = None
    ) -> User | None:
        """Fetch a user with roles+permissions eagerly loaded.

        Required in async SQLAlchemy: touching a lazy relationship outside
        of an explicit load (e.g. `user.roles` after a plain `session.get`)
        raises MissingGreenlet, so every path that needs RBAC data loads it
        up front via `selectinload`.
        """
        stmt = select(User).options(selectinload(User.roles).selectinload(Role.permissions))
        stmt = stmt.where(User.email == email.lower()) if email is not None else stmt.where(User.id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    def _issue_access_token(self, user: User) -> tuple[str, int]:
        role_names = [r.name for r in user.roles]
        permission_codes = sorted({p.code for r in user.roles for p in r.permissions})
        return create_access_token(
            user_id=user.id,
            organization_id=user.organization_id,
            roles=role_names,
            permissions=permission_codes,
        )

    async def authenticate(self, email: str, password: str) -> User:
        user = await self._get_user_with_rbac(email=email)
        # Constant-shape failure: verify against a dummy hash when the user
        # doesn't exist, so response timing doesn't reveal account existence.
        if user is None:
            verify_password(password, _DUMMY_HASH)
            raise InvalidCredentialsError()
        if not user.is_active or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        user.last_login_at = datetime.now(timezone.utc)
        await self._db.flush()
        return user

    async def issue_token_pair(self, user: User) -> TokenPair:
        access_token, expires_in = self._issue_access_token(user)
        raw_refresh = await self._create_refresh_token(user.id)
        return TokenPair(access_token=access_token, refresh_token=raw_refresh, expires_in=expires_in)

    async def _create_refresh_token(
        self, user_id: uuid.UUID, *, replaces: RefreshToken | None = None
    ) -> str:
        raw = generate_refresh_token()
        record = RefreshToken(
            user_id=user_id,
            token_hash=hash_opaque_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(days=self._settings.refresh_token_expire_days),
        )
        self._db.add(record)
        await self._db.flush()
        if replaces is not None:
            replaces.replaced_by_id = record.id
        return raw

    async def rotate_refresh_token(self, raw_refresh_token: str) -> TokenPair:
        token_hash = hash_opaque_token(raw_refresh_token)
        result = await self._db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        stored = result.scalar_one_or_none()

        if stored is None:
            raise InvalidRefreshTokenError()

        if stored.revoked_at is not None or stored.replaced_by_id is not None:
            # Reuse of an already-rotated/revoked token: treat it as
            # compromised and kill every session for this user, not just
            # this one token. Committed explicitly, right here: the router
            # converts the exception raised below into a 401, and get_auth_db()
            # rolls back the session on any exception leaving the request —
            # without this commit, the revocation itself would be undone by
            # that same rollback and never reach the database.
            logger.warning("refresh_token_reuse_detected", user_id=str(stored.user_id))
            await self.revoke_all_sessions(stored.user_id)
            await self._db.commit()
            raise InvalidRefreshTokenError()

        if stored.expires_at < datetime.now(timezone.utc):
            raise InvalidRefreshTokenError()

        user = await self._get_user_with_rbac(user_id=stored.user_id)
        if user is None or not user.is_active:
            raise InvalidRefreshTokenError()

        stored.revoked_at = datetime.now(timezone.utc)
        new_raw = await self._create_refresh_token(user.id, replaces=stored)
        access_token, expires_in = self._issue_access_token(user)
        return TokenPair(access_token=access_token, refresh_token=new_raw, expires_in=expires_in)

    async def revoke_refresh_token(self, raw_refresh_token: str) -> None:
        token_hash = hash_opaque_token(raw_refresh_token)
        result = await self._db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        stored = result.scalar_one_or_none()
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = datetime.now(timezone.utc)

    async def revoke_all_sessions(self, user_id: uuid.UUID) -> None:
        result = await self._db.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        )
        now = datetime.now(timezone.utc)
        for token in result.scalars():
            token.revoked_at = now

    async def request_password_reset(self, email: str) -> None:
        result = await self._db.execute(select(User).where(User.email == email.lower()))
        user = result.scalar_one_or_none()
        if user is None:
            return  # Never reveal whether the email is registered.

        raw = generate_password_reset_token()
        self._db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_opaque_token(raw),
                expires_at=datetime.now(timezone.utc)
                + timedelta(minutes=self._settings.password_reset_token_expire_minutes),
            )
        )
        await self._db.flush()
        # No email/SMS provider is configured (out of scope here) — log what
        # would be sent so the flow is testable end-to-end until real
        # delivery is wired up. This value is never returned in an HTTP
        # response.
        logger.info("password_reset_token_issued", user_id=str(user.id), email=user.email, raw_token=raw)

    async def confirm_password_reset(self, raw_token: str, new_password: str) -> None:
        token_hash = hash_opaque_token(raw_token)
        result = await self._db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        if stored is None or stored.used_at is not None or stored.expires_at < datetime.now(timezone.utc):
            raise InvalidResetTokenError()

        user = await self._db.get(User, stored.user_id)
        if user is None:
            raise InvalidResetTokenError()

        user.hashed_password = hash_password(new_password)
        stored.used_at = datetime.now(timezone.utc)
        # A password reset invalidates every existing session, not just the
        # device that requested it.
        await self.revoke_all_sessions(user.id)


# A real Argon2 hash of a random, never-issued password — verifying against
# it on "user not found" keeps login timing indistinguishable from a real
# password check instead of short-circuiting instantly.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(32))


def get_auth_service(db: AsyncSession = Depends(get_auth_db)) -> AuthService:
    return AuthService(db)
