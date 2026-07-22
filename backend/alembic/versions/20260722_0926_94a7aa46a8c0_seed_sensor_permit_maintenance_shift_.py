"""seed sensor permit maintenance shift permissions

Revision ID: 94a7aa46a8c0
Revises: 29626602660c
Create Date: 2026-07-22 09:26:35.905200

Same idempotent pattern as 810b77bb5b78/dacf428a4913, generalized to a list
of codes since this batch adds eight at once rather than one.
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.permissions import (
    ALL_PERMISSIONS,
    DEFAULT_ROLE_PERMISSIONS,
    MAINTENANCE_READ,
    MAINTENANCE_WRITE,
    PERMITS_READ,
    PERMITS_WRITE,
    SENSORS_READ,
    SENSORS_WRITE,
    SHIFTS_READ,
    SHIFTS_WRITE,
    SYSTEM_ROLES,
)

revision: str = "94a7aa46a8c0"
down_revision: str | None = "29626602660c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_CODES = (
    SENSORS_READ, SENSORS_WRITE, PERMITS_READ, PERMITS_WRITE,
    MAINTENANCE_READ, MAINTENANCE_WRITE, SHIFTS_READ, SHIFTS_WRITE,
)


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
