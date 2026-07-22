from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.core.permissions import CAMERA_READ, CAMERA_WRITE
from app.db.session import get_db
from app.models.enums import CameraStatus
from app.models.facility import Zone
from app.schemas.auth import AuthenticatedUser
from app.schemas.camera import CameraCreateRequest, CameraListResponse, CameraStream
from app.services.camera_service import CameraService, NotFoundError, get_camera_service

router = APIRouter(prefix="/camera", tags=["Camera"])


def _to_camera_read(camera, zone_name: str) -> CameraStream:
    return CameraStream(
        camera_id=camera.id,
        name=camera.name,
        zone_id=camera.zone_id,
        zone_name=zone_name,
        stream_url=camera.stream_url,
        status=camera.status,
        resolution=camera.resolution,
        fps=camera.fps,
    )


@router.get(
    "",
    response_model=CameraListResponse,
    summary="List camera streams",
    description=(
        "Returns all registered CCTV camera streams with their declared status. "
        "Requires the 'camera:read' permission."
    ),
)
async def read_cameras(
    _current_user: AuthenticatedUser = Depends(require_permission(CAMERA_READ)),
    service: CameraService = Depends(get_camera_service),
) -> CameraListResponse:
    cameras, zone_names = await service.list_streams()
    return CameraListResponse(
        total_cameras=len(cameras),
        active_cameras=sum(1 for c in cameras if c.status == CameraStatus.ACTIVE),
        streams=[_to_camera_read(c, zone_names[c.zone_id]) for c in cameras],
    )


@router.post(
    "",
    response_model=CameraStream,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new camera",
    description="Requires the 'camera:write' permission.",
)
async def create_camera(
    request: CameraCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission(CAMERA_WRITE)),
    service: CameraService = Depends(get_camera_service),
    db: AsyncSession = Depends(get_db),
) -> CameraStream:
    try:
        camera = await service.create(
            organization_id=current_user.organization_id,
            zone_id=request.zone_id,
            name=request.name,
            stream_url=request.stream_url,
            resolution=request.resolution,
            fps=request.fps,
            layout_x=request.layout_x,
            layout_y=request.layout_y,
        )
    except NotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "zone_id does not exist")
    zone = await db.get(Zone, camera.zone_id)
    return _to_camera_read(camera, zone.name)
