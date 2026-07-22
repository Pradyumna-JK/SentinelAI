"""seed emergency permissions

Revision ID: a7e8870b7317
Revises: 859c0a965bc9
Create Date: 2026-07-22 09:46:26.153210

Same idempotent pattern as 94a7aa46a8c0 (seed sensor/permit/maintenance/
shift permissions).
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.permissions import ALL_PERMISSIONS, DEFAULT_ROLE_PERMISSIONS, EMERGENCY_READ, EMERGENCY_WRITE, SYSTEM_ROLES

revision: str = "a7e8870b7317"
down_revision: str | None = "859c0a965bc9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_CODES = (EMERGENCY_READ, EMERGENCY_WRITE)


def upgrade() -> None:
    bind = op.get_bind()
    role_ids = {row.name: row.id for row in bind.execute(sa.text("SELECT id, name FROM roles")).mappings()}

    for code in _NEW_CODES:
        permission_id = uuid.uuid4()
        bind.execute(
            sa.text(
                "INSERT INTO permissions (id, code, description) VALUES (:id, :code, :description) "
                "ON CONFLICT (code) DO NOTHING"
            ),
            {"id": permission_id, "code": code, "description": ALL_PERMISSIONS[code]},
        )
        resolved_id = bind.execute(
            sa.text("SELECT id FROM permissions WHERE code = :code"), {"code": code}
        ).scalar_one()

        for role_name in SYSTEM_ROLES:
            if code not in DEFAULT_ROLE_PERMISSIONS.get(role_name, ()):
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
    for code in _NEW_CODES:
        bind.execute(
            sa.text(
                "DELETE FROM role_permissions WHERE permission_id IN "
                "(SELECT id FROM permissions WHERE code = :code)"
            ),
            {"code": code},
        )
        bind.execute(sa.text("DELETE FROM permissions WHERE code = :code"), {"code": code})
