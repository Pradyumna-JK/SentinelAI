"""Async vision inference engine: queue -> micro-batch -> ONNX -> decode.

Flow per frame:
    submit() -> frame-skip gate -> decode+letterbox (thread pool) ->
    bounded asyncio.Queue -> worker collects a micro-batch (up to
    `vision_batch_size` frames or `vision_batch_window_ms`, whichever
    first) -> one ONNX run per model slot needed by the batch -> decode ->
    each caller's Future resolves with its own FrameResult.

Backpressure is explicit, never blocking: a full queue resolves the caller
immediately with status=DROPPED (drop-newest). For live video, dropping the
newest frame under load is correct — the queue already holds fresher-than-
processable frames, and blocking the producer would stall the stream it's
reading from. Frame skipping (process every Nth frame per source) is the
first gate, applied before any CPU work is spent on the frame.

No business logic lives here by design: nothing in this module knows about
zones, risk, alerts, tenants, or persistence. Callers hand in frames and an
opaque source_id; they get structured detections back. What those
detections *mean* is the service layer's problem.
"""

import asyncio
import uuid
from pathlib import Path

import numpy as np
import structlog

from app.ai.vision.postprocessing import decode_predictions
from app.ai.vision.preprocessing import LetterboxMeta, decode_image, letterbox, stack_batch
from app.ai.vision.registry import (
    ALL_CAPABILITIES,
    CAPABILITY_TO_MODEL,
    MODEL_SPECS,
    ModelSpec,
    model_path,
)
from app.ai.vision.session import VisionOnnxSession
from app.ai.vision.types import Detection, EngineStats, FrameResult, FrameStatus, ModelStatus
from app.core.config import get_settings

logger = structlog.get_logger("sentinel.vision")


class InvalidFrameError(Exception):
    """Payload could not be decoded as an image."""


class _LoadedModel:
    def __init__(self, spec: ModelSpec, session: VisionOnnxSession | None, reason: str | None) -> None:
        self.spec = spec
        self.session = session
        self.reason = reason

    @property
    def loaded(self) -> bool:
        return self.session is not None


class _Request:
    __slots__ = ("request_id", "source_id", "tensor", "meta", "slots", "future", "enqueued_at")

    def __init__(
        self,
        request_id: str,
        source_id: str,
        tensor: np.ndarray,
        meta: LetterboxMeta,
        slots: list[str],
        future: "asyncio.Future[FrameResult]",
        enqueued_at: float,
    ) -> None:
        self.request_id = request_id
        self.source_id = source_id
        self.tensor = tensor
        self.meta = meta
        self.slots = slots
        self.future = future
        self.enqueued_at = enqueued_at


class VisionInferenceEngine:
    def __init__(self) -> None:
        settings = get_settings()
        self._models_dir = Path(settings.vision_models_dir)
        self._batch_size = settings.vision_batch_size
        self._batch_window_s = settings.vision_batch_window_ms / 1000.0
        self._frame_skip = max(1, settings.vision_frame_skip)
        self._default_confidence = settings.vision_min_confidence

        self._queue: asyncio.Queue[_Request] = asyncio.Queue(maxsize=settings.vision_queue_size)
        self._models: dict[str, _LoadedModel] = {}
        self._worker: asyncio.Task | None = None
        self._frame_counters: dict[str, int] = {}

        # stats
        self._processed = 0
        self._skipped = 0
        self._dropped = 0
        self._batches = 0
        self._batched_frames = 0
        self._latency_sum_ms = 0.0

    # ------------------------------------------------------------- lifecycle

    async def start(self) -> None:
        """Load whatever weights exist and start the batch worker.

        Missing weights degrade the capability, never the engine — matching
        how this app treats every optional dependency at startup.
        """
        loop = asyncio.get_running_loop()
        for spec in MODEL_SPECS:
            path = model_path(self._models_dir, spec)
            if not path.exists():
                self._models[spec.name] = _LoadedModel(spec, None, "weights file missing")
                logger.warning("vision_model_unavailable", model=spec.name, file=str(path))
                continue
            try:
                # InferenceSession construction is blocking (graph load +
                # optimization) — keep it off the event loop too.
                session = await loop.run_in_executor(None, VisionOnnxSession, path)
            except Exception as exc:  # noqa: BLE001 — any load failure = unavailable, not fatal
                self._models[spec.name] = _LoadedModel(spec, None, f"{type(exc).__name__}: {exc}"[:200])
                logger.error("vision_model_load_failed", model=spec.name, error=str(exc))
                continue
            self._models[spec.name] = _LoadedModel(spec, session, None)
            logger.info("vision_model_loaded", model=spec.name, provider=session.provider)

        self._worker = asyncio.create_task(self._worker_loop(), name="vision-batch-worker")
        logger.info(
            "vision_engine_started",
            provider=self.provider,
            batch_size=self._batch_size,
            batch_window_ms=int(self._batch_window_s * 1000),
            frame_skip=self._frame_skip,
        )

    async def stop(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass
            self._worker = None
        # Fail any stragglers cleanly instead of leaving callers hanging.
        while not self._queue.empty():
            request = self._queue.get_nowait()
            if not request.future.done():
                request.future.set_result(
                    FrameResult(request.request_id, request.source_id, FrameStatus.DROPPED)
                )
        logger.info("vision_engine_stopped")

    @property
    def running(self) -> bool:
        return self._worker is not None and not self._worker.done()

    @property
    def provider(self) -> str | None:
        for model in self._models.values():
            if model.loaded:
                return model.session.provider
        return None

    # ------------------------------------------------------------- submission

    async def submit(
        self,
        frame: bytes | np.ndarray,
        *,
        source_id: str,
        capabilities: list[str] | None = None,
    ) -> FrameResult:
        """Submit one frame; resolves when its batch has been processed.

        `capabilities` selects which detectors run (default: all six).
        Raises InvalidFrameError for undecodable bytes; every other outcome
        is expressed in FrameResult.status, not exceptions.
        """
        request_id = uuid.uuid4().hex
        wanted = capabilities if capabilities is not None else list(ALL_CAPABILITIES)

        # Gate 1: frame skipping — cheapest possible rejection, before any
        # decode work. Per-source, so one camera's skip cadence doesn't
        # depend on how many other cameras are streaming.
        counter = self._frame_counters.get(source_id, 0)
        self._frame_counters[source_id] = counter + 1
        if counter % self._frame_skip != 0:
            self._skipped += 1
            return FrameResult(request_id, source_id, FrameStatus.SKIPPED)

        loop = asyncio.get_running_loop()

        # Decode + letterbox off the event loop; ~ms-scale but it adds up
        # at N cameras x M fps.
        def _prepare() -> tuple[np.ndarray, LetterboxMeta]:
            bgr = decode_image(frame) if isinstance(frame, (bytes, bytearray)) else frame
            if bgr is None or getattr(bgr, "size", 0) == 0:
                raise InvalidFrameError("frame is not a decodable image")
            return letterbox(bgr, input_size=640)

        tensor, meta = await loop.run_in_executor(None, _prepare)

        slots_available: list[str] = []
        unavailable: list[str] = []
        for capability in wanted:
            slot = CAPABILITY_TO_MODEL.get(capability)
            if slot is None:
                unavailable.append(capability)
            elif self._models.get(slot) and self._models[slot].loaded:
                if slot not in slots_available:
                    slots_available.append(slot)
            else:
                unavailable.append(capability)

        if not slots_available:
            # Nothing runnable for this frame — answer immediately and honestly.
            return FrameResult(
                request_id, source_id, FrameStatus.PROCESSED,
                models_run=[], models_unavailable=unavailable, latency_ms=0.0,
            )

        future: asyncio.Future[FrameResult] = loop.create_future()
        request = _Request(request_id, source_id, tensor, meta, slots_available, future, loop.time())
        try:
            self._queue.put_nowait(request)
        except asyncio.QueueFull:
            self._dropped += 1
            return FrameResult(
                request_id, source_id, FrameStatus.DROPPED, models_unavailable=unavailable
            )

        result = await future
        result.models_unavailable = unavailable
        return result

    # ------------------------------------------------------------- worker

    async def _worker_loop(self) -> None:
        loop = asyncio.get_running_loop()
        while True:
            batch = [await self._queue.get()]
            deadline = loop.time() + self._batch_window_s
            while len(batch) < self._batch_size:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    break
                try:
                    batch.append(await asyncio.wait_for(self._queue.get(), timeout=remaining))
                except asyncio.TimeoutError:
                    break
            try:
                await self._run_batch(batch)
            except Exception as exc:  # noqa: BLE001 — one bad batch must not kill the worker
                logger.exception("vision_batch_failed", batch_size=len(batch))
                for request in batch:
                    if not request.future.done():
                        request.future.set_exception(exc)

    async def _run_batch(self, batch: list[_Request]) -> None:
        loop = asyncio.get_running_loop()
        detections_per_request: dict[str, list[Detection]] = {r.request_id: [] for r in batch}
        models_run_per_request: dict[str, list[str]] = {r.request_id: [] for r in batch}

        # One ONNX call per model slot, over exactly the frames that want it.
        slots_needed = {slot for request in batch for slot in request.slots}
        for slot in slots_needed:
            model = self._models[slot]
            members = [r for r in batch if slot in r.slots]
            input_batch = stack_batch([r.tensor for r in members])
            output = await model.session.run(input_batch)
            for row_index, request in enumerate(members):
                decoded = await loop.run_in_executor(
                    None,
                    decode_predictions,
                    output[row_index],
                    model.spec,
                    request.meta,
                    self._default_confidence,
                )
                detections_per_request[request.request_id].extend(decoded)
                models_run_per_request[request.request_id].append(slot)

        now = loop.time()
        for request in batch:
            latency_ms = round((now - request.enqueued_at) * 1000, 1)
            self._processed += 1
            self._latency_sum_ms += latency_ms
            if not request.future.done():
                request.future.set_result(
                    FrameResult(
                        request_id=request.request_id,
                        source_id=request.source_id,
                        status=FrameStatus.PROCESSED,
                        detections=detections_per_request[request.request_id],
                        latency_ms=latency_ms,
                        provider=self.provider,
                        models_run=models_run_per_request[request.request_id],
                    )
                )
        self._batches += 1
        self._batched_frames += len(batch)

    # ------------------------------------------------------------- stats

    def stats(self) -> EngineStats:
        return EngineStats(
            running=self.running,
            provider=self.provider,
            queue_depth=self._queue.qsize(),
            queue_capacity=self._queue.maxsize,
            frames_processed=self._processed,
            frames_skipped=self._skipped,
            frames_dropped=self._dropped,
            batches_run=self._batches,
            avg_batch_size=round(self._batched_frames / self._batches, 2) if self._batches else 0.0,
            avg_latency_ms=round(self._latency_sum_ms / self._processed, 1) if self._processed else 0.0,
            models=[
                ModelStatus(
                    name=capability,
                    model_file=self._models[slot].spec.filename if slot in self._models else "?",
                    loaded=bool(self._models.get(slot) and self._models[slot].loaded),
                    provider=self._models[slot].session.provider
                    if self._models.get(slot) and self._models[slot].loaded
                    else None,
                    reason=self._models[slot].reason if slot in self._models else "unknown capability",
                )
                for capability, slot in CAPABILITY_TO_MODEL.items()
            ],
        )


_engine: VisionInferenceEngine | None = None


def get_vision_engine() -> VisionInferenceEngine:
    """Process-wide engine singleton (created lazily, started via lifespan)."""
    global _engine
    if _engine is None:
        _engine = VisionInferenceEngine()
    return _engine
