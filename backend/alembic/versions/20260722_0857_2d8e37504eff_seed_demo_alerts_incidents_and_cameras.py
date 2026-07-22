"""seed demo alerts incidents and cameras

Revision ID: 2d8e37504eff
Revises: dacf428a4913
Create Date: 2026-07-22 08:57:02.145971

Gives the primary demo tenant ("SentinelAI Demo") a starting set of
cameras/alerts/incidents so the dashboard isn't empty the moment these
modules stop being dummy data — the same three zones (ZONE-01/02/03) the
facility-hierarchy seed migration already created. Downgrade matches rows
by their exact seeded name/message/title (scoped to this org), not a
blanket delete-by-zone, so it can't clobber unrelated rows created later
by real usage or live-testing.
"""

import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from alembic import op

from app.core.config import get_settings

revision: str = "2d8e37504eff"
down_revision: str | None = "dacf428a4913"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CAMERA_NAMES = ("Dock A - North", "Assembly Line 3 - Overview", "Chemical Storage - Entrance")
_ALERT_MESSAGES = (
    "PPE violation detected correlated with elevated gas reading",
    "Unusual vibration pattern detected on conveyor motor",
    "Restricted zone intrusion - low confidence detection",
)
_INCIDENT_TITLES = ("PPE Violation - Loading Dock A", "Vibration Anomaly - Assembly Line 3")


def upgrade() -> None:
    settings = get_settings()
    bind = op.get_bind()

    org_id = bind.execute(
        sa.text("SELECT id FROM organizations WHERE slug = :slug"),
        {"slug": settings.default_organization_slug},
    ).scalar_one()

    zone_ids = {
        row.code: row.id
        for row in bind.execute(
            sa.text("SELECT id, code FROM zones WHERE organization_id = :org_id"), {"org_id": org_id}
        ).mappings()
    }
    dock_a, assembly_3, chem_storage = zone_ids["ZONE-01"], zone_ids["ZONE-02"], zone_ids["ZONE-03"]

    admin_id = None
    if settings.admin_email:
        admin_id = bind.execute(
            sa.text("SELECT id FROM users WHERE email = :email"), {"email": settings.admin_email}
        ).scalar_one_or_none()

    now = datetime.now(timezone.utc)

    bind.execute(
        sa.text(
            "INSERT INTO cameras (id, organization_id, zone_id, name, stream_url, status, resolution, fps, "
            "layout_x, layout_y, created_at) VALUES "
            "(:id, :org_id, :zone_id, :name, :url, :status, :res, :fps, :x, :y, :now)"
        ),
        [
            {
                "id": uuid.uuid4(), "org_id": org_id, "zone_id": dock_a, "name": _CAMERA_NAMES[0],
                "url": "https://cdn.sentinelai.demo/hls/cam1.m3u8", "status": "active",
                "res": "1920x1080", "fps": 24, "x": 20.0, "y": 15.0, "now": now,
            },
            {
                "id": uuid.uuid4(), "org_id": org_id, "zone_id": assembly_3, "name": _CAMERA_NAMES[1],
                "url": "https://cdn.sentinelai.demo/hls/cam2.m3u8", "status": "active",
                "res": "1280x720", "fps": 30, "x": 50.0, "y": 30.0, "now": now,
            },
            {
                "id": uuid.uuid4(), "org_id": org_id, "zone_id": chem_storage, "name": _CAMERA_NAMES[2],
                "url": "https://cdn.sentinelai.demo/hls/cam3.m3u8", "status": "maintenance",
                "res": "1920x1080", "fps": 0, "x": 10.0, "y": 60.0, "now": now,
            },
        ],
    )

    bind.execute(
        sa.text(
            "INSERT INTO alerts (id, organization_id, zone_id, source, severity, message, acknowledged, "
            "acknowledged_by, acknowledged_at, created_at) VALUES "
            "(:id, :org_id, :zone_id, :source, :severity, :message, :ack, :ack_by, :ack_at, :now)"
        ),
        [
            {
                "id": uuid.uuid4(), "org_id": org_id, "zone_id": dock_a, "source": "risk", "severity": "Critical",
                "message": _ALERT_MESSAGES[0], "ack": False, "ack_by": None, "ack_at": None,
                "now": now - timedelta(minutes=12),
            },
            {
                "id": uuid.uuid4(), "org_id": org_id, "zone_id": assembly_3, "source": "sensor", "severity": "Medium",
                "message": _ALERT_MESSAGES[1], "ack": True, "ack_by": admin_id, "ack_at": now - timedelta(minutes=5),
                "now": now - timedelta(minutes=40),
            },
            {
                "id": uuid.uuid4(), "org_id": org_id, "zone_id": dock_a, "source": "vision", "severity": "Low",
                "message": _ALERT_MESSAGES[2], "ack": False, "ack_by": None, "ack_at": None,
                "now": now - timedelta(minutes=3),
            },
        ],
    )

    bind.execute(
        sa.text(
            "INSERT INTO incidents (id, organization_id, zone_id, title, category, severity, status, summary, "
            "detail, created_by, approved_by, created_at, approved_at, closed_at) VALUES "
            "(:id, :org_id, :zone_id, :title, :category, :severity, :status, :summary, "
            "CAST(:detail AS JSONB), :created_by, :approved_by, :now, :approved_at, NULL)"
        ),
        [
            {
                "id": uuid.uuid4(), "org_id": org_id, "zone_id": dock_a, "title": _INCIDENT_TITLES[0],
                "category": "ppe_violation", "severity": "High", "status": "draft",
                "summary": "Worker detected without hard hat near active forklift zone at 10:15 UTC.",
                "detail": "{}", "created_by": admin_id, "approved_by": None,
                "now": now - timedelta(hours=2), "approved_at": None,
            },
            {
                "id": uuid.uuid4(), "org_id": org_id, "zone_id": assembly_3, "title": _INCIDENT_TITLES[1],
                "category": "equipment_anomaly", "severity": "Medium", "status": "approved",
                "summary": "Conveyor motor vibration exceeded baseline for 12 consecutive minutes.",
                "detail": "{}", "created_by": admin_id, "approved_by": admin_id,
                "now": now - timedelta(hours=6), "approved_at": now - timedelta(hours=5),
            },
        ],
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM incidents WHERE title = ANY(:titles)"), {"titles": list(_INCIDENT_TITLES)})
    bind.execute(sa.text("DELETE FROM alerts WHERE message = ANY(:messages)"), {"messages": list(_ALERT_MESSAGES)})
    bind.execute(sa.text("DELETE FROM cameras WHERE name = ANY(:names)"), {"names": list(_CAMERA_NAMES)})
