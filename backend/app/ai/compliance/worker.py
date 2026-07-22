"""Background PDF ingestion worker.

Runs as a single always-on asyncio task (started/stopped from app/main.py's
lifespan — same lifecycle pattern as app/ai/vision/engine.py and
app/ai/risk/scheduler.py), consuming an unbounded queue of
(document_id, organization_id) jobs enqueued by
app/services/compliance_ingest_service.py right after a PDF upload commits.

One document processed at a time, deliberately: PDF extraction + embedding
a whole document is already CPU/IO-bound, uploads aren't latency-sensitive
the way live video frames are, and Gemini's embeddings API has its own
per-account rate limit that a small factory deployment's upload volume is
nowhere near stressing — no micro-batching/backpressure logic needed here,
unlike the vision engine's frame queue.

Tenant context: this worker runs outside any request, so — same problem and
same solution as app/ai/risk/scheduler.py — it sets the tenant contextvar
and the Postgres `app.current_organization_id` session variable itself for
each job, using the job's own organization_id, before touching any
TenantScoped row.
"""

import asyncio
import uuid
from datetime import datetime, timezone

import anyio
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.compliance.embeddings import get_embeddings
from app.ai.compliance.ingestion import PdfExtractionError, chunk_pages, extract_pages
from app.ai.compliance.vectorstore import add_chunks
from app.core.config import get_settings
from app.core.tenancy import current_organization_id
from app.database.storage import get_storage_client
from app.db.session import get_session_factory
from app.models.compliance import ComplianceDocument
from app.models.enums import DocumentStatus

logger = structlog.get_logger("sentinel.compliance.ingestion")


class IngestionWorker:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()
        self._worker: asyncio.Task | None = None

    async def start(self) -> None:
        self._worker = asyncio.create_task(self._worker_loop(), name="compliance-ingestion-worker")
        logger.info("compliance_ingestion_worker_started")

    async def stop(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass
            self._worker = None
        logger.info("compliance_ingestion_worker_stopped")

    @property
    def running(self) -> bool:
        return self._worker is not None and not self._worker.done()

    @property
    def queue_depth(self) -> int:
        return self._queue.qsize()

    def enqueue(self, document_id: uuid.UUID, organization_id: uuid.UUID) -> None:
        self._queue.put_nowait((str(document_id), str(organization_id)))

    # ------------------------------------------------------------- worker

    async def _worker_loop(self) -> None:
        while True:
            document_id, organization_id = await self._queue.get()
            try:
                await self._process(document_id, organization_id)
            except Exception:  # noqa: BLE001 — one bad document must not kill the worker
                logger.exception("compliance_ingestion_job_failed", document_id=document_id)

    async def _process(self, document_id: str, organization_id: str) -> None:
        session_factory = get_session_factory()
        token = current_organization_id.set(organization_id)

        async def _set_tenant(session: AsyncSession) -> None:
            # `is_local=true` scopes the GUC to the CURRENT transaction only
            # (matching app/db/session.py's get_db, for the same reason: it's
            # what lets Postgres discard it automatically at commit/rollback
            # instead of leaking it onto a pooled connection's next tenant).
            # The cost of that safety is that it must be re-issued after
            # every commit, not just once per session — this method commits
            # twice (PROCESSING, then READY/FAILED), so it's called twice.
            await session.execute(
                text("SELECT set_config('app.current_organization_id', :org_id, true)"),
                {"org_id": organization_id},
            )

        try:
            async with session_factory() as session:
                await _set_tenant(session)
                document = await session.get(ComplianceDocument, uuid.UUID(document_id))
                if document is None:
                    logger.warning("compliance_ingestion_document_missing", document_id=document_id)
                    return

                document.status = DocumentStatus.PROCESSING
                await session.commit()
                await _set_tenant(session)

                try:
                    pages, chunks, vectors = await self._extract_chunk_embed(document)

                    await anyio.to_thread.run_sync(
                        lambda: add_chunks(
                            organization_id=organization_id,
                            document_id=document_id,
                            title=document.filename,
                            chunks=chunks,
                            embeddings=vectors,
                        )
                    )

                    document.status = DocumentStatus.READY
                    document.page_count = len(pages)
                    document.chunk_count = len(chunks)
                    document.processed_at = datetime.now(timezone.utc)
                    document.error_message = None
                    logger.info(
                        "compliance_ingestion_succeeded",
                        document_id=document_id,
                        page_count=len(pages),
                        chunk_count=len(chunks),
                    )
                except Exception as exc:  # noqa: BLE001 — degrade this one document, not the worker
                    document.status = DocumentStatus.FAILED
                    document.error_message = f"{type(exc).__name__}: {exc}"[:500]
                    logger.error("compliance_ingestion_failed", document_id=document_id, error=str(exc))

                await session.commit()
        finally:
            current_organization_id.reset(token)

    async def _extract_chunk_embed(
        self, document: ComplianceDocument
    ) -> tuple[list[str], list[str], list[list[float]]]:
        settings = get_settings()
        client = get_storage_client()

        def _download() -> bytes:
            response = client.get_object(settings.minio_bucket, document.storage_key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        pdf_bytes = await anyio.to_thread.run_sync(_download)
        pages = extract_pages(pdf_bytes)
        chunks = chunk_pages(pages)
        if not chunks:
            raise PdfExtractionError("no extractable text found in PDF")

        embeddings = get_embeddings()
        vectors = await embeddings.aembed_documents(chunks)
        return pages, chunks, vectors


_worker: IngestionWorker | None = None


def get_ingestion_worker() -> IngestionWorker:
    global _worker
    if _worker is None:
        _worker = IngestionWorker()
    return _worker
