"""Canonical permission codes and the default role -> permission matrix.

Single source of truth consumed by the RBAC seed migration
(alembic/versions/*_seed_rbac.py) and the `require_permission` dependency
(app/core/deps.py). Codes follow `resource:action`. Kept independent of
app/models so the seed migration — which intentionally does not import ORM
models (see that file's docstring) — can still share these constants.
"""

DASHBOARD_READ = "dashboard:read"
CAMERA_READ = "camera:read"
CAMERA_WRITE = "camera:write"
ALERTS_READ = "alerts:read"
ALERTS_WRITE = "alerts:write"
RISK_READ = "risk:read"
RISK_WRITE = "risk:write"
INCIDENTS_READ = "incidents:read"
INCIDENTS_WRITE = "incidents:write"
COMPLIANCE_READ = "compliance:read"
COMPLIANCE_WRITE = "compliance:write"
USERS_READ = "users:read"
USERS_WRITE = "users:write"
ROLES_READ = "roles:read"
ROLES_MANAGE = "roles:manage"
FACTORIES_READ = "factories:read"
FACTORIES_WRITE = "factories:write"
SITES_READ = "sites:read"
SITES_WRITE = "sites:write"
BUILDINGS_READ = "buildings:read"
BUILDINGS_WRITE = "buildings:write"
ZONES_READ = "zones:read"
ZONES_WRITE = "zones:write"
SENSORS_READ = "sensors:read"
SENSORS_WRITE = "sensors:write"
PERMITS_READ = "permits:read"
PERMITS_WRITE = "permits:write"
MAINTENANCE_READ = "maintenance:read"
MAINTENANCE_WRITE = "maintenance:write"
SHIFTS_READ = "shifts:read"
SHIFTS_WRITE = "shifts:write"
EMERGENCY_READ = "emergency:read"
EMERGENCY_WRITE = "emergency:write"

ALL_PERMISSIONS: dict[str, str] = {
    DASHBOARD_READ: "View the live dashboard overview",
    CAMERA_READ: "View camera stream metadata",
    CAMERA_WRITE: "Register or update camera streams",
    ALERTS_READ: "View alerts",
    ALERTS_WRITE: "Create and acknowledge alerts",
    RISK_READ: "View compound risk scores",
    RISK_WRITE: "Ingest detection events into the Risk Intelligence Engine",
    INCIDENTS_READ: "View incident reports",
    INCIDENTS_WRITE: "Create, approve, and close incident reports",
    COMPLIANCE_READ: "View compliance documents and query history",
    COMPLIANCE_WRITE: "Query the Compliance Copilot",
    USERS_READ: "View user accounts in the organization",
    USERS_WRITE: "Create, update, and deactivate user accounts",
    ROLES_READ: "View roles and their permissions",
    ROLES_MANAGE: "Assign or revoke roles on user accounts",
    FACTORIES_READ: "View factories in the organization",
    FACTORIES_WRITE: "Create factories",
    SITES_READ: "View sites",
    SITES_WRITE: "Create sites",
    BUILDINGS_READ: "View buildings",
    BUILDINGS_WRITE: "Create buildings",
    ZONES_READ: "View zones",
    ZONES_WRITE: "Create zones",
    SENSORS_READ: "View IoT/SCADA sensor devices and readings",
    SENSORS_WRITE: "Register sensor devices",
    PERMITS_READ: "View work permits",
    PERMITS_WRITE: "Issue and close work permits",
    MAINTENANCE_READ: "View equipment and maintenance records",
    MAINTENANCE_WRITE: "Register equipment and log maintenance activity",
    SHIFTS_READ: "View shifts and changeover events",
    SHIFTS_WRITE: "Define shifts and log changeover events",
    EMERGENCY_READ: "View emergency protocols",
    EMERGENCY_WRITE: "Configure emergency protocols and manually trigger the orchestrator",
}

# Role names — also the exact `roles.name` values seeded into the database.
ADMIN = "Admin"
MANAGER = "Manager"
SUPERVISOR = "Supervisor"
OPERATOR = "Operator"
VIEWER = "Viewer"

SYSTEM_ROLES: tuple[str, ...] = (ADMIN, MANAGER, SUPERVISOR, OPERATOR, VIEWER)

_READ_ONLY: tuple[str, ...] = (
    DASHBOARD_READ,
    CAMERA_READ,
    ALERTS_READ,
    RISK_READ,
    INCIDENTS_READ,
    COMPLIANCE_READ,
    FACTORIES_READ,
    SITES_READ,
    BUILDINGS_READ,
    ZONES_READ,
    SENSORS_READ,
    PERMITS_READ,
    MAINTENANCE_READ,
    SHIFTS_READ,
    EMERGENCY_READ,
)

# Operational write access to the signal-fusion inputs (sensors, permits,
# maintenance, shifts) follows the same shape as RISK_WRITE/INCIDENTS_WRITE
# below — day-to-day safety operations, not administrative hierarchy edits.
_OPERATIONAL_WRITE: tuple[str, ...] = (
    ALERTS_WRITE,
    INCIDENTS_WRITE,
    COMPLIANCE_WRITE,
    RISK_WRITE,
    SENSORS_WRITE,
    PERMITS_WRITE,
    MAINTENANCE_WRITE,
    SHIFTS_WRITE,
    EMERGENCY_WRITE,
)

# Default permission grant per system role. Intentionally conservative:
# only Admin can manage users/roles or edit the facility hierarchy
# (creating a factory/site/building/zone is a rare, high-impact
# administrative action — the same category as creating a user account);
# Manager gets read-only oversight of users/roles; Supervisor/Operator/
# Viewer are purely operational. Everyone gets *_READ on the hierarchy,
# since every role needs it to navigate the dashboard/alerts/etc. by zone.
DEFAULT_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    VIEWER: _READ_ONLY,
    OPERATOR: _READ_ONLY + (ALERTS_WRITE,),
    SUPERVISOR: _READ_ONLY + _OPERATIONAL_WRITE,
    MANAGER: _READ_ONLY + _OPERATIONAL_WRITE + (USERS_READ, ROLES_READ),
    ADMIN: tuple(ALL_PERMISSIONS.keys()),
}
