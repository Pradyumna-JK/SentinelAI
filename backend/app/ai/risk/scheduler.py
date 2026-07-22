"""Background risk-recomputation scheduler.

Runs on its own timer (app/core/config.py's risk_recompute_interval_seconds),
independent of any HTTP request — camera ingestion isn't wired to a live
feed yet (see app/ai/vision's architecture notes), so this is what keeps
risk scores current for zones that received events via POST /risk/ingest
between requests, and what turns hazard events into a continuous score
*history* rather than something only ever computed on read.

Tenant handling: rather than introduce a new cross-tenant bypass role
(a THIRD RLS exception alongside sentinel_auth, widening the exact attack
surface this whole architecture exists to narrow), the scheduler processes
one organization at a time, setting the identical `current_organization_id`
contextvar and Postgres session variable a real request's
OrganizationContextMiddleware + get_db() would — so every query it issues
is subject to the same ORM filter and RLS policy as a genuine user request
for that same org. The only step needing no tenant context is listing
organization ids at all, and that needs no bypass either: `organizations`
was deliberately never made TenantScoped (see app/models/organization.py)
— it's the tenant root, not a leaf under one, so no RLS policy exists on
it in the first place.

Also the Emergency Response Orchestrator's trigger point: a zone computed
as Critical here (whether from vision hazards, the Compound Risk
Intelligence Engine, or both) is handed to
app/services/emergency_response_service.py. Deliberately NOT hooked into
`RiskEngineService.compute_zone_risk()` itself — that method is also
called synchronously from read endpoints (GET /risk, the dashboard), and
an LLM-drafted incident summary has no business adding latency to a page
load. This background tick is the only place risk computation and
emergency response meet.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.tenancy import current_organization_id
from app.db.session import get_session_factory
from app.models.enums import RiskLevel
from app.models.organization import Organization
from app.models.risk import RiskEvent
from app.services.emergency_response_service import EmergencyResponseService
from app.services.risk_engine_service import RiskEngineService

logger = structlog.get_logger("sentinel.risk.scheduler")


class RiskScheduler:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._task: asyncio.Task | None = None
        self._last_tick_at: datetime | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop(), name="risk-scheduler")
        logger.info(
            "risk_scheduler_started", interval_seconds=self._settings.risk_recompute_interval_seconds
        )

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("risk_scheduler_stopped")

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def last_tick_at(self) -> datetime | None:
        return self._last_tick_at

    async def _loop(self) -> None:
        while True:
            try:
                await self._tick()
            except Exception:  # noqa: BLE001 — one bad tick must not kill the scheduler
                logger.exception("risk_scheduler_tick_failed")
            await asyncio.sleep(self._settings.risk_recompute_interval_seconds)

    async def _tick(self) -> None:
        session_factory = get_session_factory()
        lookback = datetime.now(timezone.utc) - timedelta(minutes=self._settings.risk_event_lookback_minutes)

        async with session_factory() as session:
            org_ids = list((await session.execute(select(Organization.id))).scalars())

        total_recomputed = 0
        for org_id in org_ids:
            token = current_organization_id.set(str(org_id))
            try:
                async with session_factory() as session:
                    await session.execute(
                        text("SELECT set_config('app.current_organization_id', :org_id, true)"),
                        {"org_id": str(org_id)},
                    )
                    zone_ids = list(
                        (
                            await session.execute(
                                select(RiskEvent.zone_id)
                                .where(RiskEvent.detected_at >= lookback)
                                .distinct()
                            )
                        ).scalars()
                    )
                    engine_service = RiskEngineService(session)
                    emergency_service = EmergencyResponseService(session)
                    for zone_id in zone_ids:
                        computation = await engine_service.compute_zone_risk(zone_id)
                        total_recomputed += 1
                        if computation.level == RiskLevel.CRITICAL:
                            # A bad emergency-response attempt must not lose
                            # the risk recompute this tick already did.
                            try:
                                await emergency_service.handle_critical_zone(
                                    organization_id=org_id, zone_id=zone_id, computation=computation
                                )
                            except Exception:  # noqa: BLE001
                                logger.exception(
                                    "emergency_response_trigger_failed", zone_id=str(zone_id)
                                )
                    await session.commit()
            except Exception:  # noqa: BLE001 — one org's failure must not block the rest
                logger.exception("risk_scheduler_org_failed", organization_id=str(org_id))
            finally:
                current_organization_id.reset(token)

        self._last_tick_at = datetime.now(timezone.utc)
        if total_recomputed:
            logger.info(
                "risk_scheduler_tick", organizations=len(org_ids), zones_recomputed=total_recomputed
            )


_scheduler: RiskScheduler | None = None


def get_risk_scheduler() -> RiskScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = RiskScheduler()
    return _scheduler
