"""Frame preprocessing for YOLO ONNX inference.

Letterbox resize (aspect-preserving, gray padding) exactly as Ultralytics
does in training — feeding squashed/stretched frames instead measurably
hurts accuracy. Returns the scale/pad bookkeeping needed to map detected
boxes back to original-frame pixels in postprocessing.
"""

from dataclasses import dataclass

import cv2
import numpy as np

_PAD_COLOR = (114, 114, 114)  # Ultralytics' training-time padding gray


@dataclass(frozen=True)
class LetterboxMeta:
    """Everything needed to undo the letterbox transform for one frame."""

    scale: float
    pad_x: float
    pad_y: float
    original_width: int
    original_height: int


def decode_image(data: bytes) -> np.ndarray | None:
    """JPEG/PNG bytes -> BGR ndarray. None when the payload isn't an image."""
    array = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(array, cv2.IMREAD_COLOR)


def letterbox(frame_bgr: np.ndarray, input_size: int) -> tuple[np.ndarray, LetterboxMeta]:
    """BGR frame -> (3, S, S) float32 CHW tensor in 0..1 RGB + undo-metadata."""
    height, width = frame_bgr.shape[:2]
    scale = min(input_size / width, input_size / height)
    new_w, new_h = round(width * scale), round(height * scale)

    resized = cv2.resize(frame_bgr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    pad_x = (input_size - new_w) / 2
    pad_y = (input_size - new_h) / 2
    top, bottom = round(pad_y - 0.1), round(pad_y + 0.1)
    left, right = round(pad_x - 0.1), round(pad_x + 0.1)
    padded = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=_PAD_COLOR)

    rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
    tensor = rgb.astype(np.float32) / 255.0
    tensor = np.transpose(tensor, (2, 0, 1))  # HWC -> CHW

    meta = LetterboxMeta(
        scale=scale, pad_x=left, pad_y=top, original_width=width, original_height=height
    )
    return tensor, meta


def stack_batch(tensors: list[np.ndarray]) -> np.ndarray:
    """List of (3,S,S) -> contiguous (N,3,S,S) batch for the ONNX session."""
    return np.ascontiguousarray(np.stack(tensors, axis=0))
