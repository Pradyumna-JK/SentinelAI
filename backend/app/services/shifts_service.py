"""Shifts and changeover events — see app/models/shift.py's module docstring.

`create_changeover` derives `factory_id` from the referenced `Shift` row
rather than accepting it from the caller — a shift already belongs to
exactly one factory, so asking for it twice would just be a second place
for the two values to disagree.
"""

import uuid
from datetime import datetime, time

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.facility import Factory
from app.models.shift import Shift, ShiftChangeoverEvent


class NotFoundError(Exception):
    pass


class ShiftsService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_shifts(self) -> list[Shift]:
        result = await self._db.execute(select(Shift).order_by(Shift.start_time))
        return list(result.scalars())

    async def create_shift(
        self, *, organization_id: uuid.UUID, factory_id: uuid.UUID, name: str, start_time: time, end_time: time
    ) -> Shift:
        if await self._db.get(Factory, factory_id) is None:
            raise NotFoundError()
        shift = Shift(
            organization_id=organization_id, factory_id=factory_id, name=name,
            start_time=start_time, end_time=end_time,
        )
        self._db.add(shift)
        await self._db.flush()
        return shift

    async def list_changeovers(self) -> list[tuple[ShiftChangeoverEvent, str]]:
        result = await self._db.execute(
            select(ShiftChangeoverEvent, Shift.name)
            .join(Shift, ShiftChangeoverEvent.shift_id == Shift.id)
            .order_by(ShiftChangeoverEvent.changeover_at.desc())
        )
        return list(result.all())

    async def most_recent_changeover(self, factory_id: uuid.UUID) -> ShiftChangeoverEvent | None:
        """Used by the Compound Risk Intelligence Engine to check proximity
        to the last changeover for a zone's factory."""
        result = await self._db.execute(
            select(ShiftChangeoverEvent)
            .where(ShiftChangeoverEvent.factory_id == factory_id)
            .order_by(ShiftChangeoverEvent.changeover_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_changeover(self, *, organization_id: uuid.UUID, shift_id: uuid.UUID, changeover_at: datetime) -> ShiftChangeoverEvent:
        shift = await self._db.get(Shift, shift_id)
        if shift is None:
            raise NotFoundError()
        event = ShiftChangeoverEvent(
            organization_id=organization_id, factory_id=shift.factory_id,
            shift_id=shift_id, changeover_at=changeover_at,
        )
        self._db.add(event)
        await self._db.flush()
        return event


def get_shifts_service(db: AsyncSession = Depends(get_db)) -> ShiftsService:
    return ShiftsService(db)
