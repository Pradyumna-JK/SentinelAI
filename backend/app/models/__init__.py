"""ORM models and shared enumerations.

Every ORM model module must be imported here so Alembic's autogenerate
(which imports this package) sees the full metadata.
"""

from app.models.alert import Alert
from app.models.base import Base
from app.models.camera import Camera
from app.models.compliance import ComplianceChatMessage, ComplianceChatSession, ComplianceDocument
from app.models.emergency_protocol import EmergencyProtocol
from app.models.facility import Building, Factory, Site, Zone
from app.models.incident import Incident
from app.models.maintenance import Equipment, MaintenanceRecord
from app.models.organization import Organization
from app.models.permit import WorkPermit
from app.models.risk import RiskEvent, RiskScoreSnapshot
from app.models.role import Permission, Role, role_permissions, user_roles
from app.models.sensor import SensorDevice, SensorReading
from app.models.shift import Shift, ShiftChangeoverEvent
from app.models.token import PasswordResetToken, RefreshToken
from app.models.user import User

__all__ = [
    "Base",
    "Organization",
    "Factory",
    "Site",
    "Building",
    "Zone",
    "User",
    "Role",
    "Permission",
    "role_permissions",
    "user_roles",
    "RefreshToken",
    "PasswordResetToken",
    "RiskEvent",
    "RiskScoreSnapshot",
    "ComplianceDocument",
    "ComplianceChatSession",
    "ComplianceChatMessage",
    "Alert",
    "Incident",
    "Camera",
    "SensorDevice",
    "SensorReading",
    "WorkPermit",
    "Equipment",
    "MaintenanceRecord",
    "Shift",
    "ShiftChangeoverEvent",
    "EmergencyProtocol",
]
