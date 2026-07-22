"""LangGraph multi-agent signal fusion: four independent agents (gas,
permit, maintenance, shift) run in parallel and fan into one correlation
agent — genuine multi-agent orchestration, not a single function with four
if-statements, even though every node here is a deterministic DB query
rather than an LLM call (see this package's __init__.py for why).

The combination matrix is deliberately conservative: a single isolated
signal (a permit with no gas anomaly, a gas anomaly with nothing else
happening) is normal operations, not a compound finding. `combined=True`
only fires when at least two independent signals coincide — the exact
"data present, but nothing correlates it" gap the problem statement names.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MaintenanceStatus, PermitStatus, PermitType, SensorType
from app.models.facility import Building, Site, Zone
from app.models.maintenance import Equipment, MaintenanceRecord
from app.models.permit import WorkPermit
from app.models.sensor import SensorDevice, SensorReading
from app.models.shift import ShiftChangeoverEvent

_DANGEROUS_PERMITS = {PermitType.HOT_WORK.value, PermitType.CONFINED_SPACE.value}
_SHIFT_PROXIMITY_MINUTES = 45
_GAS_LOOKBACK_MINUTES = 20


@dataclass(frozen=True)
class CompoundRiskFinding:
    zone_id: str
    combined: bool
    severity: float
    hazard_class: str
    dominant_signals: list[str]
    rationale: str


class _GraphState(TypedDict):
    db: AsyncSession
    zone_id: str
    factory_id: str | None
    gas_anomaly: bool
    gas_sensor_names: list[str]
    active_permit_types: list[str]
    maintenance_active: bool
    shift_changeover_recent: bool
    result: CompoundRiskFinding | None


async def _gas_agent(state: _GraphState) -> dict:
    db = state["db"]
    since = datetime.now(timezone.utc) - timedelta(minutes=_GAS_LOOKBACK_MINUTES)
    rows = (
        await db.execute(
            select(SensorDevice.name, SensorReading.is_anomaly)
            .join(SensorReading, SensorReading.sensor_id == SensorDevice.id)
            .where(
                SensorDevice.zone_id == state["zone_id"],
                SensorDevice.sensor_type == SensorType.GAS,
                SensorReading.recorded_at >= since,
            )
            .order_by(SensorReading.recorded_at.desc())
        )
    ).all()
    # Latest reading per device name, first occurrence wins (already ordered newest-first).
    latest_by_device: dict[str, bool] = {}
    for name, is_anomaly in rows:
        latest_by_device.setdefault(name, is_anomaly)

    anomalous = [name for name, is_anomaly in latest_by_device.items() if is_anomaly]
    return {"gas_anomaly": bool(anomalous), "gas_sensor_names": anomalous}


async def _permit_agent(state: _GraphState) -> dict:
    db = state["db"]
    now = datetime.now(timezone.utc)
    permits = (
        await db.execute(
            select(WorkPermit.permit_type).where(
                WorkPermit.zone_id == state["zone_id"],
                WorkPermit.status == PermitStatus.ACTIVE,
                WorkPermit.valid_from <= now,
                WorkPermit.valid_to >= now,
            )
        )
    ).scalars()
    return {"active_permit_types": [p.value for p in permits]}


async def _maintenance_agent(state: _GraphState) -> dict:
    db = state["db"]
    now = datetime.now(timezone.utc)
    count = (
        await db.execute(
            select(MaintenanceRecord.id)
            .join(Equipment, MaintenanceRecord.equipment_id == Equipment.id)
            .where(
                Equipment.zone_id == state["zone_id"],
                MaintenanceRecord.status != MaintenanceStatus.COMPLETED,
                MaintenanceRecord.window_start <= now,
                MaintenanceRecord.window_end >= now,
            )
        )
    ).first()
    return {"maintenance_active": count is not None}


async def _shift_agent(state: _GraphState) -> dict:
    factory_id = state.get("factory_id")
    if factory_id is None:
        return {"shift_changeover_recent": False}
    db = state["db"]
    now = datetime.now(timezone.utc)
    latest = (
        await db.execute(
            select(ShiftChangeoverEvent.changeover_at)
            .where(ShiftChangeoverEvent.factory_id == factory_id)
            .order_by(ShiftChangeoverEvent.changeover_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    recent = latest is not None and (now - latest) <= timedelta(minutes=_SHIFT_PROXIMITY_MINUTES)
    return {"shift_changeover_recent": recent}


def _correlation_agent(state: _GraphState) -> dict:
    zone_id = state["zone_id"]
    gas_anomaly = state["gas_anomaly"]
    dangerous_permit_active = any(p in _DANGEROUS_PERMITS for p in state["active_permit_types"])
    any_permit_active = bool(state["active_permit_types"])
    maintenance_active = state["maintenance_active"]
    shift_recent = state["shift_changeover_recent"]

    signals: list[str] = []
    severity = 0.0
    hazard_class = "gas_anomaly"

    # Priority-ordered: the most dangerous, most specific combination wins.
    if gas_anomaly and dangerous_permit_active:
        signals = ["gas_anomaly", "dangerous_permit"]
        severity = 95.0
        hazard_class = "compound_gas_permit"
    elif gas_anomaly and maintenance_active:
        signals = ["gas_anomaly", "maintenance_active"]
        severity = 75.0
        hazard_class = "compound_gas_maintenance"
    elif gas_anomaly and shift_recent:
        signals = ["gas_anomaly", "shift_changeover"]
        severity = 55.0
        hazard_class = "compound_gas_shift_changeover"
    elif any_permit_active and maintenance_active and shift_recent:
        signals = ["permit_active", "maintenance_active", "shift_changeover"]
        severity = 50.0
        hazard_class = "compound_concurrent_activity"
    elif gas_anomaly:
        signals = ["gas_anomaly"]
        severity = 40.0
        hazard_class = "gas_anomaly"

    combined = len(signals) >= 2
    rationale = _build_rationale(signals, state)

    return {
        "result": CompoundRiskFinding(
            zone_id=zone_id,
            combined=combined,
            severity=severity,
            hazard_class=hazard_class,
            dominant_signals=signals,
            rationale=rationale,
        )
    }


def _build_rationale(signals: list[str], state: _GraphState) -> str:
    if not signals:
        return "No correlated risk signals detected in this zone right now."

    descriptions = {
        "gas_anomaly": f"a gas sensor reading outside its safe baseline ({', '.join(state['gas_sensor_names'])})",
        "dangerous_permit": f"an active {'/'.join(p for p in state['active_permit_types'] if p in _DANGEROUS_PERMITS)} permit",
        "maintenance_active": "equipment maintenance currently in progress",
        "shift_changeover": "a shift changeover within the last "
        f"{_SHIFT_PROXIMITY_MINUTES} minutes",
        "permit_active": f"an active work permit ({'/'.join(state['active_permit_types'])})",
    }
    parts = [descriptions[s] for s in signals if s in descriptions]
    if len(parts) == 1:
        return f"Elevated risk due to {parts[0]}."
    return "Elevated risk due to the combination of " + " and ".join(parts) + " — no single signal alone would have flagged this."


def build_graph():
    graph = StateGraph(_GraphState)
    graph.add_node("gas_agent", _gas_agent)
    graph.add_node("permit_agent", _permit_agent)
    graph.add_node("maintenance_agent", _maintenance_agent)
    graph.add_node("shift_agent", _shift_agent)
    graph.add_node("correlation_agent", _correlation_agent)

    graph.add_edge(START, "gas_agent")
    graph.add_edge(START, "permit_agent")
    graph.add_edge(START, "maintenance_agent")
    graph.add_edge(START, "shift_agent")
    graph.add_edge("gas_agent", "correlation_agent")
    graph.add_edge("permit_agent", "correlation_agent")
    graph.add_edge("maintenance_agent", "correlation_agent")
    graph.add_edge("shift_agent", "correlation_agent")
    graph.add_edge("correlation_agent", END)
    return graph.compile()


_graph = None


def get_compound_risk_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_for_zone(db: AsyncSession, *, zone_id: uuid.UUID) -> CompoundRiskFinding:
    """Resolves the zone's factory (needed by the shift agent) and runs the
    full correlation graph. Zone -> Building -> Site -> Factory, the same
    join chain already used elsewhere (see risk_engine_service.py's
    `_zones_under_factory`)."""
    factory_row = (
        await db.execute(
            select(Site.factory_id)
            .join(Building, Building.site_id == Site.id)
            .join(Zone, Zone.building_id == Building.id)
            .where(Zone.id == zone_id)
        )
    ).scalar_one_or_none()

    graph = get_compound_risk_graph()
    initial_state: _GraphState = {
        "db": db,
        "zone_id": str(zone_id),
        "factory_id": str(factory_row) if factory_row else None,
        "gas_anomaly": False,
        "gas_sensor_names": [],
        "active_permit_types": [],
        "maintenance_active": False,
        "shift_changeover_recent": False,
        "result": None,
    }
    final_state = await graph.ainvoke(initial_state)
    return final_state["result"]
