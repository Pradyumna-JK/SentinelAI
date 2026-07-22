"""FastAPI application entrypoint.

Responsibilities (and nothing else): logging bootstrap, app instantiation,
middleware, router registration, and lifecycle management. Business logic
lives in services; the PostgreSQL engine lives in app/core/database.py,
per-request sessions in app/db/session.py, and the remaining infrastructure
clients (Redis, MinIO) in app/database.
"""

import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.compliance.worker import get_ingestion_worker
from app.ai.compound_risk.scheduler import get_compound_risk_scheduler
from app.ai.risk.scheduler import get_risk_scheduler
from app.ai.sensors.scheduler import get_sensor_simulator
from app.ai.vision import get_vision_engine
from app.api import (
    alerts,
    auth,
    camera,
    compliance,
    compound_risk,
    dashboard,
    emergency,
    health,
    incidents,
    maintenance,
    permits,
    risk,
    roles,
    sensors,
    shifts,
    users,
    vision,
)
from app.api.facilities import buildings_router, factories_router, sites_router, zones_router
from app.core.config import get_settings
from app.core.database import check_database, dispose_engine
from app.core.logging import configure_logging, get_logger
from app.core.middleware import (
    OrganizationContextMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.database.redis import check_redis, close_redis
from app.database.storage import check_storage, ensure_bucket

settings = get_settings()
configure_logging(settings)
logger = get_logger("sentinel.startup")


async def _log_dependency_status() -> None:
    """Ping each dependency at startup and log the result.

    Deliberately non-fatal: in an orchestrated environment the API may come
    up moments before its dependencies. /health reports live status, and
    the orchestrator's readiness gating handles routing.
    """
    checks = {
        "postgres": asyncio.wait_for(check_database(), timeout=5.0),
        "redis": asyncio.wait_for(check_redis(), timeout=5.0),
        "minio": asyncio.wait_for(check_storage(), timeout=5.0),
    }
    results = await asyncio.gather(*checks.values(), return_exceptions=True)
    for name, result in zip(checks.keys(), results):
        if isinstance(result, Exception):
            logger.warning(
                "dependency_unavailable",
                dependency=name,
                error=f"{type(result).__name__}: {result}",
            )
        else:
            logger.info("dependency_connected", dependency=name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started_at = time.monotonic()
    logger.info(
        "application_starting",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    await _log_dependency_status()
    try:
        await asyncio.wait_for(ensure_bucket(), timeout=10.0)
        logger.info("storage_bucket_ready", bucket=settings.minio_bucket)
    except Exception as exc:  # noqa: BLE001 — storage may come up later
        logger.warning(
            "storage_bucket_unavailable",
            bucket=settings.minio_bucket,
            error=f"{type(exc).__name__}: {exc}",
        )

    # Model loading is I/O + graph-optimization heavy (seconds, not ms) but
    # still non-fatal if a weights file is missing — see engine.start().
    await get_vision_engine().start()
    await get_sensor_simulator().start()
    await get_compound_risk_scheduler().start()
    await get_risk_scheduler().start()
    await get_ingestion_worker().start()

    logger.info("application_started")
    yield

    logger.info("application_stopping")
    await get_ingestion_worker().stop()
    await get_risk_scheduler().stop()
    await get_compound_risk_scheduler().stop()
    await get_sensor_simulator().stop()
    await get_vision_engine().stop()
    await close_redis()
    await dispose_engine()
    logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    description=(
        "SentinelAI backend API — unified command center for industrial safety "
        "monitoring. Infrastructure foundation: PostgreSQL (SQLAlchemy 2 + "
        "Alembic), Redis, and MinIO object storage, fully containerized. "
        "Protected endpoints require a bearer access token from POST "
        "/auth/login — click Authorize above and paste the access_token."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware note: the last one added runs first, so CORS wraps everything
# else — preflight handling stays outermost, security headers land closest
# to the actual response. OrganizationContextMiddleware's position relative
# to the others doesn't matter functionally (it only needs to run before
# route *dependencies*, and middleware always wraps those regardless of
# ordering among themselves) — placed here for narrative order: log the
# request, resolve its tenant, then apply security headers.
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(OrganizationContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(factories_router)
app.include_router(sites_router)
app.include_router(buildings_router)
app.include_router(zones_router)
app.include_router(vision.router)
app.include_router(dashboard.router)
app.include_router(camera.router)
app.include_router(alerts.router)
app.include_router(risk.router)
app.include_router(incidents.router)
app.include_router(compliance.router)
app.include_router(sensors.router)
app.include_router(permits.router)
app.include_router(maintenance.router)
app.include_router(shifts.router)
app.include_router(compound_risk.router)
app.include_router(emergency.router)


@app.get("/", tags=["Root"], summary="Service info")
def read_root() -> dict:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
    }
