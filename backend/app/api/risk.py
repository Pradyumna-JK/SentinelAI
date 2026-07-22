"""Risk Intelligence Engine endpoints.

`GET /risk` keeps its original, smaller response shape (RiskResponse) for
backward compatibility with existing consumers (the frontend's dashboard
risk cards) — it's now backed by real computed data instead of static
placeholders, but the contract is unchanged. Every other endpoint here is
new: the richer per-zone view, history, both heatmaps, factory/organization
aggregation, and detection ingestion.
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import require_permission
from app.core.permissions import RISK_READ, RISK_WRITE
from app.schemas.auth import AuthenticatedUser
from app.schemas.risk import (
    DetectionIn,
    FactoryRiskResponse,
    IngestedHazard,
    OrganizationRiskResponse,
    RiskIngestRequest,
    RiskIngestResponse,
    RiskResponse,
    RiskScore,
    SpatialHeatmapCell,
    SpatialHeatmapResponse,
    TemporalHeatmapBucket,
    TemporalHeatmapResponse,
    ZoneHistoryPoint,
    ZoneHistoryResponse,
    ZoneRiskRead,
)
from app.services.risk_engine_service import (
    FactoryNotFoundError,
    RiskEngineService,
    ZoneNotFoundError,
    get_risk_engine_service,
)
from app.services.risk_ingest_service import DetectionIn as IngestDetectionIn
from app.services.risk_ingest_service import RiskIngestService
from app.services.risk_ingest_service import ZoneNotFoundError as IngestZoneNotFoundError
from app.services.risk_ingest_service import get_risk_ingest_service

router = APIRouter(prefix="/risk", tags=["Risk"])


def _to_zone_read(computation) -> ZoneRiskRead:
    return ZoneRiskRead(
        zone_id=uuid.UUID(computation.zone_id),
        zone_name=computation.zone_name,
        raw_score=computation.raw_score,
        score=computation.score,
        level=computation.level,
        severity=computation.severity,
        dominant_hazard_class=computation.dominant_hazard_class,
        predicted_score=computation.predicted_score,
        trend=computation.trend,
        recommended_action=computation.recommended_action,
        contributing_event_count=computation.contributing_event_count,
        computed_at=computation.computed_at,
    )


def _to_legacy_score(computation) -> RiskScore:
    rationale = (
        f"{computation.dominant_hazard_class.replace('_', ' ')} detected — {computation.recommended_action}"
        if computation.dominant_hazard_class
        else computation.recommended_action
    )
    return RiskScore(
        id=computation.zone_id,
        zone_id=computation.zone_id,
        zone_name=computation.zone_name,
        score=computation.score,
        level=computation.level,
        rationale=rationale,
        confidence="full" if computation.contributing_event_count > 0 else "no_data",
        created_at=computation.computed_at,
    )


@router.get(
    "",
    response_model=RiskResponse,
    summary="List compound risk scores for every zone in your organization",
    description=(
        "Returns the current compound risk score per zone. Backed by the "
        "Risk Intelligence Engine (app/ai/risk) — time-decayed, compound-"
        "aggregated, rolling-averaged from persisted hazard events. Requires "
        "the 'risk:read' permission. See GET /risk/zones/{zone_id} for the "
        "full detail (severity, prediction, trend) this summary omits."
    ),
)
async def read_risk_scores(
    current_user: AuthenticatedUser = Depends(require_permission(RISK_READ)),
    service: RiskEngineService = Depends(get_risk_engine_service),
) -> RiskResponse:
    result = await service.aggregate_organization_risk(current_user.organization_id)
    return RiskResponse(
        average_score=result["average_score"],
        highest_risk_zone=result["highest_risk_zone"] or "N/A",
        scores=[_to_legacy_score(c) for c in result["zones"]],
    )


@router.get(
    "/zones/{zone_id}",
    response_model=ZoneRiskRead,
    summary="Full risk detail for one zone",
    description=(
        "Computes (and persists a new snapshot of) this zone's current risk "
        "score, level, severity, prediction, trend, and recommended action."
    ),
)
async def read_zone_risk(
    zone_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(require_permission(RISK_READ)),
    service: RiskEngineService = Depends(get_risk_engine_service),
) -> ZoneRiskRead:
    try:
        computation = await service.compute_zone_risk(zone_id)
    except ZoneNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")
    return _to_zone_read(computation)


@router.get(
    "/zones/{zone_id}/history",
    response_model=ZoneHistoryResponse,
    summary="Historical risk-score snapshots for a zone",
)
async def read_zone_history(
    zone_id: uuid.UUID,
    since_minutes: int = Query(240, ge=1, le=10080, description="How far back to look, in minutes"),
    _current_user: AuthenticatedUser = Depends(require_permission(RISK_READ)),
    service: RiskEngineService = Depends(get_risk_engine_service),
) -> ZoneHistoryResponse:
    since = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
    try:
        snapshots = await service.zone_history(zone_id, since=since)
    except ZoneNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")
    return ZoneHistoryResponse(
        zone_id=zone_id,
        points=[
            ZoneHistoryPoint(computed_at=s.computed_at, score=s.score, level=s.level, trend=s.trend)
            for s in snapshots
        ],
    )


@router.get(
    "/zones/{zone_id}/heatmap/temporal",
    response_model=TemporalHeatmapResponse,
    summary="Average risk score by hour-of-day for a zone",
    description="When does this zone tend to be risky — averaged score per UTC hour-of-day over the window.",
)
async def read_zone_temporal_heatmap(
    zone_id: uuid.UUID,
    since_hours: int = Query(168, ge=1, le=8760, description="How far back to look, in hours"),
    _current_user: AuthenticatedUser = Depends(require_permission(RISK_READ)),
    service: RiskEngineService = Depends(get_risk_engine_service),
) -> TemporalHeatmapResponse:
    since = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    try:
        buckets = await service.zone_heatmap_temporal(zone_id, since=since)
    except ZoneNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")
    return TemporalHeatmapResponse(
        zone_id=zone_id,
        buckets=[
            TemporalHeatmapBucket(hour=hour, avg_score=round(avg, 1), sample_count=count)
            for hour, (avg, count) in sorted(buckets.items())
        ],
    )


@router.get(
    "/zones/{zone_id}/heatmap/spatial",
    response_model=SpatialHeatmapResponse,
    summary="Hazard density grid within a zone's camera frame",
    description="Where in the frame hazards cluster — from detection bounding-box centers, bucketed into a grid.",
)
async def read_zone_spatial_heatmap(
    zone_id: uuid.UUID,
    since_hours: int = Query(168, ge=1, le=8760),
    grid_size: int = Query(10, ge=2, le=50),
    _current_user: AuthenticatedUser = Depends(require_permission(RISK_READ)),
    service: RiskEngineService = Depends(get_risk_engine_service),
) -> SpatialHeatmapResponse:
    since = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    try:
        cells = await service.zone_heatmap_spatial(zone_id, since=since, grid_size=grid_size)
    except ZoneNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")
    return SpatialHeatmapResponse(
        zone_id=zone_id,
        grid_size=grid_size,
        cells=[SpatialHeatmapCell(**cell) for cell in cells],
    )


@router.get(
    "/factories/{factory_id}",
    response_model=FactoryRiskResponse,
    summary="Aggregated risk across every zone in a factory",
)
async def read_factory_risk(
    factory_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(require_permission(RISK_READ)),
    service: RiskEngineService = Depends(get_risk_engine_service),
) -> FactoryRiskResponse:
    try:
        result = await service.aggregate_factory_risk(factory_id)
    except FactoryNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Factory not found")
    return FactoryRiskResponse(
        factory_id=factory_id,
        factory_name=result["factory_name"],
        average_score=result["average_score"],
        highest_risk_zone=result["highest_risk_zone"],
        zone_count=result["zone_count"],
        zones=[_to_zone_read(c) for c in result["zones"]],
    )


@router.get(
    "/organization",
    response_model=OrganizationRiskResponse,
    summary="Aggregated risk across your entire organization",
)
async def read_organization_risk(
    current_user: AuthenticatedUser = Depends(require_permission(RISK_READ)),
    service: RiskEngineService = Depends(get_risk_engine_service),
) -> OrganizationRiskResponse:
    result = await service.aggregate_organization_risk(current_user.organization_id)
    return OrganizationRiskResponse(
        organization_id=current_user.organization_id,
        average_score=result["average_score"],
        highest_risk_zone=result["highest_risk_zone"],
        highest_risk_factory=result["highest_risk_factory"],
        zone_count=result["zone_count"],
        factory_averages=result["factory_averages"],
        zones=[_to_zone_read(c) for c in result["zones"]],
    )


@router.post(
    "/ingest",
    response_model=RiskIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest one frame's detections as hazard events",
    description=(
        "Interprets raw detections (as produced by the vision engine, "
        "app/ai/vision) into business-meaningful hazards — PPE violations "
        "via person/PPE bbox correlation, fire/smoke pass through directly "
        "— and persists them for the Risk Intelligence Engine to score. "
        "Intended for a camera-ingestion pipeline; requires 'risk:write'."
    ),
)
async def ingest_detections(
    payload: RiskIngestRequest,
    current_user: AuthenticatedUser = Depends(require_permission(RISK_WRITE)),
    service: RiskIngestService = Depends(get_risk_ingest_service),
) -> RiskIngestResponse:
    try:
        events = await service.ingest_frame(
            organization_id=current_user.organization_id,
            zone_id=payload.zone_id,
            camera_id=payload.camera_id,
            detections=[
                IngestDetectionIn(d.class_name, d.confidence, d.x1, d.y1, d.x2, d.y2)
                for d in payload.detections
            ],
            frame_width=payload.frame_width,
            frame_height=payload.frame_height,
            source_id=payload.source_id,
            detected_at=payload.detected_at,
        )
    except IngestZoneNotFoundError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "zone_id does not exist")
    return RiskIngestResponse(
        hazard_events_created=len(events),
        hazards=[
            IngestedHazard(hazard_class=e.hazard_class, confidence=e.confidence, severity=e.severity)
            for e in events
        ],
    )
