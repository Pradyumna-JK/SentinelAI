"""seed risk write permission

Revision ID: 810b77bb5b78
Revises: 58d473a67289
Create Date: 2026-07-22 00:45:44.406598

Same idempotent pattern as 4b11427a1a6e (seed additional rbac permissions):
ON CONFLICT DO NOTHING throughout, since d1e29503faf3 (the original seed
migration) reads app.core.permissions live and would already have inserted
this code + grant on a fresh install where it now appears in
ALL_PERMISSIONS/DEFAULT_ROLE_PERMISSIONS before that migration ever runs.
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.permissions import ALL_PERMISSIONS, DEFAULT_ROLE_PERMISSIONS, RISK_WRITE, SYSTEM_ROLES

revision: str = "810b77bb5b78"
down_revision: str | None = "58d473a67289"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()

    permission_id = uuid.uuid4()
    bind.execute(
        sa.text(
            "INSERT INTO permissions (id, code, description) VALUES (:id, :code, :description) "
            "ON CONFLICT (code) DO NOTHING"
        ),
        {"id": permission_id, "code": RISK_WRITE, "description": ALL_PERMISSIONS[RISK_WRITE]},
    )

    resolved_id = bind.execute(
        sa.text("SELECT id FROM permissions WHERE code = :code"), {"code": RISK_WRITE}
    ).scalar_one()

    role_ids = {
        row.name: row.id
        for row in bind.execute(sa.text("SELECT id, name FROM roles")).mappings()
    }
    for role_name in SYSTEM_ROLES:
        if RISK_WRITE not in DEFAULT_ROLE_PERMISSIONS.get(role_name, ()):
            continue
        role_id = role_ids.get(role_name)
        if role_id is None:
            continue
        bind.execute(
            sa.text(
                "INSERT INTO role_permissions (role_id, permission_id) "
                "VALUES (:role_id, :permission_id) ON CONFLICT DO NOTHING"
            ),
            {"role_id": role_id, "permission_id": resolved_id},
        )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN "
            "(SELECT id FROM permissions WHERE code = :code)"
        ),
        {"code": RISK_WRITE},
    )
    bind.execute(sa.text("DELETE FROM permissions WHERE code = :code"), {"code": RISK_WRITE})
