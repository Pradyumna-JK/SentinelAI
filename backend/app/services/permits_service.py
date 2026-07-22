"""Work permits — see app/models/permit.py's module docstring."""

import uuid
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.enums import PermitStatus, PermitType
from app.models.facility import Zone
from app.models.permit import WorkPermit


class NotFoundError(Exception):
    pass


class PermitsService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_permits(self) -> list[tuple[WorkPermit, str]]:
        result = await self._db.execute(
            select(WorkPermit, Zone.name).join(Zone, WorkPermit.zone_id == Zone.id).order_by(WorkPermit.created_at.desc())
        )
        return list(result.all())

    async def list_active_for_zone(self, zone_id: uuid.UUID) -> list[WorkPermit]:
        """Used by the Compound Risk Intelligence Engine — active permits
        currently in effect for a zone, not the full historical list."""
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            select(WorkPermit).where(
                WorkPermit.zone_id == zone_id,
                WorkPermit.status == PermitStatus.ACTIVE,
                WorkPermit.valid_from <= now,
                WorkPermit.valid_to >= now,
            )
        )
        return list(result.scalars())

    async def create(
        self,
        *,
        organization_id: uuid.UUID,
        zone_id: uuid.UUID,
        permit_type: PermitType,
        description: str,
        valid_from: datetime,
        valid_to: datetime,
        issued_by: uuid.UUID,
    ) -> WorkPermit:
        if await self._db.get(Zone, zone_id) is None:
            raise NotFoundError()
        permit = WorkPermit(
            organization_id=organization_id,
            zone_id=zone_id,
            permit_type=permit_type,
            status=PermitStatus.ACTIVE,
            description=description,
            issued_by=issued_by,
            valid_from=valid_from,
            valid_to=valid_to,
        )
        self._db.add(permit)
        await self._db.flush()
        return permit

    async def close(self, permit_id: uuid.UUID) -> WorkPermit:
        permit = await self._db.get(WorkPermit, permit_id)
        if permit is None:
            raise NotFoundError()
        permit.status = PermitStatus.CLOSED
        await self._db.flush()
        return permit


def get_permits_service(db: AsyncSession = Depends(get_db)) -> PermitsService:
    return PermitsService(db)
