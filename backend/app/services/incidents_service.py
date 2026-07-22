"""Incident reports: draft -> approved -> closed lifecycle.

`create` is deliberately usable both from the API (a manually-filed
incident) and — from Phase 6 onward — the Emergency Response Orchestrator,
which auto-drafts a report's `title`/`summary`/`detail` from an LLM call
constrained to a supplied evidence bundle, then calls this same service to
persist it. No separate "auto-created incident" code path.
"""

import uuid
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.enums import AlertSeverity, IncidentStatus
from app.models.facility import Zone
from app.models.incident import Incident


class NotFoundError(Exception):
    pass


class InvalidTransitionError(Exception):
    """Attempted an illegal status transition (e.g. closing a draft)."""


class IncidentsService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_incidents(self) -> tuple[list[Incident], dict[uuid.UUID, str]]:
        result = await self._db.execute(
            select(Incident, Zone.name).join(Zone, Incident.zone_id == Zone.id).order_by(Incident.created_at.desc())
        )
        rows = result.all()
        incidents = [row[0] for row in rows]
        zone_names = {row[0].zone_id: row[1] for row in rows}
        return incidents, zone_names

    async def get(self, incident_id: uuid.UUID) -> Incident:
        incident = await self._db.get(Incident, incident_id)
        if incident is None:
            raise NotFoundError()
        return incident

    async def create(
        self,
        *,
        organization_id: uuid.UUID,
        zone_id: uuid.UUID,
        title: str,
        category: str,
        severity: AlertSeverity,
        summary: str,
        detail: dict,
        created_by: uuid.UUID | None,
    ) -> Incident:
        if await self._db.get(Zone, zone_id) is None:
            raise NotFoundError()
        incident = Incident(
            organization_id=organization_id,
            zone_id=zone_id,
            title=title,
            category=category,
            severity=severity,
            status=IncidentStatus.DRAFT,
            summary=summary,
            detail=detail,
            created_by=created_by,
        )
        self._db.add(incident)
        await self._db.flush()
        return incident

    async def approve(self, incident_id: uuid.UUID, *, approved_by: uuid.UUID) -> Incident:
        incident = await self.get(incident_id)
        if incident.status != IncidentStatus.DRAFT:
            raise InvalidTransitionError()
        incident.status = IncidentStatus.APPROVED
        incident.approved_by = approved_by
        incident.approved_at = datetime.now(timezone.utc)
        await self._db.flush()
        return incident

    async def close(self, incident_id: uuid.UUID) -> Incident:
        incident = await self.get(incident_id)
        if incident.status != IncidentStatus.APPROVED:
            raise InvalidTransitionError()
        incident.status = IncidentStatus.CLOSED
        incident.closed_at = datetime.now(timezone.utc)
        await self._db.flush()
        return incident


def get_incidents_service(db: AsyncSession = Depends(get_db)) -> IncidentsService:
    return IncidentsService(db)
