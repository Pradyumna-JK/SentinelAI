"""Risk Intelligence Engine: orchestrates app/ai/risk/scoring.py's pure math
against persisted RiskEvent/RiskScoreSnapshot rows.

Every read here relies on app/core/tenancy.py's automatic ORM filter —
this file has no explicit `.where(organization_id == ...)` anywhere, same
as app/services/facility_service.py. The one place organization_id is
required as an explicit value is constructing a NEW RiskScoreSnapshot row.

Zone/factory/organization aggregation all recompute every zone live rather
than reading a cached "latest snapshot" per zone — correct and simple at
this scale (a handful of zones), and it's what keeps history/rolling-
average/trend data flowing even for a zone nobody has queried directly.
The scaling note, honestly stated: for an organization with hundreds of
zones, synchronous live recomputation per API call stops being free: at
that point aggregation should read the background scheduler's last-written
snapshot per zone instead of recomputing inline. Not needed yet.
"""

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.risk.scoring import (
    aggregate_events,
    level_band,
    predict_and_trend,
    recommend_action,
    rolling_average,
    score_event,
    severity_band,
)
from app.ai.risk.types import RiskComputation, RiskLevel, ScoredEvent, Trend
from app.core.config import get_settings
from app.db.session import get_db
from app.models.facility import Building, Factory, Site, Zone
from app.models.risk import RiskEvent, RiskScoreSnapshot


class ZoneNotFoundError(Exception):
    pass


class FactoryNotFoundError(Exception):
    pass


class RiskEngineService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._settings = get_settings()

    # ------------------------------------------------------------- zone

    async def compute_zone_risk(self, zone_id: uuid.UUID) -> RiskComputation:
        zone = await self._db.get(Zone, zone_id)
        if zone is None:
            raise ZoneNotFoundError()

        now = datetime.now(timezone.utc)
        settings = self._settings

        lookback_start = now - timedelta(minutes=settings.risk_event_lookback_minutes)
        events_result = await self._db.execute(
            select(RiskEvent).where(RiskEvent.zone_id == zone_id, RiskEvent.detected_at >= lookback_start)
        )
        events = list(events_result.scalars())

        scored = [
            ScoredEvent(
                hazard_class=e.hazard_class,
                severity=e.severity,
                confidence=e.confidence,
                detected_at=e.detected_at,
                contribution=score_event(
                    e.severity, e.confidence, e.detected_at,
                    now=now, half_life_seconds=settings.risk_decay_half_life_seconds,
                ),
            )
            for e in events
        ]
        raw_score, dominant_hazard_class, max_single = aggregate_events(
            scored, compound_boost_factor=settings.risk_compound_boost_factor
        )

        prior_result = await self._db.execute(
            select(RiskScoreSnapshot)
            .where(RiskScoreSnapshot.zone_id == zone_id)
            .order_by(RiskScoreSnapshot.computed_at.desc())
            .limit(settings.risk_history_window_for_trend)
        )
        prior_snapshots = list(reversed(list(prior_result.scalars())))  # oldest -> newest

        previous_smoothed = prior_snapshots[-1].score if prior_snapshots else None
        score = rolling_average(raw_score, previous_smoothed, alpha=settings.risk_rolling_average_alpha)

        level = level_band(score)
        severity = severity_band(max_single)

        trend_history = [(s.computed_at, s.score) for s in prior_snapshots] + [(now, score)]
        predicted_score, trend = predict_and_trend(
            trend_history,
            horizon_minutes=settings.risk_prediction_horizon_minutes,
            trend_deadband_per_minute=settings.risk_trend_deadband_per_minute,
        )

        action = recommend_action(level, dominant_hazard_class)

        snapshot = RiskScoreSnapshot(
            organization_id=zone.organization_id,
            zone_id=zone_id,
            computed_at=now,
            raw_score=round(raw_score, 2),
            score=round(score, 2),
            level=level,
            severity=severity,
            dominant_hazard_class=dominant_hazard_class,
            predicted_score=predicted_score,
            trend=trend,
            recommended_action=action,
            contributing_event_count=len(events),
        )
        self._db.add(snapshot)
        await self._db.flush()

        return RiskComputation(
            zone_id=str(zone_id),
            zone_name=zone.name,
            raw_score=snapshot.raw_score,
            score=snapshot.score,
            level=level,
            severity=severity,
            dominant_hazard_class=dominant_hazard_class,
            predicted_score=predicted_score,
            trend=trend,
            recommended_action=action,
            contributing_event_count=len(events),
            computed_at=now,
            history_used=len(prior_snapshots),
        )

    async def zone_history(self, zone_id: uuid.UUID, *, since: datetime) -> list[RiskScoreSnapshot]:
        if await self._db.get(Zone, zone_id) is None:
            raise ZoneNotFoundError()
        result = await self._db.execute(
            select(RiskScoreSnapshot)
            .where(RiskScoreSnapshot.zone_id == zone_id, RiskScoreSnapshot.computed_at >= since)
            .order_by(RiskScoreSnapshot.computed_at)
        )
        return list(result.scalars())

    async def zone_heatmap_temporal(self, zone_id: uuid.UUID, *, since: datetime) -> dict[int, tuple[float, int]]:
        """Average score by hour-of-day (0-23) over the window — "when does
        this zone tend to be risky". Returns {hour: (avg_score, sample_count)}.
        """
        if await self._db.get(Zone, zone_id) is None:
            raise ZoneNotFoundError()
        result = await self._db.execute(
            select(RiskScoreSnapshot.computed_at, RiskScoreSnapshot.score)
            .where(RiskScoreSnapshot.zone_id == zone_id, RiskScoreSnapshot.computed_at >= since)
        )
        buckets: dict[int, list[float]] = defaultdict(list)
        for computed_at, score in result.all():
            buckets[computed_at.hour].append(score)
        return {hour: (sum(scores) / len(scores), len(scores)) for hour, scores in buckets.items()}

    async def zone_heatmap_spatial(
        self, zone_id: uuid.UUID, *, since: datetime, grid_size: int = 10
    ) -> list[dict]:
        """Hazard density over a grid_size x grid_size grid of the zone's
        camera frame — "where in the frame do hazards cluster", from
        RiskEvent's normalized bbox centers. Cells with zero events are
        omitted (a sparse result, not a dense grid_size^2 array).
        """
        if await self._db.get(Zone, zone_id) is None:
            raise ZoneNotFoundError()
        result = await self._db.execute(
            select(RiskEvent).where(
                RiskEvent.zone_id == zone_id,
                RiskEvent.detected_at >= since,
                RiskEvent.bbox_x1.is_not(None),
            )
        )
        cells: dict[tuple[int, int], list[RiskEvent]] = defaultdict(list)
        for event in result.scalars():
            cx = (event.bbox_x1 + event.bbox_x2) / 2
            cy = (event.bbox_y1 + event.bbox_y2) / 2
            col = min(grid_size - 1, max(0, int(cx * grid_size)))
            row = min(grid_size - 1, max(0, int(cy * grid_size)))
            cells[(row, col)].append(event)

        return [
            {
                "row": row,
                "col": col,
                "event_count": len(events),
                "avg_severity": round(sum(e.severity for e in events) / len(events), 1),
                "dominant_hazard_class": max(
                    {e.hazard_class for e in events},
                    key=lambda cls: sum(1 for e in events if e.hazard_class == cls),
                ),
            }
            for (row, col), events in cells.items()
        ]

    # ------------------------------------------------------------- aggregation

    async def _zones_under_factory(self, factory_id: uuid.UUID) -> list[Zone]:
        result = await self._db.execute(
            select(Zone)
            .join(Building, Zone.building_id == Building.id)
            .join(Site, Building.site_id == Site.id)
            .where(Site.factory_id == factory_id)
        )
        return list(result.scalars())

    async def aggregate_factory_risk(self, factory_id: uuid.UUID) -> dict:
        factory = await self._db.get(Factory, factory_id)
        if factory is None:
            raise FactoryNotFoundError()

        zones = await self._zones_under_factory(factory_id)
        computations = [await self.compute_zone_risk(zone.id) for zone in zones]

        average = round(sum(c.score for c in computations) / len(computations), 1) if computations else 0.0
        highest = max(computations, key=lambda c: c.score) if computations else None

        return {
            "factory_id": str(factory_id),
            "factory_name": factory.name,
            "average_score": average,
            "highest_risk_zone": highest.zone_name if highest else None,
            "zone_count": len(zones),
            "zones": computations,
        }

    async def aggregate_organization_risk(self, organization_id: uuid.UUID) -> dict:
        # Relies on the automatic tenant filter for correctness (the caller's
        # own organization_id, from their JWT, is what's already active) —
        # passed explicitly here only to label the response.
        zones_result = await self._db.execute(select(Zone))
        zones = list(zones_result.scalars())
        computations = [await self.compute_zone_risk(zone.id) for zone in zones]

        factories_result = await self._db.execute(select(Factory))
        factories = list(factories_result.scalars())
        factory_scores: dict[str, list[float]] = defaultdict(list)
        for factory in factories:
            factory_zones = await self._zones_under_factory(factory.id)
            zone_ids = {str(z.id) for z in factory_zones}
            factory_scores[factory.name] = [c.score for c in computations if c.zone_id in zone_ids]

        average = round(sum(c.score for c in computations) / len(computations), 1) if computations else 0.0
        highest_zone = max(computations, key=lambda c: c.score) if computations else None

        factory_averages = {
            name: round(sum(scores) / len(scores), 1) for name, scores in factory_scores.items() if scores
        }
        highest_risk_factory = max(factory_averages, key=factory_averages.get) if factory_averages else None

        return {
            "organization_id": str(organization_id),
            "average_score": average,
            "highest_risk_zone": highest_zone.zone_name if highest_zone else None,
            "highest_risk_factory": highest_risk_factory,
            "zone_count": len(zones),
            "factory_averages": factory_averages,
            "zones": computations,
        }


def get_risk_engine_service(db: AsyncSession = Depends(get_db)) -> RiskEngineService:
    return RiskEngineService(db)
