"""Async session factory and the FastAPI DB-session dependency.

Kept separate from ``app/core/database.py`` (engine lifecycle) so each
module has exactly one reason to change: the engine's connection/pooling
config, versus how individual request sessions are scoped and cleaned up.
"""

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_auth_engine, get_engine
from app.core.tenancy import current_organization_id

_session_factory: async_sessionmaker[AsyncSession] | None = None
_auth_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the process-wide session factory, creating it on first use."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


def get_auth_session_factory() -> async_sessionmaker[AsyncSession]:
    """Session factory for AuthService's pre-authentication lookups.

    Not a FastAPI dependency, unlike ``get_db`` — it's opened internally by
    AuthService itself (see app/services/auth_service.py), not injected
    into routers, since no router should ever hold this session directly.
    No tenant ``set_config`` call here: the whole point of this connection
    is to run *before* a tenant is known, via a role with BYPASSRLS rather
    than via the session-variable mechanism the regular path uses.
    """
    global _auth_session_factory
    if _auth_session_factory is None:
        _auth_session_factory = async_sessionmaker(
            bind=get_auth_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _auth_session_factory


async def get_auth_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency for AuthService ONLY — see get_auth_session_factory.

    Same commit/rollback contract as ``get_db``, but bound to the
    RLS-bypassing auth engine and deliberately without the tenant
    ``set_config`` call. Nothing outside app/services/auth_service.py
    should ever depend on this.
    """
    async with get_auth_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding one session per request.

    Usage: ``session: AsyncSession = Depends(get_db)`` in a router. Commits
    once the route handler returns successfully; rolls back on any exception
    raised while the session is in use. The session is always closed via the
    ``async with`` block regardless of outcome.

    If ``OrganizationContextMiddleware`` resolved a tenant for this request,
    that value is pushed into Postgres as a transaction-local session
    variable (``set_config(..., is_local=true)``) *before* any other query
    runs on this session — this is what feeds app/core/tenancy.py's
    application-layer filter into the database's own Row-Level Security
    policies (see alembic/versions/*_tenant_isolation_rls.py), so tenant
    isolation holds even for a query that somehow bypasses the ORM filter.
    ``is_local=true`` (the third argument to ``set_config``) scopes the
    setting to the current transaction, which lines up exactly with this
    session's lifetime — no separate reset is needed, Postgres discards it
    at the commit/rollback below.
    """
    async with get_session_factory()() as session:
        try:
            tenant_id = current_organization_id.get()
            if tenant_id is not None:
                await session.execute(
                    text("SELECT set_config('app.current_organization_id', :tenant_id, true)"),
                    {"tenant_id": tenant_id},
                )
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
