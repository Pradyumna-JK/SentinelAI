"""Redis-backed rate limiting for authentication-adjacent endpoints.

Fixed-window counters (INCR, with EXPIRE set only on the first hit in a
window) — Redis' INCR is already atomic, so this needs no locking or Lua
script, and a fixed window is more than sufficient for throttling brute
force / spam at this scale (a token bucket or sliding window would be
over-engineering for what's actually needed here).

Two independent uses:
- login lockout: keyed by *both* account (email) and client IP, so either
  a targeted attack on one account or a credential-stuffing sweep across
  many accounts from one source gets stopped.
- password-reset throttle: keyed by account only — this endpoint has no
  password to brute-force, the risk is spam/email-bombing a single address.
"""

from app.core.config import get_settings
from app.database.redis import get_redis


async def _remaining_lockout_seconds(key: str, limit: int) -> int | None:
    redis = get_redis()
    count = await redis.get(key)
    if count is not None and int(count) >= limit:
        ttl = await redis.ttl(key)
        return max(ttl, 1)
    return None


async def _increment(key: str, window_seconds: int) -> None:
    redis = get_redis()
    new_count = await redis.incr(key)
    if new_count == 1:
        await redis.expire(key, window_seconds)


def _account_key(email: str) -> str:
    return f"auth:fail:acct:{email.lower()}"


def _ip_key(ip: str) -> str:
    return f"auth:fail:ip:{ip}"


def _reset_request_key(email: str) -> str:
    return f"auth:reset:acct:{email.lower()}"


async def check_login_lockout(email: str, client_ip: str) -> int | None:
    """Returns seconds remaining if the account or the client IP is locked out."""
    settings = get_settings()
    for key in (_account_key(email), _ip_key(client_ip)):
        remaining = await _remaining_lockout_seconds(key, settings.max_login_attempts)
        if remaining is not None:
            return remaining
    return None


async def record_login_failure(email: str, client_ip: str) -> None:
    settings = get_settings()
    window_seconds = settings.login_lockout_minutes * 60
    await _increment(_account_key(email), window_seconds)
    await _increment(_ip_key(client_ip), window_seconds)


async def reset_login_attempts(email: str, client_ip: str) -> None:
    """Called on successful login so a past near-miss doesn't linger."""
    redis = get_redis()
    await redis.delete(_account_key(email), _ip_key(client_ip))


async def check_password_reset_throttle(email: str) -> int | None:
    """Returns seconds remaining if this address has requested too many resets."""
    settings = get_settings()
    return await _remaining_lockout_seconds(_reset_request_key(email), settings.max_password_reset_requests)


async def record_password_reset_request(email: str) -> None:
    settings = get_settings()
    window_seconds = settings.password_reset_throttle_minutes * 60
    await _increment(_reset_request_key(email), window_seconds)
