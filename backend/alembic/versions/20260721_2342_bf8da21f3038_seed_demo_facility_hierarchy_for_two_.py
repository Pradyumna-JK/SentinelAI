"""seed demo facility hierarchy for two tenants

Revision ID: bf8da21f3038
Revises: 4b11427a1a6e
Create Date: 2026-07-21 23:42:32.769490

Adds a small Factory -> Site -> Building -> Zone hierarchy to the existing
default organization, AND creates a second organization ("Acme
Manufacturing") with its own admin user and its own hierarchy. The second
tenant exists specifically so cross-tenant isolation can be tested against
two real organizations rather than asserted against one — there is
currently no `POST /organizations` endpoint (not in this task's scope), so
seeding via migration is the only way to get a second tenant into the
system at all.

Both hierarchies reuse the same `code` values (e.g. "FAC-01", "SITE-01")
deliberately: codes are unique *per parent*, not globally (see
app/models/facility.py's UniqueConstraints), so two tenants safely using
identical codes is expected, not a collision — and is itself a small,
concrete demonstration that these identifiers are tenant-scoped.
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.config import get_settings
from app.core.permissions import ADMIN as ADMIN_ROLE_NAME
from app.core.security import hash_password

revision: str = "bf8da21f3038"
down_revision: str | None = "4b11427a1a6e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

organizations_table = sa.table(
    "organizations", sa.column("id", sa.UUID()), sa.column("name", sa.String()), sa.column("slug", sa.String())
)
factories_table = sa.table(
    "factories",
    sa.column("id", sa.UUID()),
    sa.column("organization_id", sa.UUID()),
    sa.column("name", sa.String()),
    sa.column("code", sa.String()),
)
sites_table = sa.table(
    "sites",
    sa.column("id", sa.UUID()),
    sa.column("organization_id", sa.UUID()),
    sa.column("factory_id", sa.UUID()),
    sa.column("name", sa.String()),
    sa.column("code", sa.String()),
)
buildings_table = sa.table(
    "buildings",
    sa.column("id", sa.UUID()),
    sa.column("organization_id", sa.UUID()),
    sa.column("site_id", sa.UUID()),
    sa.column("name", sa.String()),
    sa.column("code", sa.String()),
)
zones_table = sa.table(
    "zones",
    sa.column("id", sa.UUID()),
    sa.column("organization_id", sa.UUID()),
    sa.column("building_id", sa.UUID()),
    sa.column("name", sa.String()),
    sa.column("code", sa.String()),
    sa.column("zone_type", sa.String()),
)
users_table = sa.table(
    "users",
    sa.column("id", sa.UUID()),
    sa.column("organization_id", sa.UUID()),
    sa.column("email", sa.String()),
    sa.column("hashed_password", sa.String()),
    sa.column("full_name", sa.String()),
    sa.column("is_active", sa.Boolean()),
)
user_roles_table = sa.table("user_roles", sa.column("user_id", sa.UUID()), sa.column("role_id", sa.UUID()))


def upgrade() -> None:
    settings = get_settings()
    bind = op.get_bind()

    tenant1_id = bind.execute(
        sa.text("SELECT id FROM organizations WHERE slug = :slug"),
        {"slug": settings.default_organization_slug},
    ).scalar_one()
    _seed_hierarchy(
        bind,
        organization_id=tenant1_id,
        factory=("Riverside Manufacturing", "FAC-01"),
        site=("Riverside Plant 1", "SITE-01"),
        buildings=[
            ("Production Hall A", "BLDG-01", [
                ("Loading Dock A", "ZONE-01", "loading_dock"),
                ("Assembly Line 3", "ZONE-02", "assembly_line"),
            ]),
            ("Chemical Storage Block", "BLDG-02", [
                ("Chemical Storage", "ZONE-03", "storage"),
            ]),
        ],
    )

    tenant2_id = uuid.uuid4()
    bind.execute(
        sa.insert(organizations_table).values(
            id=tenant2_id, name="Acme Manufacturing", slug="acme-manufacturing"
        )
    )
    _seed_hierarchy(
        bind,
        organization_id=tenant2_id,
        factory=("Acme Plant", "FAC-01"),
        site=("Acme Site 1", "SITE-01"),
        buildings=[
            ("Warehouse 1", "BLDG-01", [
                ("Receiving Bay", "ZONE-01", "loading_dock"),
                ("Cold Storage", "ZONE-02", "storage"),
            ]),
        ],
    )

    if settings.admin_email and settings.admin_password:
        # Reuses the same bootstrap password as the primary demo admin —
        # this account exists purely so cross-tenant isolation can be
        # exercised against a second, real login, not as a separate secret
        # to manage.
        admin_id = uuid.uuid4()
        bind.execute(
            sa.insert(users_table).values(
                id=admin_id,
                organization_id=tenant2_id,
                email="admin@acme-manufacturing.demo",
                hashed_password=hash_password(settings.admin_password.get_secret_value()),
                full_name="Acme Admin",
                is_active=True,
            )
        )
        admin_role_id = bind.execute(
            sa.text("SELECT id FROM roles WHERE name = :name"), {"name": ADMIN_ROLE_NAME}
        ).scalar_one()
        bind.execute(sa.insert(user_roles_table).values(user_id=admin_id, role_id=admin_role_id))
    else:
        print(
            "WARNING: SENTINEL_ADMIN_EMAIL/SENTINEL_ADMIN_PASSWORD not set — "
            "skipping the second tenant's demo admin user. Its facility "
            "hierarchy was still seeded."
        )


def _seed_hierarchy(bind, *, organization_id, factory, site, buildings) -> None:
    factory_id = uuid.uuid4()
    bind.execute(
        sa.insert(factories_table).values(
            id=factory_id, organization_id=organization_id, name=factory[0], code=factory[1]
        )
    )
    site_id = uuid.uuid4()
    bind.execute(
        sa.insert(sites_table).values(
            id=site_id, organization_id=organization_id, factory_id=factory_id, name=site[0], code=site[1]
        )
    )
    for building_name, building_code, zones in buildings:
        building_id = uuid.uuid4()
        bind.execute(
            sa.insert(buildings_table).values(
                id=building_id,
                organization_id=organization_id,
                site_id=site_id,
                name=building_name,
                code=building_code,
            )
        )
        for zone_name, zone_code, zone_type in zones:
            bind.execute(
                sa.insert(zones_table).values(
                    id=uuid.uuid4(),
                    organization_id=organization_id,
                    building_id=building_id,
                    name=zone_name,
                    code=zone_code,
                    zone_type=zone_type,
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    # Cascades (organizations -> factories/sites/buildings/zones/users, all
    # ON DELETE CASCADE) clean up everything tenant2 owns in one statement.
    bind.execute(sa.text("DELETE FROM organizations WHERE slug = 'acme-manufacturing'"))

    settings = get_settings()
    tenant1_id = bind.execute(
        sa.text("SELECT id FROM organizations WHERE slug = :slug"),
        {"slug": settings.default_organization_slug},
    ).scalar_one()
    # Deleting the factory cascades to its sites/buildings/zones; the
    # organization itself (and its pre-existing users) is left untouched.
    bind.execute(
        sa.text("DELETE FROM factories WHERE organization_id = :org_id AND code = 'FAC-01'"),
        {"org_id": tenant1_id},
    )
