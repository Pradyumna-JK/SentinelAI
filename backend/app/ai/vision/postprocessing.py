"""YOLOv8 ONNX output decoding: thresholding, NMS, box un-mapping.

Input contract (Ultralytics YOLOv8 export): one output of shape
(N, 4 + num_classes, anchors) — xywh box center-format at model input
scale, then one score row per class. No objectness row.
"""

import numpy as np

from app.ai.vision.preprocessing import LetterboxMeta
from app.ai.vision.registry import ModelSpec
from app.ai.vision.types import BBox, Detection


def decode_predictions(
    output_row: np.ndarray,          # (4 + num_classes, anchors) — one frame's slice
    spec: ModelSpec,
    meta: LetterboxMeta,
    default_confidence: float,
) -> list[Detection]:
    predictions = output_row.T  # -> (anchors, 4 + nc)
    boxes_xywh = predictions[:, :4]
    class_scores = predictions[:, 4:]

    class_ids = np.argmax(class_scores, axis=1)
    confidences = class_scores[np.arange(class_scores.shape[0]), class_ids]

    # Cheap global pre-filter at the lowest configured threshold; exact
    # per-class thresholds are applied after, on the surviving few.
    floor = min([default_confidence, *spec.confidence_overrides.values()])
    keep = confidences >= floor
    if not np.any(keep):
        return []
    boxes_xywh, class_ids, confidences = boxes_xywh[keep], class_ids[keep], confidences[keep]

    survivors: list[tuple[list[float], float, int]] = []  # ([x,y,w,h], conf, class_id)
    for box, class_id, conf in zip(boxes_xywh, class_ids, confidences):
        name = spec.class_names[class_id]
        if spec.class_filter is not None and name not in spec.class_filter:
            continue
        if conf < spec.confidence_overrides.get(name, default_confidence):
            continue
        cx, cy, w, h = box
        survivors.append(([float(cx - w / 2), float(cy - h / 2), float(w), float(h)], float(conf), int(class_id)))

    if not survivors:
        return []

    # Per-class NMS: boxes of different classes may legitimately overlap
    # (a person wearing a vest), so suppression only happens within a class.
    import cv2  # local import keeps this module importable without cv2 for pure-decode tests

    detections: list[Detection] = []
    for class_id in {s[2] for s in survivors}:
        class_boxes = [s for s in survivors if s[2] == class_id]
        indices = cv2.dnn.NMSBoxes(
            bboxes=[b for b, _, _ in class_boxes],
            scores=[c for _, c, _ in class_boxes],
            score_threshold=0.0,  # thresholds already applied above
            nms_threshold=spec.nms_iou_threshold,
        )
        for i in np.array(indices).flatten():
            (x, y, w, h), conf, cid = class_boxes[int(i)]
            detections.append(
                Detection(
                    class_name=spec.class_names[cid],
                    confidence=round(conf, 4),
                    bbox=_unmap_box(x, y, w, h, meta),
                    model=spec.name,
                )
            )
    return detections


def _unmap_box(x: float, y: float, w: float, h: float, meta: LetterboxMeta) -> BBox:
    """Model-input-scale xywh (top-left) -> original-frame pixel xyxy, clamped."""
    x1 = (x - meta.pad_x) / meta.scale
    y1 = (y - meta.pad_y) / meta.scale
    x2 = (x + w - meta.pad_x) / meta.scale
    y2 = (y + h - meta.pad_y) / meta.scale
    return BBox(
        x1=round(max(0.0, min(x1, meta.original_width)), 1),
        y1=round(max(0.0, min(y1, meta.original_height)), 1),
        x2=round(max(0.0, min(x2, meta.original_width)), 1),
        y2=round(max(0.0, min(y2, meta.original_height)), 1),
    )
