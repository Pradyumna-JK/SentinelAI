"""ChromaDB client + the one and only tenant-safe read/write path.

A single collection ("compliance_documents") serves every organization,
rather than one Chroma collection per tenant. That's a deliberate choice,
not a shortcut: a per-tenant collection would need its own provisioning
step (create-on-first-upload, list-and-filter-by-prefix to enumerate them,
etc.) — a second tenant-isolation mechanism to keep in sync with the first.
Instead this module reuses the exact discipline already established for
Postgres (RLS policies, app/core/tenancy.py's TenantScoped ORM filter):
every write stores `organization_id` as chunk metadata, and — critically —
`query()` below is the *only* function in this module that reads from the
collection, and it always includes `organization_id` in its `where` filter.
There is no raw-client escape hatch exposed; nothing outside this module
ever gets a `Collection` object to query directly.

Cosine distance space (`hnsw:space: cosine`) is configured explicitly
rather than relying on Chroma's default (L2) — cosine is the standard
choice for normalized text embeddings, and `1 - distance` then reads
directly as a similarity score in [0, 1] for `compliance_min_relevance_score`
(app/core/config.py) to threshold against.
"""

from functools import lru_cache

import chromadb
import structlog

from app.ai.compliance.types import RetrievedChunk
from app.core.config import get_settings

logger = structlog.get_logger("sentinel.compliance.vectorstore")

_COLLECTION_NAME = "compliance_documents"


@lru_cache
def get_chroma_client() -> chromadb.HttpClient:
    settings = get_settings()
    return chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)


def _get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def add_chunks(
    *,
    organization_id: str,
    document_id: str,
    title: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    """Upsert one document's chunks. `ids` are `{document_id}:{chunk_index}`
    so re-ingesting the same document (e.g. after a fix-and-retry) overwrites
    its previous chunks instead of duplicating them.
    """
    if not chunks:
        return
    collection = _get_collection()
    ids = [f"{document_id}:{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "organization_id": organization_id,
            "document_id": document_id,
            "title": title,
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]
    collection.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)


def delete_document(*, organization_id: str, document_id: str) -> None:
    """Remove every chunk belonging to one document. `organization_id` is
    included in the filter even though `document_id` alone would already be
    unique — never construct a Chroma delete/query filter without it; that
    invariant is exactly what makes this module's tenant isolation hold.
    """
    collection = _get_collection()
    collection.delete(where={"$and": [{"organization_id": organization_id}, {"document_id": document_id}]})


def query(*, organization_id: str, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
    collection = _get_collection()
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"organization_id": organization_id},
    )
    ids = result.get("ids") or [[]]
    documents = result.get("documents") or [[]]
    metadatas = result.get("metadatas") or [[]]
    distances = result.get("distances") or [[]]
    if not ids or not ids[0]:
        return []

    chunks: list[RetrievedChunk] = []
    for doc_text, metadata, distance in zip(documents[0], metadatas[0], distances[0]):
        chunks.append(
            RetrievedChunk(
                document_id=str(metadata.get("document_id", "")),
                title=str(metadata.get("title", "")),
                chunk_index=int(metadata.get("chunk_index", 0)),
                text=doc_text,
                similarity=round(1.0 - distance, 4),
            )
        )
    return chunks


async def check_vectorstore() -> None:
    """Raise if Chroma is unreachable. Used by /health."""
    import anyio

    client = get_chroma_client()
    await anyio.to_thread.run_sync(client.heartbeat)
