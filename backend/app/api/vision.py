"""Vision engine observability.

Gated by `camera:read` rather than a new permission code — this is
operational status for the same capability area as /camera (which fronts
the camera stream, this fronts what's being run against it), and adding a
dedicated permission for one read-only status endpoint would mean another
RBAC seed migration for no real isolation benefit.
"""

from fastapi import APIRouter, Depends

from app.ai.vision import get_vision_engine
from app.core.deps import require_permission
from app.core.permissions import CAMERA_READ
from app.schemas.auth import AuthenticatedUser
from app.schemas.vision import ModelStatusRead, VisionEngineStatus

router = APIRouter(prefix="/vision", tags=["Vision"])


@router.get(
    "/status",
    response_model=VisionEngineStatus,
    summary="Vision inference engine status",
    description=(
        "Reports whether the engine is running, which execution provider is "
        "active (GPU/CPU), per-capability model availability, and queue/"
        "throughput counters. No frame submission endpoint exists yet — this "
        "engine has no camera-ingestion wiring in this task's scope."
    ),
)
def get_vision_status(
    _current_user: AuthenticatedUser = Depends(require_permission(CAMERA_READ)),
) -> VisionEngineStatus:
    stats = get_vision_engine().stats()
    return VisionEngineStatus(
        running=stats.running,
        provider=stats.provider,
        queue_depth=stats.queue_depth,
        queue_capacity=stats.queue_capacity,
        frames_processed=stats.frames_processed,
        frames_skipped=stats.frames_skipped,
        frames_dropped=stats.frames_dropped,
        batches_run=stats.batches_run,
        avg_batch_size=stats.avg_batch_size,
        avg_latency_ms=stats.avg_latency_ms,
        models=[
            ModelStatusRead(
                name=m.name, model_file=m.model_file, loaded=m.loaded, provider=m.provider, reason=m.reason
            )
            for m in stats.models
        ],
    )
