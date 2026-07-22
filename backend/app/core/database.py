"""PostgreSQL engine: creation, pooling, health check, and disposal.

Session management (``async_sessionmaker`` + the FastAPI ``get_db``
dependency) lives in ``app/db/session.py``, which imports ``get_engine``
from here — this module owns only the engine's lifecycle, nothing else.

The engine is a lazily-created module-level singleton: importing this module
(e.g. from Alembic tooling or a unit test) never opens a connection by
itself, and every request/probe within one process shares the same
connection pool instead of opening a new one per call.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_auth_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Return the process-wide async engine, creating it on first use.

    Deliberately connects with ``settings.app_database_url``, not
    ``settings.database_url`` — the app runs as an unprivileged, RLS-
    restricted role, while migrations (alembic/env.py) use the owning role
    that created the schema. See the ``app_db_user`` field docstring in
    app/core/config.py for why this split exists.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.app_database_url,
            pool_pre_ping=True,  # discard dead connections instead of erroring
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            echo=settings.db_echo,
        )
    return _engine


def get_auth_engine() -> AsyncEngine:
    """Separate engine for AuthService's pre-authentication lookups only —
    see the ``auth_db_user`` field docstring in app/core/config.py. Kept
    entirely separate from ``get_engine()`` (its own pool, its own role) so
    it's structurally impossible for some other service to accidentally
    import and reuse the RLS-bypassing connection for anything else.
    """
    global _auth_engine
    if _auth_engine is None:
        settings = get_settings()
        _auth_engine = create_async_engine(
            settings.auth_database_url,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=5,
            echo=settings.db_echo,
        )
    return _auth_engine


async def check_database() -> None:
    """Raise if PostgreSQL is unreachable. Consumed by ``GET /health``."""
    async with get_engine().connect() as conn:
        await conn.execute(text("SELECT 1"))


async def dispose_engine() -> None:
    """Close the connection pools. Called from the app's shutdown lifespan."""
    global _engine, _auth_engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
    if _auth_engine is not None:
        await _auth_engine.dispose()
        _auth_engine = None
