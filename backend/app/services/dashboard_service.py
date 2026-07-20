"""Business logic for the Dashboard module.

Currently returns static dummy data. Will be backed by the Compound Risk
Engine and agent heartbeat store once those are implemented.
"""

from functools import lru_cache

from app.models.enums import AgentHealth, RiskLevel
from app.schemas.dashboard import AgentStatus, DashboardOverview, ZoneSummary
from app.utils.generators import utc_now


class DashboardService:
    """Aggregates zone risk summaries and agent health for the dashboard."""

    def __init__(self) -> None:
        self._zones = [
            ZoneSummary(
                zone_id="zone-001",
                zone_name="Loading Dock A",
                site_name="Plant 1",
                risk_score=72.5,
                risk_level=RiskLevel.HIGH,
                active_alerts=2,
            ),
            ZoneSummary(
                zone_id="zone-002",
                zone_name="Assembly Line 3",
                site_name="Plant 1",
                risk_score=34.0,
                risk_level=RiskLevel.MEDIUM,
                active_alerts=1,
            ),
            ZoneSummary(
                zone_id="zone-003",
                zone_name="Chemical Storage",
                site_name="Plant 2",
                risk_score=18.5,
                risk_level=RiskLevel.LOW,
                active_alerts=0,
            ),
        ]
        self._agents = [
            AgentStatus(name="vision_intelligence_agent", status=AgentHealth.HEALTHY, last_run_at=utc_now()),
            AgentStatus(name="sensor_intelligence_agent", status=AgentHealth.HEALTHY, last_run_at=utc_now()),
            AgentStatus(name="compound_risk_engine", status=AgentHealth.HEALTHY, last_run_at=utc_now()),
            AgentStatus(name="compliance_copilot", status=AgentHealth.DEGRADED, last_run_at=utc_now()),
            AgentStatus(name="emergency_response_agent", status=AgentHealth.HEALTHY, last_run_at=utc_now()),
            AgentStatus(name="incident_report_generator", status=AgentHealth.HEALTHY, last_run_at=utc_now()),
        ]

    def get_overview(self) -> DashboardOverview:
        return DashboardOverview(
            total_sites=2,
            total_zones=len(self._zones),
            total_cameras=6,
            total_active_alerts=sum(zone.active_alerts for zone in self._zones),
            zones=self._zones,
            agents=self._agents,
            generated_at=utc_now(),
        )


@lru_cache
def get_dashboard_service() -> DashboardService:
    return DashboardService()
