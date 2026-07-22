"""auth role (bypassrls, auth-domain grants only)

Revision ID: 38039e033cd7
Revises: bf8da21f3038
Create Date: 2026-07-21 23:57:10.775307

Creates `sentinel_auth`: the role AuthService's dedicated engine connects
as (app/core/database.py's get_auth_engine). Exists because enabling RLS on
`users` (migration 52b241967788) correctly broke pre-authentication lookups
— login must find a user by email *before* any tenant context exists, and
the RLS policy (rightly) returns zero rows without one. Discovered live:
after that migration shipped, every login returned 401.

BYPASSRLS + narrowly-scoped grants, rather than a policy carve-out on the
`users` table itself (e.g. `OR current_setting(...) IS NULL`), because a
carve-out would weaken the table's protection for *every* connection —
including `sentinel_app` — while a separate role confines the exception to
the one code path that needs it, enforced by the database, auditable in
pg_roles. It gets NOTHING outside the auth domain: no factories, sites,
buildings, zones. See app/core/config.py's `auth_db_user` docstring.
"""

from collections.abc import Sequence

from alembic import op

from app.core.config import get_settings

revision: str = "38039e033cd7"
down_revision: str | None = "bf8da21f3038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Every table this role can touch, with the minimum verbs AuthService uses:
# - users: find by email/id, update last_login_at / hashed_password
# - refresh_tokens / password_reset_tokens: full lifecycle ownership
# - RBAC tables: read-only, to resolve roles+permissions into JWT claims
_GRANTS = {
    "users": "SELECT, UPDATE",
    "refresh_tokens": "SELECT, INSERT, UPDATE, DELETE",
    "password_reset_tokens": "SELECT, INSERT, UPDATE, DELETE",
    "roles": "SELECT",
    "permissions": "SELECT",
    "role_permissions": "SELECT",
    "user_roles": "SELECT",
}


def _ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def upgrade() -> None:
    settings = get_settings()
    auth_password = settings.auth_db_password.get_secret_value() if settings.auth_db_password else None
    if not auth_password:
        print(
            "WARNING: SENTINEL_AUTH_DB_USER/SENTINEL_AUTH_DB_PASSWORD not set — "
            "skipping creation of the auth role. Login will FAIL while RLS is "
            "enabled on `users` unless auth_database_url resolves to a role "
            "that can read that table without a tenant context."
        )
        return

    auth_user = settings.auth_db_user or "sentinel_auth"
    user_sql = _ident(auth_user)
    db_sql = _ident(settings.postgres_db)

    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = {_literal(auth_user)}) THEN
                CREATE ROLE {user_sql} LOGIN BYPASSRLS PASSWORD {_literal(auth_password)};
            ELSE
                ALTER ROLE {user_sql} WITH LOGIN BYPASSRLS PASSWORD {_literal(auth_password)};
            END IF;
        END
        $$;
        """
    )
    op.execute(f"GRANT CONNECT ON DATABASE {db_sql} TO {user_sql}")
    op.execute(f"GRANT USAGE ON SCHEMA public TO {user_sql}")
    for table, verbs in _GRANTS.items():
        op.execute(f"GRANT {verbs} ON {table} TO {user_sql}")


def downgrade() -> None:
    settings = get_settings()
    auth_user = settings.auth_db_user or "sentinel_auth"
    user_sql = _ident(auth_user)
    db_sql = _ident(settings.postgres_db)

    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = {_literal(auth_user)}) THEN
                REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {user_sql};
                REVOKE USAGE ON SCHEMA public FROM {user_sql};
                REVOKE CONNECT ON DATABASE {db_sql} FROM {user_sql};
                DROP ROLE {user_sql};
            END IF;
        END
        $$;
        """
    )
