"""Detection ingestion: raw detections -> interpreted hazards -> persisted
RiskEvent rows.

This is where app/ai/vision's pure ML output and app/ai/risk's pure hazard-
interpretation logic (catalog.py) meet persistence and tenancy — neither of
those two `app/ai` packages imports the other or touches the database
directly; this service is the seam.
"""

import uuid
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.risk.catalog import interpret_detections
from app.ai.risk.types import NormalizedBBox, RawDetection
from app.db.session import get_db
from app.models.facility import Zone
from app.models.risk import RiskEvent


class ZoneNotFoundError(Exception):
    pass


class DetectionIn:
    """Plain input shape for one detection to ingest — decoupled from both
    the vision engine's Detection dataclass and any Pydantic schema, so
    this service has exactly one contract regardless of caller."""

    __slots__ = ("class_name", "confidence", "x1", "y1", "x2", "y2")

    def __init__(self, class_name: str, confidence: float, x1: float, y1: float, x2: float, y2: float) -> None:
        self.class_name = class_name
        self.confidence = confidence
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2


class RiskIngestService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def ingest_frame(
        self,
        *,
        organization_id: uuid.UUID,
        zone_id: uuid.UUID,
        camera_id: str,
        detections: list[DetectionIn],
        frame_width: float,
        frame_height: float,
        source_id: str | None = None,
        detected_at: datetime | None = None,
    ) -> list[RiskEvent]:
        """Interpret one frame's detections and persist the resulting
        hazard events. `frame_width`/`frame_height` normalize pixel boxes
        to the 0..1 scale RiskEvent stores (see its docstring) — pass 1.0/
        1.0 if the caller's boxes are already normalized.

        Raises ZoneNotFoundError if `zone_id` doesn't exist *for the
        caller's organization* — the automatic tenant filter (app/core/
        tenancy.py) makes "belongs to another org" and "doesn't exist"
        indistinguishable here too, same as everywhere else in the API.
        """
        if await self._db.get(Zone, zone_id) is None:
            raise ZoneNotFoundError()

        detected_at = detected_at or datetime.now(timezone.utc)

        raw = [
            RawDetection(
                class_name=d.class_name,
                confidence=d.confidence,
                bbox=NormalizedBBox(
                    x1=d.x1 / frame_width,
                    y1=d.y1 / frame_height,
                    x2=d.x2 / frame_width,
                    y2=d.y2 / frame_height,
                ),
            )
            for d in detections
        ]

        result = interpret_detections(raw)

        events = [
            RiskEvent(
                organization_id=organization_id,
                zone_id=zone_id,
                camera_id=camera_id,
                source_id=source_id,
                hazard_class=hazard.hazard_class,
                confidence=hazard.confidence,
                severity=hazard.severity,
                bbox_x1=hazard.bbox.x1 if hazard.bbox else None,
                bbox_y1=hazard.bbox.y1 if hazard.bbox else None,
                bbox_x2=hazard.bbox.x2 if hazard.bbox else None,
                bbox_y2=hazard.bbox.y2 if hazard.bbox else None,
                detected_at=detected_at,
            )
            for hazard in result.hazards
        ]
        self._db.add_all(events)
        await self._db.flush()
        return events


def get_risk_ingest_service(db: AsyncSession = Depends(get_db)) -> RiskIngestService:
    return RiskIngestService(db)
