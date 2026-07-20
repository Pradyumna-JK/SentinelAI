from pydantic import BaseModel, Field

from app.models.enums import CameraStatus


class CameraStream(BaseModel):
    camera_id: str = Field(..., description="Unique identifier of the camera")
    name: str = Field(..., description="Human-readable camera name")
    zone_id: str = Field(..., description="Identifier of the zone this camera monitors")
    zone_name: str = Field(..., description="Name of the zone this camera monitors")
    stream_url: str = Field(..., description="HLS/RTSP stream URL for live playback")
    status: CameraStatus = Field(..., description="Current connectivity status of the camera")
    resolution: str = Field(..., description="Stream resolution, e.g. '1920x1080'")
    fps: int = Field(..., ge=0, description="Frames per second the stream is delivering")


class CameraListResponse(BaseModel):
    total_cameras: int = Field(..., ge=0)
    active_cameras: int = Field(..., ge=0)
    streams: list[CameraStream]

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_cameras": 2,
                "active_cameras": 1,
                "streams": [
                    {
                        "camera_id": "cam-001",
                        "name": "Dock A - North",
                        "zone_id": "zone-001",
                        "zone_name": "Loading Dock A",
                        "stream_url": "https://cdn.sentinelai.demo/hls/cam1.m3u8",
                        "status": "active",
                        "resolution": "1920x1080",
                        "fps": 24,
                    }
                ],
            }
        }
    }
