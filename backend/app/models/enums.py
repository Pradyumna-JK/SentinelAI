"""Shared enumerations used across schemas and services."""

from enum import Enum


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class AlertSeverity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class CameraStatus(str, Enum):
    ACTIVE = "active"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class IncidentStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    CLOSED = "closed"


class AgentHealth(str, Enum):
    HEALTHY = "Healthy"
    DEGRADED = "Degraded"
    OFFLINE = "Offline"


class Trend(str, Enum):
    """Direction of a zone's risk score over its recent history — see
    app/ai/risk/scoring.py's `predict_and_trend`."""

    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"


class DocumentStatus(str, Enum):
    """Lifecycle of an uploaded compliance PDF through the background
    ingestion worker — see app/ai/compliance/worker.py."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ComplianceIntent(str, Enum):
    """Question category the Compliance Copilot's classify_intent graph
    node sorts a question into — see app/ai/compliance/graph.py and
    prompts.py's per-intent system-prompt guidance."""

    SAFETY_RULE_LOOKUP = "safety_rule_lookup"
    INCIDENT_EXPLANATION = "incident_explanation"
    COMPLIANCE_RECOMMENDATION = "compliance_recommendation"
    GENERAL = "general"


class AlertSource(str, Enum):
    """Which subsystem raised an Alert row — lets the dashboard/UI group and
    filter by origin without parsing the free-text message."""

    VISION = "vision"
    RISK = "risk"
    SENSOR = "sensor"
    PERMIT = "permit"
    EMERGENCY = "emergency"
    MANUAL = "manual"


class SensorType(str, Enum):
    GAS = "gas"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    VIBRATION = "vibration"


class PermitType(str, Enum):
    """The specific combination the problem statement calls out — hot work
    near elevated gas readings — is exactly why HOT_WORK and CONFINED_SPACE
    exist as distinct values the Compound Risk Intelligence Engine can key
    correlation rules off of, rather than a single generic 'permit' type."""

    HOT_WORK = "hot_work"
    CONFINED_SPACE = "confined_space"
    ELECTRICAL = "electrical"
    WORKING_AT_HEIGHT = "working_at_height"
    GENERAL = "general"


class PermitStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    ACTIVE = "active"
    CLOSED = "closed"
    REVOKED = "revoked"


class EquipmentCriticality(str, Enum):
    """Kept distinct from RiskLevel/AlertSeverity despite the same four
    values — this is a static property of the equipment, not a computed
    state, the same distinction already drawn between RiskLevel (computed)
    and AlertSeverity (an event's declared severity)."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class MaintenanceStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
