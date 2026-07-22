"""seed camera write permission

Revision ID: dacf428a4913
Revises: 1d0a764f027f
Create Date: 2026-07-22 08:56:26.392982

Same idempotent pattern as 810b77bb5b78 (seed risk write permission):
ON CONFLICT DO NOTHING throughout, since the original seed migration reads
app.core.permissions live and would already have inserted this code+grant
on a fresh install where it now appears in ALL_PERMISSIONS before that
migration ever runs.
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.permissions import ALL_PERMISSIONS, CAMERA_WRITE, DEFAULT_ROLE_PERMISSIONS, SYSTEM_ROLES

revision: str = "dacf428a4913"
down_revision: str | None = "1d0a764f027f"
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
        {"id": permission_id, "code": CAMERA_WRITE, "description": ALL_PERMISSIONS[CAMERA_WRITE]},
    )

    resolved_id = bind.execute(
        sa.text("SELECT id FROM permissions WHERE code = :code"), {"code": CAMERA_WRITE}
    ).scalar_one()

    role_ids = {
        row.name: row.id
        for row in bind.execute(sa.text("SELECT id, name FROM roles")).mappings()
    }
    for role_name in SYSTEM_ROLES:
        if CAMERA_WRITE not in DEFAULT_ROLE_PERMISSIONS.get(role_name, ()):
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
        {"code": CAMERA_WRITE},
    )
    bind.execute(sa.text("DELETE FROM permissions WHERE code = :code"), {"code": CAMERA_WRITE})
