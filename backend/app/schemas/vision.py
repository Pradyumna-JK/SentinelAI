from pydantic import BaseModel, Field


class ModelStatusRead(BaseModel):
    name: str = Field(..., description="Detection capability, e.g. 'person', 'helmet'")
    model_file: str
    loaded: bool
    provider: str | None = Field(None, description="'CUDAExecutionProvider' | 'CPUExecutionProvider'")
    reason: str | None = Field(None, description="Why unavailable, when loaded is false")


class VisionEngineStatus(BaseModel):
    running: bool
    provider: str | None = Field(None, description="Execution provider in use, e.g. CPU/CUDA")
    queue_depth: int
    queue_capacity: int
    frames_processed: int
    frames_skipped: int
    frames_dropped: int
    batches_run: int
    avg_batch_size: float
    avg_latency_ms: float
    models: list[ModelStatusRead]
