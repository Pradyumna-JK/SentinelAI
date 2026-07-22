"""PDF -> extracted text -> chunks. Pure functions: no DB, no HTTP, no
vector-store writes — app/ai/compliance/worker.py orchestrates those. Kept
separate so extraction/chunking can be unit-tested without a running
Chroma/Postgres/MinIO stack.
"""

import io

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.core.config import get_settings


class PdfExtractionError(Exception):
    """The PDF could not be parsed, or contained no extractable text."""


def extract_pages(pdf_bytes: bytes) -> list[str]:
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as exc:  # noqa: BLE001 — any parse failure -> one clear error type
        raise PdfExtractionError(f"could not parse PDF: {type(exc).__name__}: {exc}") from exc
    return [page.extract_text() or "" for page in reader.pages]


def chunk_pages(pages: list[str]) -> list[str]:
    """Join every page's text and re-split, rather than chunking each page
    independently — a chunk is allowed to span a page boundary, which
    matters for regulatory text where a clause continues onto the next
    page. Page numbers aren't retained per chunk as a result; citations
    reference the document + chunk index, not a page number (see
    app/schemas/compliance.py's ComplianceCitation).
    """
    settings = get_settings()
    full_text = "\n\n".join(p for p in pages if p.strip())
    if not full_text.strip():
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.compliance_chunk_size,
        chunk_overlap=settings.compliance_chunk_overlap,
    )
    return splitter.split_text(full_text)
