import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.core.permissions import SENSORS_READ, SENSORS_WRITE
from app.db.session import get_db
from app.models.facility import Zone
from app.schemas.auth import AuthenticatedUser
from app.schemas.sensors import (
    SensorDeviceCreateRequest,
    SensorDeviceListResponse,
    SensorDeviceRead,
    SensorReadingHistoryResponse,
    SensorReadingPoint,
)
from app.services.sensors_service import NotFoundError, SensorsService, get_sensors_service

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.get(
    "",
    response_model=SensorDeviceListResponse,
    summary="List sensor devices with their latest reading",
    description=(
        "Real IoT/SCADA sensor readings are simulated (app/ai/sensors) — no "
        "hardware exists for this demo. Requires the 'sensors:read' permission."
    ),
)
async def list_sensors(
    _current_user: AuthenticatedUser = Depends(require_permission(SENSORS_READ)),
    service: SensorsService = Depends(get_sensors_service),
) -> SensorDeviceListResponse:
    rows = await service.list_devices()
    return SensorDeviceListResponse(
        items=[
            SensorDeviceRead(
                id=device.id,
                zone_id=device.zone_id,
                zone_name=zone_name,
                sensor_type=device.sensor_type,
                name=device.name,
                unit=device.unit,
                baseline_min=device.baseline_min,
                baseline_max=device.baseline_max,
                latest_value=latest.value if latest else None,
                latest_recorded_at=latest.recorded_at if latest else None,
                is_anomaly=latest.is_anomaly if latest else False,
            )
            for device, zone_name, latest in rows
        ]
    )


@router.get(
    "/{sensor_id}/readings",
    response_model=SensorReadingHistoryResponse,
    summary="Reading history for one sensor",
)
async def read_sensor_history(
    sensor_id: uuid.UUID,
    since_minutes: int = Query(60, ge=1, le=10080),
    _current_user: AuthenticatedUser = Depends(require_permission(SENSORS_READ)),
    service: SensorsService = Depends(get_sensors_service),
) -> SensorReadingHistoryResponse:
    since = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
    try:
        readings = await service.get_history(sensor_id, since=since)
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sensor not found")
    return SensorReadingHistoryResponse(
        sensor_id=sensor_id,
        readings=[
            SensorReadingPoint(value=r.value, is_anomaly=r.is_anomaly, recorded_at=r.recorded_at)
            for r in readings
        ],
    )


@router.post(
    "",
    response_model=SensorDeviceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a sensor device",
    description="Requires the 'sensors:write' permission.",
)
async def create_sensor(
    request: SensorDeviceCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission(SENSORS_WRITE)),
    service: SensorsService = Depends(get_sensors_service),
    db: AsyncSession = Depends(get_db),
) -> SensorDeviceRead:
    try:
        device = await service.create(
            organization_id=current_user.organization_id,
            zone_id=request.zone_id,
            sensor_type=request.sensor_type,
            name=request.name,
            unit=request.unit,
            baseline_min=request.baseline_min,
            baseline_max=request.baseline_max,
        )
    except NotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "zone_id does not exist")
    zone = await db.get(Zone, device.zone_id)
    return SensorDeviceRead(
        id=device.id,
        zone_id=device.zone_id,
        zone_name=zone.name,
        sensor_type=device.sensor_type,
        name=device.name,
        unit=device.unit,
        baseline_min=device.baseline_min,
        baseline_max=device.baseline_max,
        latest_value=None,
        latest_recorded_at=None,
        is_anomaly=False,
    )
