"""extend rls to alerts incidents cameras

Revision ID: 1d0a764f027f
Revises: 1206f03685c5
Create Date: 2026-07-22 08:56:06.892428

Same treatment as every prior RLS extension (risk tables: c9d5400b7942,
compliance tables: 2f6f1b472232). No new GRANTs needed for `sentinel_app`:
the original tenant-isolation-rls migration's `ALTER DEFAULT PRIVILEGES`
covers every table the owning role creates from then on.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "1d0a764f027f"
down_revision: str | None = "1206f03685c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ("alerts", "incidents", "cameras")


def upgrade() -> None:
    for table in _TABLES:
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
    for table in reversed(_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
