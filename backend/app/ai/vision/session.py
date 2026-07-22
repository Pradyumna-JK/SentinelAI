"""ONNX Runtime session management: provider selection and async execution.

GPU support / CPU fallback happens here and only here: at session creation
we request CUDA first and let ONNX Runtime fall back to CPU if the runtime
build or the host has no usable GPU. Which provider actually won is
reported upward (FrameResult.provider, /vision/status) rather than assumed
— "we asked for CUDA" and "we're running CUDA" are different facts.

`run()` pushes the (CPU-bound, GIL-releasing) session call onto the default
thread pool so the event loop never blocks — the engine stays fully async
without pretending inference itself is awaitable.
"""

import asyncio
from pathlib import Path

import numpy as np
import onnxruntime as ort

# Order = preference. ORT silently skips providers its build doesn't have,
# so listing CUDA on a CPU-only install is safe, not an error.
_PREFERRED_PROVIDERS = ("CUDAExecutionProvider", "CPUExecutionProvider")


class VisionOnnxSession:
    def __init__(self, model_file: Path) -> None:
        available = set(ort.get_available_providers())
        requested = [p for p in _PREFERRED_PROVIDERS if p in available]

        options = ort.SessionOptions()
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        self._session = ort.InferenceSession(str(model_file), sess_options=options, providers=requested)
        self._input_name = self._session.get_inputs()[0].name
        # The provider ORT actually chose, not the one we hoped for.
        self.provider: str = self._session.get_providers()[0]

    async def run(self, batch: np.ndarray) -> np.ndarray:
        """(N,3,S,S) float32 -> (N, 4+nc, anchors), off the event loop."""
        loop = asyncio.get_running_loop()
        outputs = await loop.run_in_executor(None, self._run_sync, batch)
        return outputs

    def _run_sync(self, batch: np.ndarray) -> np.ndarray:
        return self._session.run(None, {self._input_name: batch})[0]
