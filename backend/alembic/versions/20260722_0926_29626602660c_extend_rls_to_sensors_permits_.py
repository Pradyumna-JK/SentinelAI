"""extend rls to sensors permits maintenance shifts

Revision ID: 29626602660c
Revises: 6168573dc611
Create Date: 2026-07-22 09:26:15.108813

Same treatment as every prior RLS extension. No new GRANTs needed for
`sentinel_app`: the original tenant-isolation-rls migration's `ALTER
DEFAULT PRIVILEGES` covers every table the owning role creates from then on.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "29626602660c"
down_revision: str | None = "6168573dc611"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "sensor_devices",
    "sensor_readings",
    "work_permits",
    "equipment",
    "maintenance_records",
    "shifts",
    "shift_changeover_events",
)


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
