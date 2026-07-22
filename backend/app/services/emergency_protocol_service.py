"""Emergency protocol registry — see app/models/emergency_protocol.py."""

import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.emergency_protocol import EmergencyProtocol


class EmergencyProtocolService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_protocols(self) -> list[EmergencyProtocol]:
        result = await self._db.execute(select(EmergencyProtocol).order_by(EmergencyProtocol.hazard_type))
        return list(result.scalars())

    async def create(
        self, *, organization_id: uuid.UUID, hazard_type: str, steps: list[str], evacuation_route: str | None
    ) -> EmergencyProtocol:
        protocol = EmergencyProtocol(
            organization_id=organization_id, hazard_type=hazard_type, steps=steps, evacuation_route=evacuation_route
        )
        self._db.add(protocol)
        await self._db.flush()
        return protocol


def get_emergency_protocol_service(db: AsyncSession = Depends(get_db)) -> EmergencyProtocolService:
    return EmergencyProtocolService(db)
