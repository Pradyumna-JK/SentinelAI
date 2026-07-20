from fastapi import APIRouter, Depends

from app.schemas.camera import CameraListResponse
from app.services.camera_service import CameraService, get_camera_service

router = APIRouter(prefix="/camera", tags=["Camera"])


@router.get(
    "",
    response_model=CameraListResponse,
    summary="List camera streams",
    description=(
        "Returns all registered CCTV camera streams with their live status. "
        "Backed by dummy data until the Vision Intelligence Agent is implemented."
    ),
)
def read_cameras(service: CameraService = Depends(get_camera_service)) -> CameraListResponse:
    return service.list_streams()
