"""seed demo risk event history for chemical storage zone

Revision ID: 58d473a67289
Revises: c9d5400b7942
Create Date: 2026-07-22 00:37:38.184617

Hand-authored, fully self-contained demo data — deliberately NOT computed
via app/ai/risk/scoring.py (unlike the RBAC seed migration, which
legitimately reads live app.core.permissions constants because permissions
genuinely are configuration). This is fabricated narrative data for
demoing history/trend/heatmap immediately after a fresh deploy, and it
should render identically forever regardless of any future change to the
scoring formula — so the numbers are literals, not derived.

Narrative: Chemical Storage's smoke detector picks up rising smoke over an
hour, escalates to a confirmed fire, is suppressed, and the zone spends its
last ~10 minutes clearing — 13 score snapshots at 10-minute intervals (the
readable "trend" time series) backed by 8 raw hazard events (what a real
ingest would have produced) anchored to whenever this migration runs.
"""

import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from alembic import op

from app.core.config import get_settings

revision: str = "58d473a67289"
down_revision: str | None = "c9d5400b7942"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

risk_events_table = sa.table(
    "risk_events",
    sa.column("id", sa.UUID()),
    sa.column("organization_id", sa.UUID()),
    sa.column("zone_id", sa.UUID()),
    sa.column("camera_id", sa.String()),
    sa.column("source_id", sa.String()),
    sa.column("hazard_class", sa.String()),
    sa.column("confidence", sa.Float()),
    sa.column("severity", sa.Float()),
    sa.column("bbox_x1", sa.Float()),
    sa.column("bbox_y1", sa.Float()),
    sa.column("bbox_x2", sa.Float()),
    sa.column("bbox_y2", sa.Float()),
    sa.column("detected_at", sa.DateTime(timezone=True)),
)

risk_score_snapshots_table = sa.table(
    "risk_score_snapshots",
    sa.column("id", sa.UUID()),
    sa.column("organization_id", sa.UUID()),
    sa.column("zone_id", sa.UUID()),
    sa.column("computed_at", sa.DateTime(timezone=True)),
    sa.column("raw_score", sa.Float()),
    sa.column("score", sa.Float()),
    sa.column("level", sa.String()),
    sa.column("severity", sa.String()),
    sa.column("dominant_hazard_class", sa.String()),
    sa.column("predicted_score", sa.Float()),
    sa.column("trend", sa.String()),
    sa.column("recommended_action", sa.Text()),
    sa.column("contributing_event_count", sa.Integer()),
)

# (minutes_ago, hazard_class, confidence, bbox)
_EVENTS = [
    (85, "smoke", 0.55, (0.30, 0.20, 0.55, 0.50)),
    (72, "smoke", 0.68, (0.32, 0.22, 0.58, 0.52)),
    (58, "smoke", 0.75, (0.28, 0.18, 0.60, 0.55)),
    (45, "smoke", 0.82, (0.30, 0.15, 0.62, 0.58)),
    (32, "fire", 0.70, (0.35, 0.25, 0.50, 0.48)),
    (28, "fire", 0.91, (0.36, 0.24, 0.52, 0.50)),
    (15, "fire", 0.60, (0.34, 0.26, 0.49, 0.47)),
    (8, "smoke", 0.50, (0.30, 0.20, 0.55, 0.50)),
]

# (minutes_ago, raw_score, score, level, severity, dominant, predicted, trend, action, count)
_SNAPSHOTS = [
    (120, 8.0, 8.0, "Low", "Low", None, None, "stable", "No action required — continue routine monitoring.", 0),
    (110, 10.0, 9.5, "Low", "Low", None, None, "stable", "No action required — continue routine monitoring.", 0),
    (100, 12.0, 11.0, "Low", "Low", None, None, "stable", "No action required — continue routine monitoring.", 0),
    (90, 15.0, 13.5, "Low", "Low", None, 20.0, "increasing", "No action required — continue routine monitoring.", 1),
    (80, 24.0, 18.5, "Low", "Medium", "smoke", 35.0, "increasing", "Flag for the next scheduled safety walk-through.", 1),
    (70, 34.0, 24.9, "Medium", "Medium", "smoke", 48.0, "increasing", "Flag for the next scheduled safety walk-through.", 2),
    (60, 46.0, 32.6, "Medium", "Medium", "smoke", 60.0, "increasing", "Flag for the next scheduled safety walk-through.", 2),
    (50, 59.0, 41.6, "Medium", "High", "smoke", 74.0, "increasing", "Dispatch a supervisor to the zone and confirm compliance in person.", 3),
    (40, 69.0, 50.4, "High", "High", "smoke", 84.0, "increasing", "Dispatch a supervisor to the zone and confirm compliance in person.", 4),
    (30, 86.0, 61.2, "High", "Critical", "fire", 95.0, "increasing", "Escalate to a safety supervisor immediately and restrict zone access.", 6),
    (20, 93.0, 70.7, "High", "Critical", "fire", 90.0, "increasing", "Evacuate the zone immediately and notify emergency services.", 7),
    (10, 71.0, 70.9, "High", "High", "fire", 55.0, "decreasing", "Dispatch a supervisor to the zone and confirm compliance in person.", 5),
    (0, 43.0, 62.1, "Medium", "Medium", "smoke", 40.0, "decreasing", "Flag for the next scheduled safety walk-through.", 3),
]


def upgrade() -> None:
    settings = get_settings()
    bind = op.get_bind()

    org_id = bind.execute(
        sa.text("SELECT id FROM organizations WHERE slug = :slug"),
        {"slug": settings.default_organization_slug},
    ).scalar_one_or_none()
    if org_id is None:
        print("WARNING: default organization not found — skipping demo risk history seed.")
        return

    zone_id = bind.execute(
        sa.text(
            "SELECT z.id FROM zones z "
            "JOIN buildings b ON b.id = z.building_id "
            "WHERE z.organization_id = :org_id AND z.code = 'ZONE-03'"
        ),
        {"org_id": org_id},
    ).scalar_one_or_none()
    if zone_id is None:
        print("WARNING: Chemical Storage zone (code ZONE-03) not found — skipping demo risk history seed.")
        return

    now = datetime.now(timezone.utc)

    op.bulk_insert(
        risk_events_table,
        [
            {
                "id": uuid.uuid4(),
                "organization_id": org_id,
                "zone_id": zone_id,
                "camera_id": "cam-003",
                "source_id": "seed-demo",
                "hazard_class": hazard_class,
                "confidence": confidence,
                "severity": 100.0 if hazard_class == "fire" else 70.0,
                "bbox_x1": bbox[0],
                "bbox_y1": bbox[1],
                "bbox_x2": bbox[2],
                "bbox_y2": bbox[3],
                "detected_at": now - timedelta(minutes=minutes_ago),
            }
            for minutes_ago, hazard_class, confidence, bbox in _EVENTS
        ],
    )

    op.bulk_insert(
        risk_score_snapshots_table,
        [
            {
                "id": uuid.uuid4(),
                "organization_id": org_id,
                "zone_id": zone_id,
                "computed_at": now - timedelta(minutes=minutes_ago),
                "raw_score": raw_score,
                "score": score,
                "level": level,
                "severity": severity,
                "dominant_hazard_class": dominant,
                "predicted_score": predicted,
                "trend": trend,
                "recommended_action": action,
                "contributing_event_count": count,
            }
            for minutes_ago, raw_score, score, level, severity, dominant, predicted, trend, action, count in _SNAPSHOTS
        ],
    )


def downgrade() -> None:
    settings = get_settings()
    bind = op.get_bind()

    org_id = bind.execute(
        sa.text("SELECT id FROM organizations WHERE slug = :slug"),
        {"slug": settings.default_organization_slug},
    ).scalar_one_or_none()
    if org_id is None:
        return

    zone_id = bind.execute(
        sa.text("SELECT id FROM zones WHERE organization_id = :org_id AND code = 'ZONE-03'"),
        {"org_id": org_id},
    ).scalar_one_or_none()
    if zone_id is None:
        return

    bind.execute(
        sa.text("DELETE FROM risk_events WHERE zone_id = :zone_id AND source_id = 'seed-demo'"),
        {"zone_id": zone_id},
    )
    bind.execute(
        sa.text(
            "DELETE FROM risk_score_snapshots WHERE zone_id = :zone_id "
            "AND recommended_action IN ("
            "  'No action required — continue routine monitoring.',"
            "  'Flag for the next scheduled safety walk-through.',"
            "  'Dispatch a supervisor to the zone and confirm compliance in person.',"
            "  'Escalate to a safety supervisor immediately and restrict zone access.',"
            "  'Evacuate the zone immediately and notify emergency services.'"
            ")"
        ),
        {"zone_id": zone_id},
    )
