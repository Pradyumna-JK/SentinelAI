"""Model registry: maps detection *capabilities* to physical ONNX models.

The six capabilities (person, helmet, vest, gloves, fire, smoke) are served
by three physical model slots — one general-purpose COCO model and two
domain models. A capability is available only when its model's weights file
exists on disk; missing weights degrade that capability to "unavailable"
(reported via engine stats / FrameResult.models_unavailable) instead of
failing the engine, consistent with how this app treats every optional
dependency.

Honest status of the three slots:
- yolov8n.onnx        — REAL weights (Ultralytics YOLOv8n, COCO-80), exported
                        to ONNX with a dynamic batch axis. Serves `person`
                        via a class filter.
- ppe-yolov8.onnx     — slot for a custom-trained PPE model (helmet/vest/
                        gloves). No public production-grade weights exist to
                        bundle; train/procure and drop the file in — the
                        class list below must match the training label order.
- fire-smoke-yolov8.onnx — same situation for fire/smoke.

All specs assume the Ultralytics YOLOv8 ONNX export contract: input
(N,3,H,W) float32 0-1 RGB, output (N, 4+num_classes, anchors) with xywh
boxes at model scale and per-class scores (no separate objectness).
"""

from dataclasses import dataclass, field
from pathlib import Path

# Ultralytics COCO-80 label order — decode indexes into this list.
COCO_CLASSES: tuple[str, ...] = (
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush",
)


@dataclass(frozen=True)
class ModelSpec:
    """One physical ONNX model and how to interpret its output."""

    name: str                          # physical slot name
    filename: str
    class_names: tuple[str, ...]       # index -> label, must match training order
    input_size: int = 640
    # Only emit these classes (None = all). This is how the COCO model
    # serves just `person` without wasting output on 79 irrelevant classes.
    class_filter: frozenset[str] | None = None
    # Per-class confidence overrides; anything absent uses the engine-wide
    # default from Settings. Safety-critical classes (fire/smoke) typically
    # run LOWER thresholds — a false alarm is cheaper than a missed fire.
    confidence_overrides: dict[str, float] = field(default_factory=dict)
    nms_iou_threshold: float = 0.45


MODEL_SPECS: tuple[ModelSpec, ...] = (
    ModelSpec(
        name="coco-general",
        filename="yolov8n.onnx",
        class_names=COCO_CLASSES,
        class_filter=frozenset({"person"}),
    ),
    ModelSpec(
        name="ppe",
        filename="ppe-yolov8.onnx",
        class_names=("helmet", "vest", "gloves"),
    ),
    ModelSpec(
        name="fire-smoke",
        filename="fire-smoke-yolov8.onnx",
        class_names=("fire", "smoke"),
        confidence_overrides={"fire": 0.25, "smoke": 0.25},
    ),
)

# capability -> physical slot serving it
CAPABILITY_TO_MODEL: dict[str, str] = {
    "person": "coco-general",
    "helmet": "ppe",
    "vest": "ppe",
    "gloves": "ppe",
    "fire": "fire-smoke",
    "smoke": "fire-smoke",
}

ALL_CAPABILITIES: tuple[str, ...] = tuple(CAPABILITY_TO_MODEL.keys())


def model_path(models_dir: str | Path, spec: ModelSpec) -> Path:
    return Path(models_dir) / spec.filename
