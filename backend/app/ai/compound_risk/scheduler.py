"""Background Compound Risk Intelligence Engine.

Same lifecycle and per-org tenant-handling pattern as every other scheduler
in this codebase (app/ai/risk/scheduler.py, app/ai/sensors/scheduler.py):
one always-on asyncio task, one organization at a time via the identical
`current_organization_id` contextvar + Postgres session variable a real
request would use.

Every zone is checked every tick (demo scale — a handful of zones), and any
finding with nonzero severity is persisted as a `RiskEvent` with
`camera_id="compound-risk-engine"` — a synthetic sentinel value, since this
finding has no real camera behind it (see app/models/risk.py's own
docstring anticipating exactly this: "a future non-vision hazard source...
wouldn't have a bounding box at all"). That event then flows through the
*existing* Risk Intelligence Engine's time-decay/compound-aggregation math
the next time app/ai/risk/scheduler.py ticks — no parallel scoring system.
"""

import asyncio
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, text

from app.ai.compound_risk.graph import run_for_zone
from app.core.config import get_settings
from app.core.tenancy import current_organization_id
from app.db.session import get_session_factory
from app.models.facility import Zone
from app.models.organization import Organization
from app.models.risk import RiskEvent

logger = structlog.get_logger("sentinel.compound_risk.scheduler")

_SYNTHETIC_CAMERA_ID = "compound-risk-engine"


class CompoundRiskScheduler:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._task: asyncio.Task | None = None
        self._last_tick_at: datetime | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop(), name="compound-risk-scheduler")
        logger.info(
            "compound_risk_scheduler_started",
            interval_seconds=self._settings.compound_risk_recompute_interval_seconds,
        )

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("compound_risk_scheduler_stopped")

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
                logger.exception("compound_risk_scheduler_tick_failed")
            await asyncio.sleep(self._settings.compound_risk_recompute_interval_seconds)

    async def _tick(self) -> None:
        session_factory = get_session_factory()
        async with session_factory() as session:
            org_ids = list((await session.execute(select(Organization.id))).scalars())

        total_events = 0
        total_combined = 0
        for org_id in org_ids:
            token = current_organization_id.set(str(org_id))
            try:
                async with session_factory() as session:
                    await session.execute(
                        text("SELECT set_config('app.current_organization_id', :org_id, true)"),
                        {"org_id": str(org_id)},
                    )
                    zone_ids = list((await session.execute(select(Zone.id))).scalars())
                    for zone_id in zone_ids:
                        finding = await run_for_zone(session, zone_id=zone_id)
                        if finding.severity <= 0:
                            continue
                        session.add(
                            RiskEvent(
                                organization_id=org_id,
                                zone_id=zone_id,
                                camera_id=_SYNTHETIC_CAMERA_ID,
                                hazard_class=finding.hazard_class,
                                confidence=1.0,
                                severity=finding.severity,
                                detected_at=datetime.now(timezone.utc),
                            )
                        )
                        total_events += 1
                        if finding.combined:
                            total_combined += 1
                            logger.info(
                                "compound_risk_detected",
                                organization_id=str(org_id),
                                zone_id=str(zone_id),
                                hazard_class=finding.hazard_class,
                                severity=finding.severity,
                                signals=finding.dominant_signals,
                                rationale=finding.rationale,
                            )
                    await session.commit()
            except Exception:  # noqa: BLE001 — one org's failure must not block the rest
                logger.exception("compound_risk_scheduler_org_failed", organization_id=str(org_id))
            finally:
                current_organization_id.reset(token)

        self._last_tick_at = datetime.now(timezone.utc)
        if total_events:
            logger.info(
                "compound_risk_scheduler_tick",
                organizations=len(org_ids),
                events_written=total_events,
                compound_findings=total_combined,
            )


_scheduler: CompoundRiskScheduler | None = None


def get_compound_risk_scheduler() -> CompoundRiskScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = CompoundRiskScheduler()
    return _scheduler
