"""Structured detection types returned by the vision inference engine.

Plain dataclasses, not Pydantic: this layer has no HTTP/validation concerns
and callers in the service layer convert to API schemas when (and only
when) results cross the API boundary. Nothing in here knows about risk,
alerts, tenants, or persistence — the engine's contract is strictly
"frame in, detections out".
"""

from dataclasses import dataclass, field
from enum import Enum


class FrameStatus(str, Enum):
    PROCESSED = "processed"  # ran through inference
    SKIPPED = "skipped"      # dropped by frame-skipping policy (every Nth frame runs)
    DROPPED = "dropped"      # queue full — backpressure, caller may retry/ignore


@dataclass(frozen=True)
class BBox:
    """Pixel coordinates in the ORIGINAL frame (letterbox already undone)."""

    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class Detection:
    class_name: str        # e.g. "person", "helmet", "fire"
    confidence: float      # 0..1, already >= the class's configured threshold
    bbox: BBox
    model: str             # which physical model produced this


@dataclass
class FrameResult:
    request_id: str
    source_id: str                     # opaque caller-supplied stream/camera key
    status: FrameStatus
    detections: list[Detection] = field(default_factory=list)
    latency_ms: float | None = None    # queue-entry -> decode-complete; None unless PROCESSED
    provider: str | None = None        # "CUDAExecutionProvider" | "CPUExecutionProvider"
    models_run: list[str] = field(default_factory=list)
    models_unavailable: list[str] = field(default_factory=list)


@dataclass
class ModelStatus:
    name: str              # capability name: person/helmet/vest/gloves/fire/smoke
    model_file: str
    loaded: bool
    provider: str | None   # None when not loaded
    reason: str | None     # why not loaded (e.g. "weights file missing")


@dataclass
class EngineStats:
    running: bool
    provider: str | None
    queue_depth: int
    queue_capacity: int
    frames_processed: int
    frames_skipped: int
    frames_dropped: int
    batches_run: int
    avg_batch_size: float
    avg_latency_ms: float
    models: list[ModelStatus] = field(default_factory=list)
