"""extend rls to compliance tables

Revision ID: 2f6f1b472232
Revises: 900e3391549b
Create Date: 2026-07-22 08:08:02.020634

Same treatment as the risk-tables RLS extension (c9d5400b7942), applied to
the three new Compliance Copilot tables. No new GRANTs needed for
`sentinel_app`: the original tenant-isolation-rls migration's `ALTER
DEFAULT PRIVILEGES IN SCHEMA public GRANT ... ON TABLES` covers every table
the owning role creates from then on, including these three.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "2f6f1b472232"
down_revision: str | None = "900e3391549b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ("compliance_documents", "compliance_chat_sessions", "compliance_chat_messages")


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
