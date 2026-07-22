"""seed demo sensor permit maintenance shift data

Revision ID: a824c497a505
Revises: 94a7aa46a8c0
Create Date: 2026-07-22 09:27:03.575222

Seeds the flagship scenario the problem statement names directly: a hot-work
permit active in the same zone (Chemical Storage / ZONE-03) as an elevated
gas reading, simultaneously overlapping active maintenance and a recent
shift changeover — all four signals the Compound Risk Intelligence Engine
correlates, present at once, so that engine has something real to detect
the moment it's built instead of waiting on the sensor simulator's first
few ticks to coincidentally produce an anomaly.
"""

import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta, time, timezone

import sqlalchemy as sa
from alembic import op

from app.core.config import get_settings

revision: str = "a824c497a505"
down_revision: str | None = "94a7aa46a8c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SENSOR_NAME = "Chemical Storage Gas Sensor"
_EQUIPMENT_NAME = "Chemical Storage Ventilation Unit"
_PERMIT_DESCRIPTION = "Hot work - pipe repair near chemical storage racking"
_SHIFT_NAME = "Day Shift"


def upgrade() -> None:
    settings = get_settings()
    bind = op.get_bind()

    org_id = bind.execute(
        sa.text("SELECT id FROM organizations WHERE slug = :slug"),
        {"slug": settings.default_organization_slug},
    ).scalar_one()
    zone_id = bind.execute(
        sa.text("SELECT id FROM zones WHERE organization_id = :org_id AND code = 'ZONE-03'"),
        {"org_id": org_id},
    ).scalar_one()
    factory_id = bind.execute(
        sa.text("SELECT id FROM factories WHERE organization_id = :org_id AND code = 'FAC-01'"),
        {"org_id": org_id},
    ).scalar_one()
    admin_id = None
    if settings.admin_email:
        admin_id = bind.execute(
            sa.text("SELECT id FROM users WHERE email = :email"), {"email": settings.admin_email}
        ).scalar_one_or_none()

    now = datetime.now(timezone.utc)

    sensor_id = uuid.uuid4()
    bind.execute(
        sa.text(
            "INSERT INTO sensor_devices (id, organization_id, zone_id, sensor_type, name, unit, "
            "baseline_min, baseline_max, created_at) VALUES "
            "(:id, :org_id, :zone_id, 'gas', :name, 'ppm', 0, 50, :now)"
        ),
        {"id": sensor_id, "org_id": org_id, "zone_id": zone_id, "name": _SENSOR_NAME, "now": now},
    )
    bind.execute(
        sa.text(
            "INSERT INTO sensor_readings (id, organization_id, sensor_id, value, is_anomaly, recorded_at) "
            "VALUES (:id, :org_id, :sensor_id, 68.4, true, :now)"
        ),
        {"id": uuid.uuid4(), "org_id": org_id, "sensor_id": sensor_id, "now": now},
    )

    equipment_id = uuid.uuid4()
    bind.execute(
        sa.text(
            "INSERT INTO equipment (id, organization_id, zone_id, name, equipment_type, criticality, created_at) "
            "VALUES (:id, :org_id, :zone_id, :name, 'ventilation', 'High', :now)"
        ),
        {"id": equipment_id, "org_id": org_id, "zone_id": zone_id, "name": _EQUIPMENT_NAME, "now": now},
    )
    bind.execute(
        sa.text(
            "INSERT INTO maintenance_records (id, organization_id, equipment_id, status, technician, "
            "window_start, window_end, created_at) VALUES "
            "(:id, :org_id, :equipment_id, 'in_progress', 'Contract Technician', :start, :end, :now)"
        ),
        {
            "id": uuid.uuid4(), "org_id": org_id, "equipment_id": equipment_id,
            "start": now - timedelta(minutes=30), "end": now + timedelta(minutes=30), "now": now,
        },
    )

    bind.execute(
        sa.text(
            "INSERT INTO work_permits (id, organization_id, zone_id, permit_type, status, description, "
            "issued_by, valid_from, valid_to, created_at) VALUES "
            "(:id, :org_id, :zone_id, 'hot_work', 'active', :description, :issued_by, :from_, :to_, :now)"
        ),
        {
            "id": uuid.uuid4(), "org_id": org_id, "zone_id": zone_id, "description": _PERMIT_DESCRIPTION,
            "issued_by": admin_id, "from_": now - timedelta(minutes=20), "to_": now + timedelta(hours=2), "now": now,
        },
    )

    shift_id = uuid.uuid4()
    bind.execute(
        sa.text(
            "INSERT INTO shifts (id, organization_id, factory_id, name, start_time, end_time, created_at) "
            "VALUES (:id, :org_id, :factory_id, :name, :start, :end, :now)"
        ),
        {
            "id": shift_id, "org_id": org_id, "factory_id": factory_id, "name": _SHIFT_NAME,
            "start": time(6, 0), "end": time(14, 0), "now": now,
        },
    )
    bind.execute(
        sa.text(
            "INSERT INTO shift_changeover_events (id, organization_id, factory_id, shift_id, changeover_at, created_at) "
            "VALUES (:id, :org_id, :factory_id, :shift_id, :changeover_at, :now)"
        ),
        {
            "id": uuid.uuid4(), "org_id": org_id, "factory_id": factory_id, "shift_id": shift_id,
            "changeover_at": now - timedelta(minutes=10), "now": now,
        },
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM shift_changeover_events WHERE shift_id IN (SELECT id FROM shifts WHERE name = :name)"), {"name": _SHIFT_NAME})
    bind.execute(sa.text("DELETE FROM shifts WHERE name = :name"), {"name": _SHIFT_NAME})
    bind.execute(sa.text("DELETE FROM work_permits WHERE description = :description"), {"description": _PERMIT_DESCRIPTION})
    bind.execute(sa.text("DELETE FROM maintenance_records WHERE equipment_id IN (SELECT id FROM equipment WHERE name = :name)"), {"name": _EQUIPMENT_NAME})
    bind.execute(sa.text("DELETE FROM equipment WHERE name = :name"), {"name": _EQUIPMENT_NAME})
    bind.execute(sa.text("DELETE FROM sensor_readings WHERE sensor_id IN (SELECT id FROM sensor_devices WHERE name = :name)"), {"name": _SENSOR_NAME})
    bind.execute(sa.text("DELETE FROM sensor_devices WHERE name = :name"), {"name": _SENSOR_NAME})
