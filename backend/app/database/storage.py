"""MinIO S3-compatible object storage (evidence frames, report exports).

The official ``minio`` client is synchronous; every call is dispatched to a
worker thread via anyio so the event loop is never blocked.
"""

from functools import lru_cache

import anyio
import urllib3
from minio import Minio

from app.core.config import get_settings


@lru_cache
def get_storage_client() -> Minio:
    settings = get_settings()
    # The client's default urllib3 policy (5 retries with backoff) turns a
    # storage outage into a ~40s stall per call. Bounded timeouts + a single
    # retry keep probes fast; callers decide their own retry strategy.
    http_client = urllib3.PoolManager(
        timeout=urllib3.Timeout(connect=2.0, read=5.0),
        retries=urllib3.Retry(total=1, backoff_factor=0.2),
    )
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key.get_secret_value(),
        secure=settings.minio_secure,
        http_client=http_client,
    )


async def check_storage() -> None:
    """Raise if MinIO is unreachable. Used by /health."""
    client = get_storage_client()
    bucket = get_settings().minio_bucket
    await anyio.to_thread.run_sync(client.bucket_exists, bucket)


async def ensure_bucket() -> None:
    """Create the evidence bucket on startup if it does not exist yet."""
    client = get_storage_client()
    bucket = get_settings().minio_bucket

    def _ensure() -> None:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)

    await anyio.to_thread.run_sync(_ensure)
