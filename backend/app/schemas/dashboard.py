import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AgentHealth, RiskLevel


class ZoneSummary(BaseModel):
    zone_id: uuid.UUID = Field(..., description="Unique identifier of the zone")
    zone_name: str = Field(..., description="Human-readable zone name")
    site_name: str = Field(..., description="Name of the site the zone belongs to")
    risk_score: float = Field(..., ge=0, le=100, description="Current compound risk score (0-100)")
    risk_level: RiskLevel = Field(..., description="Categorical risk level derived from the score")
    active_alerts: int = Field(..., ge=0, description="Number of unacknowledged alerts in this zone")


class AgentStatus(BaseModel):
    name: str = Field(..., description="Machine-readable agent identifier")
    status: AgentHealth = Field(..., description="Current health/heartbeat status of the agent")
    last_run_at: datetime | None = Field(
        None, description="Timestamp of the agent's last successful run, or null if it hasn't run yet"
    )


class DashboardOverview(BaseModel):
    total_sites: int = Field(..., ge=0)
    total_zones: int = Field(..., ge=0)
    total_cameras: int = Field(..., ge=0)
    total_active_alerts: int = Field(..., ge=0)
    zones: list[ZoneSummary]
    agents: list[AgentStatus]
    generated_at: datetime = Field(..., description="Timestamp this snapshot was generated")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_sites": 2,
                "total_zones": 3,
                "total_cameras": 6,
                "total_active_alerts": 3,
                "zones": [
                    {
                        "zone_id": "b3f2a1e0-0000-4000-8000-000000000000",
                        "zone_name": "Loading Dock A",
                        "site_name": "Plant 1",
                        "risk_score": 72.5,
                        "risk_level": "High",
                        "active_alerts": 2,
                    }
                ],
                "agents": [
                    {
                        "name": "vision_intelligence_engine",
                        "status": "Healthy",
                        "last_run_at": "2026-07-20T10:15:03Z",
                    }
                ],
                "generated_at": "2026-07-20T10:15:04Z",
            }
        }
    }
