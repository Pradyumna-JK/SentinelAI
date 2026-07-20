"""FastAPI application entrypoint: app instantiation, middleware, and router registration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, camera, compliance, dashboard, incidents, risk
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "SentinelAI backend API — unified command center for industrial safety "
        "monitoring. AI agents (Vision, Sensor, Risk, Compliance, Emergency, "
        "Incident Reporting) are not yet wired in; endpoints currently return "
        "representative dummy data so the frontend and API contract can be built "
        "and tested in parallel."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(camera.router)
app.include_router(alerts.router)
app.include_router(risk.router)
app.include_router(incidents.router)
app.include_router(compliance.router)


@app.get("/", tags=["Root"], summary="Service info")
def read_root() -> dict:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
    }


@app.get("/health", tags=["Root"], summary="Health check")
def read_health() -> dict:
    return {"status": "ok"}
