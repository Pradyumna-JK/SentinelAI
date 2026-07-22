"""Password hashing (Argon2) and JWT encode/decode.

Argon2id via argon2-cffi — the OWASP-recommended KDF for password storage:
memory-hard (resistant to GPU/ASIC cracking) and, unlike bcrypt, has no
72-byte input truncation footgun. JWTs via PyJWT: short-lived, self-contained
access tokens carry resolved roles/permissions so authorization doesn't need
a DB round-trip per request. Refresh tokens are deliberately NOT JWTs —
they're opaque random strings whose SHA-256 hash is checked against
`refresh_tokens` (see app/services/auth_service.py), which is what makes
revocation and rotation possible at all for something with a 30-day lifetime.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except VerifyMismatchError:
        return False


def needs_rehash(hashed: str) -> bool:
    """True if `hashed` was made with weaker-than-current Argon2 parameters.

    Not wired into a call site yet (no endpoint re-saves a password outside
    of an explicit reset) — exposed for the natural place to use it: after a
    successful login, transparently re-hash and save if this returns True.
    """
    return _hasher.check_needs_rehash(hashed)


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def create_access_token(
    *,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
    roles: list[str],
    permissions: list[str],
) -> tuple[str, int]:
    """Returns (encoded_jwt, expires_in_seconds)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "org_id": str(organization_id),
        "roles": roles,
        "permissions": permissions,
        "type": TokenType.ACCESS.value,
        "iat": now,
        "exp": now + expires_delta,
        "jti": secrets.token_hex(16),
    }
    token = jwt.encode(payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError (or a subclass) on any invalid/expired/wrong-type token."""
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret_key.get_secret_value(), algorithms=[settings.jwt_algorithm])
    if payload.get("type") != TokenType.ACCESS.value:
        raise jwt.InvalidTokenError("Not an access token")
    return payload


def generate_refresh_token() -> str:
    """Opaque, high-entropy bearer token — not a JWT. Only its hash is stored."""
    return secrets.token_urlsafe(48)


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_opaque_token(raw_token: str) -> str:
    """SHA-256 hex digest, used for both refresh and password-reset tokens.

    Plain SHA-256 (not Argon2) is correct here, not a shortcut: these tokens
    are already ~256+ bits of CSPRNG entropy, so there's no offline
    brute-force risk to slow down the way there is for human-chosen
    passwords — a fast, deterministic digest is exactly what's needed to
    look the token up by hash in O(1) via a unique index.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
