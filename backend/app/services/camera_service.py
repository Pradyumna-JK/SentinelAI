"""Business logic for the Camera / CCTV Monitoring module.

Currently returns static dummy data. Will be backed by the camera registry
and the Vision Intelligence Agent's live stream metadata once implemented.
"""

from functools import lru_cache

from app.models.enums import CameraStatus
from app.schemas.camera import CameraListResponse, CameraStream


class CameraService:
    """Provides registered CCTV camera stream metadata."""

    def __init__(self) -> None:
        self._streams = [
            CameraStream(
                camera_id="cam-001",
                name="Dock A - North",
                zone_id="zone-001",
                zone_name="Loading Dock A",
                stream_url="https://cdn.sentinelai.demo/hls/cam1.m3u8",
                status=CameraStatus.ACTIVE,
                resolution="1920x1080",
                fps=24,
            ),
            CameraStream(
                camera_id="cam-002",
                name="Assembly Line 3 - Overview",
                zone_id="zone-002",
                zone_name="Assembly Line 3",
                stream_url="https://cdn.sentinelai.demo/hls/cam2.m3u8",
                status=CameraStatus.ACTIVE,
                resolution="1280x720",
                fps=30,
            ),
            CameraStream(
                camera_id="cam-003",
                name="Chemical Storage - Entrance",
                zone_id="zone-003",
                zone_name="Chemical Storage",
                stream_url="https://cdn.sentinelai.demo/hls/cam3.m3u8",
                status=CameraStatus.MAINTENANCE,
                resolution="1920x1080",
                fps=0,
            ),
        ]

    def list_streams(self) -> CameraListResponse:
        active_count = sum(1 for stream in self._streams if stream.status == CameraStatus.ACTIVE)
        return CameraListResponse(
            total_cameras=len(self._streams),
            active_cameras=active_count,
            streams=self._streams,
        )


@lru_cache
def get_camera_service() -> CameraService:
    return CameraService()
