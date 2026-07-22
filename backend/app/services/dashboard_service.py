"""Dashboard aggregation: zone risk summaries + live agent health, drawn
from the real facility hierarchy, the Risk Intelligence Engine, and the
actual background agents running in this process (vision engine, sensor
simulator, compound risk engine, risk scheduler, compliance ingestion
worker). Only agents that genuinely exist are listed — the Emergency
Response Orchestrator will be added here once it exists, rather than
padding this list with a placeholder for capability that isn't built yet.
"""

import uuid
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.compliance.worker import get_ingestion_worker
from app.ai.compound_risk.scheduler import get_compound_risk_scheduler
from app.ai.risk.scheduler import get_risk_scheduler
from app.ai.sensors.scheduler import get_sensor_simulator
from app.ai.vision import get_vision_engine
from app.db.session import get_db
from app.models.alert import Alert
from app.models.camera import Camera
from app.models.enums import AgentHealth
from app.models.facility import Building, Site, Zone
from app.schemas.dashboard import AgentStatus, DashboardOverview, ZoneSummary
from app.services.risk_engine_service import RiskEngineService


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_overview(self, organization_id: uuid.UUID) -> DashboardOverview:
        total_sites = (await self._db.execute(select(func.count()).select_from(Site))).scalar_one()
        total_zones = (await self._db.execute(select(func.count()).select_from(Zone))).scalar_one()
        total_cameras = (await self._db.execute(select(func.count()).select_from(Camera))).scalar_one()

        zones = await self._build_zone_summaries(organization_id)

        return DashboardOverview(
            total_sites=total_sites,
            total_zones=total_zones,
            total_cameras=total_cameras,
            total_active_alerts=sum(z.active_alerts for z in zones),
            zones=zones,
            agents=self._agent_statuses(),
            generated_at=datetime.now(timezone.utc),
        )

    async def _build_zone_summaries(self, organization_id: uuid.UUID) -> list[ZoneSummary]:
        risk_engine = RiskEngineService(self._db)
        risk_result = await risk_engine.aggregate_organization_risk(organization_id)

        site_names: dict[uuid.UUID, str] = dict(
            (
                await self._db.execute(
                    select(Zone.id, Site.name)
                    .join(Building, Zone.building_id == Building.id)
                    .join(Site, Building.site_id == Site.id)
                )
            ).all()
        )

        alert_counts: dict[uuid.UUID, int] = dict(
            (
                await self._db.execute(
                    select(Alert.zone_id, func.count())
                    .where(Alert.acknowledged.is_(False))
                    .group_by(Alert.zone_id)
                )
            ).all()
        )

        return [
            ZoneSummary(
                zone_id=uuid.UUID(computation.zone_id),
                zone_name=computation.zone_name,
                site_name=site_names.get(uuid.UUID(computation.zone_id), "Unknown"),
                risk_score=computation.score,
                risk_level=computation.level,
                active_alerts=alert_counts.get(uuid.UUID(computation.zone_id), 0),
            )
            for computation in risk_result["zones"]
        ]

    def _agent_statuses(self) -> list[AgentStatus]:
        vision_stats = get_vision_engine().stats()
        if not vision_stats.running:
            vision_health = AgentHealth.OFFLINE
        elif vision_stats.provider is None:
            vision_health = AgentHealth.DEGRADED
        else:
            vision_health = AgentHealth.HEALTHY

        scheduler = get_risk_scheduler()
        risk_health = AgentHealth.HEALTHY if scheduler.running else AgentHealth.OFFLINE

        worker = get_ingestion_worker()
        compliance_health = AgentHealth.HEALTHY if worker.running else AgentHealth.OFFLINE

        sensor_sim = get_sensor_simulator()
        sensor_health = AgentHealth.HEALTHY if sensor_sim.running else AgentHealth.OFFLINE

        compound_risk_scheduler = get_compound_risk_scheduler()
        compound_risk_health = AgentHealth.HEALTHY if compound_risk_scheduler.running else AgentHealth.OFFLINE

        now = datetime.now(timezone.utc)
        return [
            AgentStatus(
                name="vision_intelligence_engine",
                status=vision_health,
                last_run_at=now if vision_stats.running else None,
            ),
            AgentStatus(
                name="sensor_iot_simulator", status=sensor_health, last_run_at=sensor_sim.last_tick_at
            ),
            AgentStatus(
                name="compound_risk_intelligence_engine",
                status=compound_risk_health,
                last_run_at=compound_risk_scheduler.last_tick_at,
            ),
            AgentStatus(
                name="risk_intelligence_engine", status=risk_health, last_run_at=scheduler.last_tick_at
            ),
            AgentStatus(
                name="compliance_copilot",
                status=compliance_health,
                last_run_at=now if worker.running else None,
            ),
        ]


def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(db)
