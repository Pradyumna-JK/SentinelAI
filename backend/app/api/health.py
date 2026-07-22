"""Health endpoints.

- ``GET /health/live`` — liveness: the process is up and serving. Used by the
  container HEALTHCHECK; deliberately touches no dependencies so a database
  outage never causes the orchestrator to restart-loop the API.
- ``GET /health``      — readiness: probes PostgreSQL, Redis, and MinIO
  concurrently (2s timeout each) and reports per-component status, uptime,
  and version. Returns 503 when degraded so load balancers can act on it.
"""

import asyncio
import time
from collections.abc import Awaitable

import structlog
from fastapi import APIRouter, Request, Response, status

from app.ai.compliance.vectorstore import check_vectorstore
from app.core.config import get_settings
from app.core.database import check_database
from app.database.redis import check_redis
from app.database.storage import check_storage
from app.schemas.health import ComponentCheck, HealthResponse, LivenessResponse

router = APIRouter(prefix="/health", tags=["Health"])
logger = structlog.get_logger("sentinel.health")

_PROBE_TIMEOUT_SECONDS = 2.0


async def _probe(name: str, check: Awaitable[None]) -> ComponentCheck:
    start = time.perf_counter()
    try:
        await asyncio.wait_for(check, timeout=_PROBE_TIMEOUT_SECONDS)
    except Exception as exc:  # noqa: BLE001 — any failure means "down"
        logger.warning("health_check_failed", component=name, error=f"{type(exc).__name__}: {exc}")
        return ComponentCheck(status="down", detail=f"{type(exc).__name__}: {exc}"[:200])
    latency_ms = round((time.perf_counter() - start) * 1000, 1)
    return ComponentCheck(status="up", latency_ms=latency_ms)


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description="Process-level liveness only; never touches external dependencies.",
)
def liveness() -> LivenessResponse:
    return LivenessResponse()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Readiness / dependency health",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def health(request: Request, response: Response) -> HealthResponse:
    settings = get_settings()

    database, redis, storage, vectorstore = await asyncio.gather(
        _probe("database", check_database()),
        _probe("redis", check_redis()),
        _probe("storage", check_storage()),
        _probe("vectorstore", check_vectorstore()),
    )

    all_up = all(c.status == "up" for c in (database, redis, storage, vectorstore))
    if not all_up:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="healthy" if all_up else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=round(time.monotonic() - request.app.state.started_at, 1),
        database=database,
        redis=redis,
        storage=storage,
        vectorstore=vectorstore,
    )
