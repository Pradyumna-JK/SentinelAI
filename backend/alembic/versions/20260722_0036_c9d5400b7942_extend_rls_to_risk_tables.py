"""extend rls to risk tables

Revision ID: c9d5400b7942
Revises: 3df528190e3f
Create Date: 2026-07-22 00:36:56.828752

Same treatment as the original tenant-isolation-rls migration
(52b241967788), extended to the two new risk tables. No new GRANTs needed
for `sentinel_app`: that migration's `ALTER DEFAULT PRIVILEGES IN SCHEMA
public GRANT ... ON TABLES` applies to every table the owning role creates
from then on, including these two, created here by that same role.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c9d5400b7942"
down_revision: str | None = "3df528190e3f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ("risk_events", "risk_score_snapshots")


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
