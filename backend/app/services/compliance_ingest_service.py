"""Document upload/management for the Compliance Copilot.

Owns the MinIO object (raw PDF bytes) and the ComplianceDocument row
(ingestion status); handing the actual extract/chunk/embed work off to the
background worker (app/ai/compliance/worker.py) is this service's last
step, not something it does inline — an upload request should return as
soon as the bytes are durably stored, not block on however long ingestion
takes.
"""

import io
import uuid

import anyio
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.compliance.vectorstore import delete_document as vector_delete_document
from app.ai.compliance.worker import IngestionWorker, get_ingestion_worker
from app.core.config import get_settings
from app.database.storage import get_storage_client
from app.db.session import get_db
from app.models.compliance import ComplianceDocument
from app.models.enums import DocumentStatus


class DocumentNotFoundError(Exception):
    pass


class InvalidDocumentError(Exception):
    """Wrong content type, oversized, or otherwise rejected before upload."""


class ComplianceIngestService:
    def __init__(self, db: AsyncSession, worker: IngestionWorker) -> None:
        self._db = db
        self._worker = worker
        self._settings = get_settings()

    async def upload_document(
        self,
        *,
        organization_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> ComplianceDocument:
        if content_type != "application/pdf" and not filename.lower().endswith(".pdf"):
            raise InvalidDocumentError("only PDF files are accepted")
        max_bytes = self._settings.compliance_max_upload_mb * 1024 * 1024
        if len(data) > max_bytes:
            raise InvalidDocumentError(f"file exceeds the {self._settings.compliance_max_upload_mb}MB limit")
        if len(data) == 0:
            raise InvalidDocumentError("file is empty")

        document_id = uuid.uuid4()
        storage_key = f"compliance/{organization_id}/{document_id}/{filename}"

        client = get_storage_client()
        settings = self._settings

        def _upload() -> None:
            client.put_object(
                settings.minio_bucket,
                storage_key,
                io.BytesIO(data),
                length=len(data),
                content_type="application/pdf",
            )

        await anyio.to_thread.run_sync(_upload)

        document = ComplianceDocument(
            id=document_id,
            organization_id=organization_id,
            uploaded_by=uploaded_by,
            filename=filename,
            storage_key=storage_key,
            content_type="application/pdf",
            size_bytes=len(data),
            status=DocumentStatus.PENDING,
        )
        self._db.add(document)
        await self._db.flush()
        await self._db.commit()

        self._worker.enqueue(document_id, organization_id)
        return document

    async def list_documents(self) -> list[ComplianceDocument]:
        result = await self._db.execute(select(ComplianceDocument).order_by(ComplianceDocument.created_at.desc()))
        return list(result.scalars())

    async def get_document(self, document_id: uuid.UUID) -> ComplianceDocument:
        document = await self._db.get(ComplianceDocument, document_id)
        if document is None:
            raise DocumentNotFoundError()
        return document

    async def delete_document(self, document_id: uuid.UUID) -> None:
        document = await self.get_document(document_id)
        organization_id = str(document.organization_id)

        client = get_storage_client()
        settings = self._settings
        try:
            await anyio.to_thread.run_sync(
                lambda: client.remove_object(settings.minio_bucket, document.storage_key)
            )
        except Exception:  # noqa: BLE001 — proceed with DB/Chroma cleanup even if the object is already gone
            pass
        await anyio.to_thread.run_sync(
            lambda: vector_delete_document(organization_id=organization_id, document_id=str(document_id))
        )
        await self._db.delete(document)
        await self._db.commit()


def get_compliance_ingest_service(
    db: AsyncSession = Depends(get_db),
    worker: IngestionWorker = Depends(get_ingestion_worker),
) -> ComplianceIngestService:
    return ComplianceIngestService(db, worker)
