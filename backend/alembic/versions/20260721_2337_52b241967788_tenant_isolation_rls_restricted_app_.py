"""tenant isolation rls (restricted app role + row level security)

Revision ID: 52b241967788
Revises: 99f0a9b23be2
Create Date: 2026-07-21 23:37:48.104164

Layer 2 of tenant isolation — the backstop for the ORM-level filter in
app/core/tenancy.py. Two parts, and both matter:

1. A new, unprivileged Postgres role (`sentinel_app`) that the running
   application connects as (see app/core/database.py / app_database_url).
   This migration keeps running as the *owner* role (SENTINEL_POSTGRES_USER,
   e.g. "sentinel") — which, in this stack's postgres:16-alpine image, was
   created as a superuser during `initdb` bootstrap. Superusers bypass Row-
   Level Security unconditionally, no exceptions. If the app queried using
   that same owner role, every RLS policy below would be a no-op for it —
   which is *why* a second, non-superuser role has to exist at all.

2. `FORCE ROW LEVEL SECURITY` on every tenant-scoped table, with a policy
   keyed to the Postgres session variable `app.current_organization_id`
   (set per-request/transaction by app/db/session.py's `get_db()`, sourced
   from the same JWT claim the ORM-level filter uses — see
   OrganizationContextMiddleware in app/core/middleware.py). `current_setting(
   ..., true)` (missing_ok) returns NULL when that variable was never set (a
   raw psql session, a future admin tool that forgot to call `get_db()`'s
   equivalent), and `organization_id = NULL` is never true in SQL — so an
   unscoped connection sees zero rows, not everything. Fail-closed by
   construction, not by convention.

Role names/passwords are DDL, not DML — Postgres's CREATE/ALTER ROLE don't
accept client-side bind parameters (`DO $$ ... $$` blocks don't have an
argument list at all), so values are escaped in Python and embedded as SQL
literals here, the same way `psycopg2.sql`/`asyncpg` do it internally.
These values come from operator-controlled Settings, not request input.
"""

from collections.abc import Sequence

from alembic import op

from app.core.config import get_settings

revision: str = "52b241967788"
down_revision: str | None = "99f0a9b23be2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TENANT_SCOPED_TABLES = ("users", "factories", "sites", "buildings", "zones")


def _ident(value: str) -> str:
    """Quote a SQL identifier (role/database name)."""
    return '"' + value.replace('"', '""') + '"'


def _literal(value: str) -> str:
    """Quote a SQL string literal (password)."""
    return "'" + value.replace("'", "''") + "'"


def upgrade() -> None:
    settings = get_settings()
    app_password = settings.app_db_password.get_secret_value() if settings.app_db_password else None

    if not app_password:
        print(
            "WARNING: SENTINEL_APP_DB_USER/SENTINEL_APP_DB_PASSWORD not set — "
            "skipping creation of the restricted app role. RLS policies "
            "will still be created and enforced, but the application will "
            "keep connecting as the schema-owning (superuser) role and "
            "bypass them entirely. Set both and re-run to close this gap."
        )
    else:
        app_user = settings.app_db_user or "sentinel_app"
        user_sql = _ident(app_user)
        password_sql = _literal(app_password)
        db_sql = _ident(settings.postgres_db)

        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = {_literal(app_user)}) THEN
                    CREATE ROLE {user_sql} LOGIN PASSWORD {password_sql};
                ELSE
                    ALTER ROLE {user_sql} WITH PASSWORD {password_sql};
                END IF;
            END
            $$;
            """
        )
        op.execute(f"GRANT CONNECT ON DATABASE {db_sql} TO {user_sql}")
        op.execute(f"GRANT USAGE ON SCHEMA public TO {user_sql}")
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {user_sql}")
        # So a *future* migration's new table is automatically usable by the
        # app role too, without needing a matching GRANT of its own.
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {user_sql}"
        )
        # alembic_version isn't tenant data and the app has no business
        # writing to it — no reason to leave it reachable.
        op.execute(f"REVOKE ALL ON alembic_version FROM {user_sql}")

    for table in _TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
                USING (organization_id = current_setting('app.current_organization_id', true)::uuid)
                WITH CHECK (organization_id = current_setting('app.current_organization_id', true)::uuid)
            """
        )


def downgrade() -> None:
    for table in reversed(_TENANT_SCOPED_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    settings = get_settings()
    app_user = settings.app_db_user or "sentinel_app"
    user_sql = _ident(app_user)
    db_sql = _ident(settings.postgres_db)

    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = {_literal(app_user)}) THEN
                ALTER DEFAULT PRIVILEGES IN SCHEMA public
                    REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM {user_sql};
                REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {user_sql};
                REVOKE USAGE ON SCHEMA public FROM {user_sql};
                REVOKE CONNECT ON DATABASE {db_sql} FROM {user_sql};
                DROP ROLE {user_sql};
            END IF;
        END
        $$;
        """
    )
