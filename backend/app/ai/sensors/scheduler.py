"""Background sensor-reading simulator.

Same lifecycle and tenant-handling pattern as app/ai/risk/scheduler.py: one
always-on asyncio task, one organization processed at a time using the
identical `current_organization_id` contextvar + Postgres session variable
a real request would use — no cross-tenant bypass role needed here either,
for the same reason documented there.

Excursion state (whether a sensor is currently mid-spike, per
simulator.py) is kept in-process, keyed by sensor id — it's simulator
bookkeeping, not data anything else needs, so it doesn't get a DB column.
It resets on restart, which just means a restart can't interrupt an
in-progress excursion; harmless for a demo.
"""

import asyncio
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, text

from app.ai.sensors.simulator import is_anomaly, next_reading
from app.core.config import get_settings
from app.core.tenancy import current_organization_id
from app.db.session import get_session_factory
from app.models.organization import Organization
from app.models.sensor import SensorDevice, SensorReading

logger = structlog.get_logger("sentinel.sensors.scheduler")


class SensorSimulatorScheduler:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._task: asyncio.Task | None = None
        self._excursion_state: dict[uuid.UUID, bool] = {}
        self._last_tick_at: datetime | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop(), name="sensor-simulator")
        logger.info(
            "sensor_simulator_started", interval_seconds=self._settings.sensor_simulation_interval_seconds
        )

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("sensor_simulator_stopped")

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
            except Exception:  # noqa: BLE001 — one bad tick must not kill the simulator
                logger.exception("sensor_simulator_tick_failed")
            await asyncio.sleep(self._settings.sensor_simulation_interval_seconds)

    async def _tick(self) -> None:
        session_factory = get_session_factory()
        async with session_factory() as session:
            org_ids = list((await session.execute(select(Organization.id))).scalars())

        total_readings = 0
        for org_id in org_ids:
            token = current_organization_id.set(str(org_id))
            try:
                async with session_factory() as session:
                    await session.execute(
                        text("SELECT set_config('app.current_organization_id', :org_id, true)"),
                        {"org_id": str(org_id)},
                    )
                    devices = list((await session.execute(select(SensorDevice))).scalars())
                    for device in devices:
                        latest = (
                            await session.execute(
                                select(SensorReading)
                                .where(SensorReading.sensor_id == device.id)
                                .order_by(SensorReading.recorded_at.desc())
                                .limit(1)
                            )
                        ).scalar_one_or_none()
                        previous_value = latest.value if latest else (device.baseline_min + device.baseline_max) / 2

                        result = next_reading(
                            previous_value=previous_value,
                            baseline_min=device.baseline_min,
                            baseline_max=device.baseline_max,
                            in_excursion=self._excursion_state.get(device.id, False),
                        )
                        self._excursion_state[device.id] = result.in_excursion

                        session.add(
                            SensorReading(
                                organization_id=org_id,
                                sensor_id=device.id,
                                value=result.value,
                                is_anomaly=is_anomaly(result.value, device.baseline_min, device.baseline_max),
                                recorded_at=datetime.now(timezone.utc),
                            )
                        )
                        total_readings += 1
                    await session.commit()
            except Exception:  # noqa: BLE001 — one org's failure must not block the rest
                logger.exception("sensor_simulator_org_failed", organization_id=str(org_id))
            finally:
                current_organization_id.reset(token)

        self._last_tick_at = datetime.now(timezone.utc)
        if total_readings:
            logger.info("sensor_simulator_tick", organizations=len(org_ids), readings_written=total_readings)


_scheduler: SensorSimulatorScheduler | None = None


def get_sensor_simulator() -> SensorSimulatorScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = SensorSimulatorScheduler()
    return _scheduler
