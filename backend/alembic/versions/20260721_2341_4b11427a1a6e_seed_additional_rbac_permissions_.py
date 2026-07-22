"""seed additional rbac permissions (facility hierarchy)

Revision ID: 4b11427a1a6e
Revises: 52b241967788
Create Date: 2026-07-21 23:41:13.577038

Adds the 8 permission codes introduced for the facility hierarchy
(factories/sites/buildings/zones :read/:write) and grants them to the 5
system roles per app/core/permissions.py's current DEFAULT_ROLE_PERMISSIONS.
The original seed migration (d1e29503faf3) already ran against the live
database *before* these 8 codes existed, so it only ever inserted the
original 13 — this migration adds exactly the delta.

Written with `ON CONFLICT DO NOTHING` rather than assuming that delta,
though: `d1e29503faf3` reads `app.core.permissions` constants *live*, so a
fresh `alembic upgrade head` from an empty database today would have that
earlier migration insert all 21 current permissions immediately, and this
one would then be inserting a set that already exists. Idempotent by
construction covers both "replaying real history" and "fresh install"
without needing two different code paths.
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.permissions import ALL_PERMISSIONS, DEFAULT_ROLE_PERMISSIONS, SYSTEM_ROLES

revision: str = "4b11427a1a6e"
down_revision: str | None = "52b241967788"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_CODES = (
    "factories:read",
    "factories:write",
    "sites:read",
    "sites:write",
    "buildings:read",
    "buildings:write",
    "zones:read",
    "zones:write",
)


def upgrade() -> None:
    bind = op.get_bind()

    for code in _NEW_CODES:
        bind.execute(
            sa.text(
                "INSERT INTO permissions (id, code, description) "
                "VALUES (:id, :code, :description) ON CONFLICT (code) DO NOTHING"
            ),
            {"id": uuid.uuid4(), "code": code, "description": ALL_PERMISSIONS[code]},
        )

    role_ids = {
        row.name: row.id
        for row in bind.execute(sa.text("SELECT id, name FROM roles")).mappings()
    }
    permission_ids = {
        row.code: row.id
        for row in bind.execute(
            sa.text("SELECT id, code FROM permissions WHERE code IN :codes").bindparams(
                sa.bindparam("codes", expanding=True)
            ),
            {"codes": list(_NEW_CODES)},
        ).mappings()
    }

    for role_name in SYSTEM_ROLES:
        role_id = role_ids.get(role_name)
        if role_id is None:
            continue
        for code in DEFAULT_ROLE_PERMISSIONS.get(role_name, ()):
            if code not in _NEW_CODES:
                continue  # already granted by the original seed migration
            permission_id = permission_ids.get(code)
            if permission_id is None:
                continue
            bind.execute(
                sa.text(
                    "INSERT INTO role_permissions (role_id, permission_id) "
                    "VALUES (:role_id, :permission_id) ON CONFLICT DO NOTHING"
                ),
                {"role_id": role_id, "permission_id": permission_id},
            )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN "
            "(SELECT id FROM permissions WHERE code IN :codes)"
        ).bindparams(sa.bindparam("codes", expanding=True)),
        {"codes": list(_NEW_CODES)},
    )
    bind.execute(
        sa.text("DELETE FROM permissions WHERE code IN :codes").bindparams(
            sa.bindparam("codes", expanding=True)
        ),
        {"codes": list(_NEW_CODES)},
    )
