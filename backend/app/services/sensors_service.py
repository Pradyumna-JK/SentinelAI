"""IoT/SCADA sensor registry + readings.

`list_devices` returns each device's latest reading via a `DISTINCT ON`-style
query (Postgres `.distinct(column)`) rather than N+1 per-device lookups —
the same reasoning as every other list endpoint in this codebase that joins
for a denormalized display field (see alerts_service.py's zone-name join).
"""

import uuid
from datetime import datetime

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.facility import Zone
from app.models.sensor import SensorDevice, SensorReading


class NotFoundError(Exception):
    pass


class SensorsService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_devices(self) -> list[tuple[SensorDevice, str, SensorReading | None]]:
        device_rows = (
            await self._db.execute(
                select(SensorDevice, Zone.name).join(Zone, SensorDevice.zone_id == Zone.id).order_by(SensorDevice.name)
            )
        ).all()

        latest_readings = (
            await self._db.execute(
                select(SensorReading)
                .distinct(SensorReading.sensor_id)
                .order_by(SensorReading.sensor_id, SensorReading.recorded_at.desc())
            )
        ).scalars()
        latest_by_sensor = {r.sensor_id: r for r in latest_readings}

        return [(device, zone_name, latest_by_sensor.get(device.id)) for device, zone_name in device_rows]

    async def get_history(self, sensor_id: uuid.UUID, *, since: datetime) -> list[SensorReading]:
        if await self._db.get(SensorDevice, sensor_id) is None:
            raise NotFoundError()
        result = await self._db.execute(
            select(SensorReading)
            .where(SensorReading.sensor_id == sensor_id, SensorReading.recorded_at >= since)
            .order_by(SensorReading.recorded_at)
        )
        return list(result.scalars())

    async def create(
        self,
        *,
        organization_id: uuid.UUID,
        zone_id: uuid.UUID,
        sensor_type,
        name: str,
        unit: str,
        baseline_min: float,
        baseline_max: float,
    ) -> SensorDevice:
        if await self._db.get(Zone, zone_id) is None:
            raise NotFoundError()
        device = SensorDevice(
            organization_id=organization_id,
            zone_id=zone_id,
            sensor_type=sensor_type,
            name=name,
            unit=unit,
            baseline_min=baseline_min,
            baseline_max=baseline_max,
        )
        self._db.add(device)
        await self._db.flush()
        return device


def get_sensors_service(db: AsyncSession = Depends(get_db)) -> SensorsService:
    return SensorsService(db)
