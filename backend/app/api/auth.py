"""Authentication endpoints: login, refresh, logout, password reset."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.deps import get_current_user
from app.core.rate_limit import (
    check_login_lockout,
    check_password_reset_throttle,
    record_login_failure,
    record_password_reset_request,
    reset_login_attempts,
)
from app.schemas.auth import (
    AuthenticatedUser,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenPair,
)
from app.services.auth_service import (
    AuthService,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    InvalidResetTokenError,
    get_auth_service,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _client_ip(request: Request) -> str:
    """Prefers the first hop of X-Forwarded-For (set by a reverse proxy/load
    balancer in front of the API) over the raw socket peer, which behind
    such a proxy would just be the proxy itself for every request.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Authenticate and obtain an access/refresh token pair",
    description=(
        "Exchanges an email/password for a short-lived JWT access token and a "
        "long-lived, server-tracked refresh token. Returns 401 for any invalid "
        "credential without distinguishing 'wrong password' from 'no such user'. "
        "Returns 429 after repeated failures, tracked per-account *and* per-IP "
        "(Redis-backed) — either threshold locks out further attempts for a "
        "cooldown window, so both a targeted attack on one account and a "
        "credential-stuffing sweep across many accounts get stopped."
    ),
    responses={status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Too many failed login attempts"}},
)
async def login(
    payload: LoginRequest, request: Request, auth_service: AuthService = Depends(get_auth_service)
) -> TokenPair:
    client_ip = _client_ip(request)

    locked_for = await check_login_lockout(payload.email, client_ip)
    if locked_for is not None:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Too many failed login attempts. Try again in {locked_for} seconds.",
            headers={"Retry-After": str(locked_for)},
        )

    try:
        user = await auth_service.authenticate(payload.email, payload.password)
    except InvalidCredentialsError:
        await record_login_failure(payload.email, client_ip)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")

    await reset_login_attempts(payload.email, client_ip)
    return await auth_service.issue_token_pair(user)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Rotate a refresh token for a new access/refresh pair",
    description=(
        "The presented refresh token is revoked and replaced by a new one "
        "(rotation) — the response contains a *different* refresh token than "
        "the one submitted. Reuse of an already-rotated token revokes every "
        "session for that user, since it indicates the token was stolen."
    ),
)
async def refresh(payload: RefreshRequest, auth_service: AuthService = Depends(get_auth_service)) -> TokenPair:
    try:
        return await auth_service.rotate_refresh_token(payload.refresh_token)
    except InvalidRefreshTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid, expired, or already-used refresh token")


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke a refresh token",
    description=(
        "Ends the session tied to the given refresh token. The access token "
        "already issued for that session remains valid until it naturally "
        "expires (it is stateless and short-lived by design)."
    ),
)
async def logout(
    payload: LogoutRequest,
    _current_user: AuthenticatedUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    await auth_service.revoke_refresh_token(payload.refresh_token)
    return MessageResponse(message="Logged out")


@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    summary="Request a password reset",
    description=(
        "Always returns the same generic message regardless of whether the "
        "email is registered, to avoid leaking account existence via response "
        "differences. Throttled per-email (Redis-backed) since, unlike login, "
        "there's no password to brute-force here — the risk is spam/email-"
        "bombing a single address. No email/SMS provider is wired up yet — see "
        "AuthService.request_password_reset for the interim logging behavior."
    ),
    responses={status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Too many reset requests for this address"}},
)
async def request_password_reset(
    payload: PasswordResetRequest, auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    throttled_for = await check_password_reset_throttle(payload.email)
    if throttled_for is not None:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Too many reset requests for this address. Try again in {throttled_for} seconds.",
            headers={"Retry-After": str(throttled_for)},
        )

    await record_password_reset_request(payload.email)
    await auth_service.request_password_reset(payload.email)
    return MessageResponse(message="If that email is registered, a reset link has been sent.")


@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
    summary="Complete a password reset",
    description="Consumes a single-use reset token, sets the new password, and revokes all existing sessions.",
)
async def confirm_password_reset(
    payload: PasswordResetConfirm, auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    try:
        await auth_service.confirm_password_reset(payload.token, payload.new_password)
    except InvalidResetTokenError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token")
    return MessageResponse(message="Password has been reset. Please log in again.")
