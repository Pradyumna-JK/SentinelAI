"""Emergency Response Orchestrator: on a Critical risk finding, matches a
site-configured protocol (exact hazard-type match -> high confidence;
fallback to a "general" protocol -> low confidence; nothing configured ->
explicit gap notice, never a fabricated protocol — the never-implemented
Emergency Response Agent spec, docs/11_AI_ARCHITECTURE.md §5), auto-drafts
a structured incident report from the evidence (that same doc's Incident
Report Generator §6 — LLM-drafted and evidence-constrained, with a
templated fallback if the LLM call itself fails, since a safety-critical
incident must still get created even if drafting degrades), and raises a
Critical alert. Reuses the *existing* Incident/Alert persistence
(app/services/incidents_service.py, app/services/alerts_service.py) — no
parallel notification system, and the same `ChatGoogleGenerativeAI` client the
Compliance Copilot already uses — no second LLM integration.

A cooldown (a recent auto-created incident already exists for this zone)
stops one ongoing Critical state from spawning a new incident on every
scheduler tick.
"""

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_content import extract_text
from app.ai.risk.types import RiskComputation
from app.core.config import get_settings
from app.models.emergency_protocol import EmergencyProtocol
from app.models.enums import AlertSeverity, AlertSource
from app.models.incident import Incident
from app.services.alerts_service import create_alert
from app.services.incidents_service import IncidentsService

logger = structlog.get_logger("sentinel.emergency")

AUTO_INCIDENT_CATEGORY = "emergency_auto"
_COOLDOWN_MINUTES = 10
_GENERAL_PROTOCOL_HAZARD_TYPE = "general"
# No real Twilio/SendGrid/Slack credentials exist for this demo — dispatch
# is logged, not actually sent, and stated plainly as a simulation rather
# than pretending it's a real integration.
_SIMULATED_CHANNELS = ("sms", "email", "site_pa_system")


class EmergencyResponseService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._settings = get_settings()

    async def handle_critical_zone(
        self, *, organization_id: uuid.UUID, zone_id: uuid.UUID, computation: RiskComputation
    ) -> Incident | None:
        if await self._recently_handled(zone_id):
            return None

        protocol, match_confidence = await self._match_protocol(computation.dominant_hazard_class)
        summary = await self._draft_summary(computation, protocol, match_confidence)

        incidents_service = IncidentsService(self._db)
        incident = await incidents_service.create(
            organization_id=organization_id,
            zone_id=zone_id,
            title=f"Critical risk - {computation.zone_name}",
            category=AUTO_INCIDENT_CATEGORY,
            severity=AlertSeverity.CRITICAL,
            summary=summary,
            detail={
                "risk_score": computation.score,
                "dominant_hazard_class": computation.dominant_hazard_class,
                "matched_protocol": protocol.hazard_type if protocol else None,
                "match_confidence": match_confidence,
                "evacuation_route": protocol.evacuation_route if protocol else None,
                "steps": protocol.steps if protocol else [],
            },
            created_by=None,
        )

        await create_alert(
            self._db,
            organization_id=organization_id,
            zone_id=zone_id,
            severity=AlertSeverity.CRITICAL,
            source=AlertSource.EMERGENCY,
            message=f"Emergency response triggered: {summary[:300]}",
        )

        logger.info(
            "emergency_alert_dispatched_simulated",
            zone=computation.zone_name,
            channels=list(_SIMULATED_CHANNELS),
            evacuation_route=protocol.evacuation_route if protocol else None,
            match_confidence=match_confidence,
        )
        return incident

    async def _recently_handled(self, zone_id: uuid.UUID) -> bool:
        since = datetime.now(timezone.utc) - timedelta(minutes=_COOLDOWN_MINUTES)
        result = await self._db.execute(
            select(Incident.id)
            .where(
                Incident.zone_id == zone_id,
                Incident.category == AUTO_INCIDENT_CATEGORY,
                Incident.created_at >= since,
            )
            .limit(1)
        )
        return result.first() is not None

    async def _match_protocol(self, hazard_class: str | None) -> tuple[EmergencyProtocol | None, str]:
        if hazard_class:
            exact = (
                await self._db.execute(select(EmergencyProtocol).where(EmergencyProtocol.hazard_type == hazard_class))
            ).scalar_one_or_none()
            if exact is not None:
                return exact, "high"

        general = (
            await self._db.execute(
                select(EmergencyProtocol).where(EmergencyProtocol.hazard_type == _GENERAL_PROTOCOL_HAZARD_TYPE)
            )
        ).scalar_one_or_none()
        if general is not None:
            return general, "low (fallback to general protocol)"

        return None, "none (no protocols configured)"

    async def _draft_summary(
        self, computation: RiskComputation, protocol: EmergencyProtocol | None, match_confidence: str
    ) -> str:
        prompt = (
            "You are the SentinelAI Incident Report Generator. Draft a structured, "
            "audit-ready incident summary using ONLY the evidence below. Do not "
            "speculate beyond the evidence. Two to four sentences.\n\n"
            f"Zone: {computation.zone_name}\n"
            f"Risk score: {computation.score} ({computation.level.value})\n"
            f"Dominant hazard: {computation.dominant_hazard_class or 'unspecified'}\n"
            f"Recommended action: {computation.recommended_action}\n"
            f"Matched emergency protocol: {protocol.hazard_type if protocol else 'none configured'} "
            f"(confidence: {match_confidence})\n"
        )
        try:
            llm = ChatGoogleGenerativeAI(
                model=self._settings.gemini_chat_model,
                google_api_key=self._settings.gemini_api_key.get_secret_value(),
                temperature=0.2,
            )
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            return extract_text(response.content)
        except Exception:  # noqa: BLE001 — a safety-critical incident must still get created
            logger.warning(
                "emergency_summary_llm_failed_using_template", zone=computation.zone_name, exc_info=True
            )
            return (
                f"Critical risk detected in {computation.zone_name} (score {computation.score}), "
                f"dominant factor: {computation.dominant_hazard_class or 'compound risk finding'}. "
                f"{computation.recommended_action} Matched protocol: "
                f"{protocol.hazard_type if protocol else 'none configured'} ({match_confidence})."
            )
