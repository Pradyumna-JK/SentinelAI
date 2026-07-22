"""Equipment registry + maintenance activity — see app/models/maintenance.py."""

import uuid
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.enums import EquipmentCriticality, MaintenanceStatus
from app.models.facility import Zone
from app.models.maintenance import Equipment, MaintenanceRecord


class NotFoundError(Exception):
    pass


class MaintenanceService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------- equipment

    async def list_equipment(self) -> list[tuple[Equipment, str]]:
        result = await self._db.execute(
            select(Equipment, Zone.name).join(Zone, Equipment.zone_id == Zone.id).order_by(Equipment.name)
        )
        return list(result.all())

    async def create_equipment(
        self, *, organization_id: uuid.UUID, zone_id: uuid.UUID, name: str, equipment_type: str,
        criticality: EquipmentCriticality,
    ) -> Equipment:
        if await self._db.get(Zone, zone_id) is None:
            raise NotFoundError()
        equipment = Equipment(
            organization_id=organization_id, zone_id=zone_id, name=name,
            equipment_type=equipment_type, criticality=criticality,
        )
        self._db.add(equipment)
        await self._db.flush()
        return equipment

    # ------------------------------------------------------------- maintenance records

    async def list_records(self) -> list[tuple[MaintenanceRecord, str, uuid.UUID]]:
        result = await self._db.execute(
            select(MaintenanceRecord, Equipment.name, Equipment.zone_id)
            .join(Equipment, MaintenanceRecord.equipment_id == Equipment.id)
            .order_by(MaintenanceRecord.window_start.desc())
        )
        return list(result.all())

    async def list_active_for_zone(self, zone_id: uuid.UUID) -> list[MaintenanceRecord]:
        """Used by the Compound Risk Intelligence Engine — maintenance
        records currently in their active window for equipment in a zone."""
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            select(MaintenanceRecord)
            .join(Equipment, MaintenanceRecord.equipment_id == Equipment.id)
            .where(
                Equipment.zone_id == zone_id,
                MaintenanceRecord.status != MaintenanceStatus.COMPLETED,
                MaintenanceRecord.window_start <= now,
                MaintenanceRecord.window_end >= now,
            )
        )
        return list(result.scalars())

    async def create_record(
        self, *, organization_id: uuid.UUID, equipment_id: uuid.UUID, technician: str | None,
        window_start: datetime, window_end: datetime,
    ) -> MaintenanceRecord:
        equipment = await self._db.get(Equipment, equipment_id)
        if equipment is None:
            raise NotFoundError()
        record = MaintenanceRecord(
            organization_id=organization_id, equipment_id=equipment_id,
            status=MaintenanceStatus.IN_PROGRESS, technician=technician,
            window_start=window_start, window_end=window_end,
        )
        self._db.add(record)
        await self._db.flush()
        return record

    async def complete_record(self, record_id: uuid.UUID) -> MaintenanceRecord:
        record = await self._db.get(MaintenanceRecord, record_id)
        if record is None:
            raise NotFoundError()
        record.status = MaintenanceStatus.COMPLETED
        await self._db.flush()
        return record


def get_maintenance_service(db: AsyncSession = Depends(get_db)) -> MaintenanceService:
    return MaintenanceService(db)
