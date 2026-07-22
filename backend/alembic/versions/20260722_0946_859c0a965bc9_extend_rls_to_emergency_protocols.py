"""extend rls to emergency protocols

Revision ID: 859c0a965bc9
Revises: 5c19f87c74bd
Create Date: 2026-07-22 09:46:03.764037

Same treatment as every prior RLS extension. No new GRANTs needed for
`sentinel_app`: the original tenant-isolation-rls migration's `ALTER
DEFAULT PRIVILEGES` covers every table the owning role creates from then on.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "859c0a965bc9"
down_revision: str | None = "5c19f87c74bd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "emergency_protocols"


def upgrade() -> None:
    op.execute(f"ALTER TABLE {_TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {_TABLE}
            USING (organization_id = current_setting('app.current_organization_id', true)::uuid)
            WITH CHECK (organization_id = current_setting('app.current_organization_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {_TABLE}")
    op.execute(f"ALTER TABLE {_TABLE} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_TABLE} DISABLE ROW LEVEL SECURITY")
