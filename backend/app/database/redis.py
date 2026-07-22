"""Async Redis client (cache, pub/sub, future rate limiting)."""

from redis.asyncio import Redis

from app.core.config import get_settings

_client: Redis | None = None


def get_redis() -> Redis:
    """Return the shared async Redis client (also usable as a FastAPI dependency)."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password.get_secret_value(),
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _client


async def check_redis() -> None:
    """Raise if Redis is unreachable. Used by /health."""
    await get_redis().ping()


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
