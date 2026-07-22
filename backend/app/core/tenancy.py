"""Automatic, ORM-level tenant scoping — layer 1 of 2.

The core problem with multi-tenancy bugs: every query against a
tenant-scoped table has to remember to add `WHERE organization_id = ...`,
by hand, forever, in every service method, forever. Miss it once and one
company sees another company's data. This module removes the "by hand"
part: any model that inherits `TenantScoped` gets an automatic
`organization_id` filter injected into *every* SELECT/`session.get()`
issued against it, for the lifetime of the request — via SQLAlchemy 2's
`with_loader_criteria`, registered on a session-wide `do_orm_execute` event.
A developer would have to go out of their way to bypass this, not forget it.

Layer 2 (the backstop for "went out of their way", or for raw SQL that
never goes through the ORM at all) is PostgreSQL Row-Level Security — see
alembic/versions/*_tenant_isolation_rls.py and app/db/session.py, which
feeds this same contextvar's value into Postgres as a session variable.

Both layers read the *same* source of truth: `current_organization_id`,
set once per request by `OrganizationContextMiddleware`
(app/core/middleware.py) from the validated JWT — never from a client-
supplied header, query param, or body field. There is deliberately no way
to ask the API "show me organization X's data" by passing X in; the only
input is "who does this token belong to," which is exactly what
`get_current_user` already establishes.
"""

import contextvars
import uuid
from typing import ClassVar

from sqlalchemy import ForeignKey, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, Session, declared_attr, mapped_column, with_loader_criteria

current_organization_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_organization_id", default=None
)


class TenantScoped:
    """Mixin for models that must never be visible across organizations.

    Declares the `organization_id` column itself (via `declared_attr`, so
    each subclass gets its own concrete column with the shared shape:
    non-nullable FK to organizations, indexed, CASCADE on org deletion).
    This is load-bearing, not just DRY: `with_loader_criteria` resolves the
    criteria lambda against this base class, so the attribute must exist
    *on the mixin* — a pure marker mixin with per-model columns fails at
    query time with "type object 'TenantScoped' has no attribute
    'organization_id'" (found the hard way; this is also how SQLAlchemy's
    own docs structure the pattern).
    """

    __tenant_scoped__: ClassVar[bool] = True

    @declared_attr
    def organization_id(cls) -> Mapped[uuid.UUID]:  # noqa: N805 — SQLAlchemy passes the class
        return mapped_column(
            UUID(as_uuid=True),
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )


@event.listens_for(Session, "do_orm_execute")
def _inject_tenant_filter(execute_state) -> None:
    """Adds `WHERE organization_id = <current tenant>` to every ORM SELECT.

    Applies to `TenantScoped` subclasses only, including through
    `Session.get()`, relationship lazy-loads, and joins — anywhere
    SQLAlchemy would otherwise construct a SELECT against one of these
    entities. Deliberately does nothing (no filter, not "filter to nothing")
    when there's no tenant context: that's the correct behavior for
    non-request code paths (a startup script, a maintenance task) that pass
    `organization_id` explicitly instead of relying on ambient context —
    trying to *guess* a safe default there would be worse than staying out
    of the way.
    """
    if not execute_state.is_select:
        return

    tenant_id = current_organization_id.get()
    if tenant_id is None:
        return

    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            TenantScoped,
            lambda cls: cls.organization_id == tenant_id,
            include_aliases=True,
        )
    )
