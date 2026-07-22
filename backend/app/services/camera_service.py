"""Camera registry: real FK'd to a zone, replacing the earlier dummy list.

Live stream health/frame delivery is the Vision Intelligence Engine's
concern (app/ai/vision) — this service owns only the registry (what
cameras exist, which zone they monitor, their declared status), matching
the same "persistence vs. live processing" split as Compliance's document
registry vs. its ingestion worker.
"""

import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.camera import Camera
from app.models.facility import Zone


class NotFoundError(Exception):
    pass


class CameraService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_streams(self) -> tuple[list[Camera], dict[uuid.UUID, str]]:
        result = await self._db.execute(
            select(Camera, Zone.name).join(Zone, Camera.zone_id == Zone.id).order_by(Camera.name)
        )
        rows = result.all()
        cameras = [row[0] for row in rows]
        zone_names = {row[0].zone_id: row[1] for row in rows}
        return cameras, zone_names

    async def create(
        self,
        *,
        organization_id: uuid.UUID,
        zone_id: uuid.UUID,
        name: str,
        stream_url: str,
        resolution: str | None,
        fps: int | None,
        layout_x: float | None,
        layout_y: float | None,
    ) -> Camera:
        if await self._db.get(Zone, zone_id) is None:
            raise NotFoundError()
        camera = Camera(
            organization_id=organization_id,
            zone_id=zone_id,
            name=name,
            stream_url=stream_url,
            resolution=resolution,
            fps=fps,
            layout_x=layout_x,
            layout_y=layout_y,
        )
        self._db.add(camera)
        await self._db.flush()
        return camera


def get_camera_service(db: AsyncSession = Depends(get_db)) -> CameraService:
    return CameraService(db)
