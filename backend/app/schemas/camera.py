import uuid

from pydantic import BaseModel, Field

from app.models.enums import CameraStatus


class CameraStream(BaseModel):
    camera_id: uuid.UUID = Field(..., description="Unique identifier of the camera")
    name: str = Field(..., description="Human-readable camera name")
    zone_id: uuid.UUID = Field(..., description="Identifier of the zone this camera monitors")
    zone_name: str = Field(..., description="Name of the zone this camera monitors")
    stream_url: str = Field(..., description="HLS/RTSP stream URL for live playback")
    status: CameraStatus = Field(..., description="Current connectivity status of the camera")
    resolution: str | None = Field(None, description="Stream resolution, e.g. '1920x1080'")
    fps: int | None = Field(None, ge=0, description="Frames per second the stream is delivering")


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
                        "camera_id": "b3f2a1e0-0000-4000-8000-000000000003",
                        "name": "Dock A - North",
                        "zone_id": "b3f2a1e0-0000-4000-8000-000000000000",
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


class CameraCreateRequest(BaseModel):
    zone_id: uuid.UUID = Field(..., description="Zone this camera monitors")
    name: str = Field(..., min_length=1, max_length=255)
    stream_url: str = Field(..., min_length=1, max_length=500)
    resolution: str | None = Field(None, max_length=20)
    fps: int | None = Field(None, ge=0)
    layout_x: float | None = Field(None, description="Position within the zone's floorplan rectangle")
    layout_y: float | None = Field(None)
