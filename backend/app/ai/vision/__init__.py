"""Vision Intelligence Agent — async YOLO/ONNX inference engine.

Pure inference: frame bytes in, structured Detection objects out (see
types.py). No zone/risk/alert/tenant logic lives here — that's the service
layer's job once this is wired to camera ingestion (out of scope here; see
architecture notes for the boundary).

Public surface: `VisionInferenceEngine` (engine.py), started/stopped from
the app lifespan, and `get_vision_engine()` for the process-wide instance.
"""

from app.ai.vision.engine import VisionInferenceEngine, get_vision_engine
from app.ai.vision.types import (
    BBox,
    Detection,
    EngineStats,
    FrameResult,
    FrameStatus,
    ModelStatus,
)

__all__ = [
    "VisionInferenceEngine",
    "get_vision_engine",
    "BBox",
    "Detection",
    "EngineStats",
    "FrameResult",
    "FrameStatus",
    "ModelStatus",
]
