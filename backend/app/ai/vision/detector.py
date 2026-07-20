"""Vision Intelligence Agent placeholder.

Not implemented yet. Once wired up (YOLOv8 + OpenCV per
docs/11_AI_ARCHITECTURE.md §1), this module will process camera frames and
emit detections for the Risk Engine to consume. Kept as an empty seam so
`services/camera_service.py` has a stable integration point to call into
later, rather than requiring another restructuring.
"""


class VisionDetectionEngine:
    """Placeholder for the future real-time hazard detection engine."""

    def detect(self, frame_reference: str) -> list[dict]:
        raise NotImplementedError("Vision Intelligence Agent is not implemented yet.")
