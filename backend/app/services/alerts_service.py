"""Alerts: the central notification sink — see app/models/alert.py's
module docstring for why every detection subsystem shares one table.

`create_alert` is called both from the API (manual alerts, `source=manual`)
and internally by other services (compound risk, permit agent, emergency
orchestrator, in later phases) — it takes a plain `AsyncSession` rather
than being bound to a request-scoped instance, so a background job can
call it through whatever session it already has open.
"""

import uuid
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.alert import Alert
from app.models.enums import AlertSeverity, AlertSource
from app.models.facility import Zone


class NotFoundError(Exception):
    pass


async def create_alert(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    zone_id: uuid.UUID,
    severity: AlertSeverity,
    message: str,
    source: AlertSource = AlertSource.MANUAL,
) -> Alert:
    alert = Alert(organization_id=organization_id, zone_id=zone_id, source=source, severity=severity, message=message)
    db.add(alert)
    await db.flush()
    return alert


class AlertsService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_alerts(self) -> tuple[list[Alert], dict[uuid.UUID, str]]:
        result = await self._db.execute(
            select(Alert, Zone.name).join(Zone, Alert.zone_id == Zone.id).order_by(Alert.created_at.desc())
        )
        rows = result.all()
        alerts = [row[0] for row in rows]
        zone_names = {row[0].zone_id: row[1] for row in rows}
        return alerts, zone_names

    async def create(
        self, *, organization_id: uuid.UUID, zone_id: uuid.UUID, severity: AlertSeverity, message: str, source: AlertSource
    ) -> Alert:
        if await self._db.get(Zone, zone_id) is None:
            raise NotFoundError()
        return await create_alert(
            self._db, organization_id=organization_id, zone_id=zone_id, severity=severity, message=message, source=source
        )

    async def acknowledge(self, alert_id: uuid.UUID, *, acknowledged_by: uuid.UUID) -> Alert:
        alert = await self._db.get(Alert, alert_id)
        if alert is None:
            raise NotFoundError()
        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now(timezone.utc)
        await self._db.flush()
        return alert


def get_alerts_service(db: AsyncSession = Depends(get_db)) -> AlertsService:
    return AlertsService(db)
