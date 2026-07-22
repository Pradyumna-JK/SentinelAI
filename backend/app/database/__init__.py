"""Non-relational infrastructure clients.

- ``redis``   — async Redis client (cache / pub-sub / rate limiting)
- ``storage`` — MinIO S3-compatible object storage (evidence frames, exports)

PostgreSQL lives in app/core/database.py (engine) and app/db/session.py
(sessions), not here — this package is only for the non-SQL dependencies.

Both clients are created lazily on first use so importing the app never
requires live infrastructure (unit tests, alembic autogenerate, tooling).
Each module exposes a ``check_*`` coroutine consumed by /health.
"""
