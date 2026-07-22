"""HTTP middleware: request correlation, structured access logging, and
baseline security headers.

Each request gets an ``X-Request-ID`` (honoring one supplied by an upstream
proxy/gateway), which is bound to structlog's contextvars so every log line
emitted while handling that request — from any module — carries the id.
"""

import time
import uuid

import jwt
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.core.tenancy import current_organization_id

logger = structlog.get_logger("sentinel.access")

# Probed by container orchestrators every few seconds; log at debug so they
# don't drown out real traffic.
_QUIET_PATHS = {"/health/live"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                client=request.client.host if request.client else None,
            )
            raise
        finally:
            structlog.contextvars.unbind_contextvars("request_id")

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log = logger.debug if request.url.path in _QUIET_PATHS else logger.info
        log(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
            client=request.client.host if request.client else None,
            request_id=request_id,
        )
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds baseline security response headers to every response.

    HSTS is only sent outside "development" — it instructs browsers to
    remember "always use HTTPS for this host" for a year, which is actively
    harmful on a plain-HTTP localhost dev server (the browser would then
    refuse to load it over http:// until the HSTS record expires or is
    manually cleared).
    """

    def __init__(self, app) -> None:
        super().__init__(app)
        self._send_hsts = get_settings().environment != "development"

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if self._send_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class OrganizationContextMiddleware(BaseHTTPMiddleware):
    """Resolves the current tenant (organization) from the request's JWT and
    makes it available for the rest of the request — to the automatic ORM
    filter (app/core/tenancy.py) and, via app/db/session.py, to PostgreSQL's
    Row-Level Security as a session variable.

    Deliberately NOT an authorization check: a missing or invalid token
    just means no tenant context gets set, and the request proceeds to
    whatever the route's own dependencies do about that (`get_current_user`
    still 401s as normal; public routes like /health and /auth/login don't
    need one at all). Keeping "is this token valid" as the single
    responsibility of `get_current_user` — not duplicated here — means
    there's exactly one place that decides whether a request is
    authenticated, which is what makes that decision auditable.

    The only source of truth for "which organization" is the token's own
    `org_id` claim, put there at login by the server itself
    (app/core/security.py's `create_access_token`). There is no code path
    anywhere that reads a client-supplied organization id from a header,
    query parameter, or request body — that's what makes cross-tenant
    impersonation structurally impossible rather than merely disallowed.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        organization_id = self._resolve_organization_id(request)
        token = current_organization_id.set(organization_id)
        try:
            return await call_next(request)
        finally:
            # Always reset, including on error — a contextvar left set would
            # be invisible to *this* request (Starlette gives each request
            # its own asyncio Task, so there's no cross-request leak risk
            # even without this), but resetting explicitly is what makes
            # that guarantee an assertion in the code rather than an
            # implicit property of the ASGI server's task-per-request
            # behavior.
            current_organization_id.reset(token)

    @staticmethod
    def _resolve_organization_id(request: Request) -> str | None:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return None
        raw_token = auth_header[len("bearer ") :].strip()
        try:
            payload = decode_access_token(raw_token)
        except jwt.PyJWTError:
            return None
        return payload.get("org_id")
