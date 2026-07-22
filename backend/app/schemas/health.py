from typing import Literal

from pydantic import BaseModel, Field


class ComponentCheck(BaseModel):
    status: Literal["up", "down"] = Field(..., description="Whether the dependency responded")
    latency_ms: float | None = Field(None, description="Round-trip time of the probe, when up")
    detail: str | None = Field(None, description="Truncated error description, when down")


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"] = Field(
        ..., description="'healthy' only when every dependency is up"
    )
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment name")
    uptime_seconds: float = Field(..., ge=0, description="Seconds since application startup")
    database: ComponentCheck
    redis: ComponentCheck
    storage: ComponentCheck
    vectorstore: ComponentCheck

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "0.2.0",
                "environment": "production",
                "uptime_seconds": 4213.7,
                "database": {"status": "up", "latency_ms": 2.4, "detail": None},
                "redis": {"status": "up", "latency_ms": 0.8, "detail": None},
                "storage": {"status": "up", "latency_ms": 5.1, "detail": None},
                "vectorstore": {"status": "up", "latency_ms": 3.2, "detail": None},
            }
        }
    }


class LivenessResponse(BaseModel):
    status: Literal["alive"] = "alive"
