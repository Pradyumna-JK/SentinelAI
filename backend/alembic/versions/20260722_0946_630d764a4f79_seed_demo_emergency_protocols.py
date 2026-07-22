"""seed demo emergency protocols

Revision ID: 630d764a4f79
Revises: a7e8870b7317
Create Date: 2026-07-22 09:46:50.040219

Seeds a "general" fallback protocol plus an exact-match protocol for
"compound_gas_permit" — the hazard_class the Compound Risk Intelligence
Engine emits for exactly the problem statement's flagship scenario (a
hot-work/confined-space permit active alongside a gas anomaly), so the
demo shows a genuine high-confidence protocol match, not just the fallback.
"""

import uuid
from collections.abc import Sequence
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

from app.core.config import get_settings

revision: str = "630d764a4f79"
down_revision: str | None = "a7e8870b7317"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_GENERAL_ROUTE = "Nearest marked exit; muster at the main gate assembly point."
_GAS_PERMIT_ROUTE = "Evacuate via the north corridor away from the storage racking; muster at the secondary assembly point, upwind."


def upgrade() -> None:
    settings = get_settings()
    bind = op.get_bind()

    org_id = bind.execute(
        sa.text("SELECT id FROM organizations WHERE slug = :slug"),
        {"slug": settings.default_organization_slug},
    ).scalar_one()

    now = datetime.now(timezone.utc)
    bind.execute(
        sa.text(
            "INSERT INTO emergency_protocols (id, organization_id, hazard_type, steps, evacuation_route, created_at) "
            "VALUES (:id, :org_id, 'general', CAST(:steps AS JSONB), :route, :now)"
        ),
        {
            "id": uuid.uuid4(), "org_id": org_id,
            "steps": '["Notify the shift supervisor", "Account for all personnel in the zone", "Await all-clear before re-entry"]',
            "route": _GENERAL_ROUTE, "now": now,
        },
    )
    bind.execute(
        sa.text(
            "INSERT INTO emergency_protocols (id, organization_id, hazard_type, steps, evacuation_route, created_at) "
            "VALUES (:id, :org_id, 'compound_gas_permit', CAST(:steps AS JSONB), :route, :now)"
        ),
        {
            "id": uuid.uuid4(), "org_id": org_id,
            "steps": '["Immediately suspend all hot work / spark-producing activity in the zone", '
            '"Evacuate non-essential personnel", "Ventilate the area and re-check gas levels before resuming work", '
            '"Notify the fire safety officer and log the exposure"]',
            "route": _GAS_PERMIT_ROUTE, "now": now,
        },
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM emergency_protocols WHERE hazard_type IN ('general', 'compound_gas_permit')"))
