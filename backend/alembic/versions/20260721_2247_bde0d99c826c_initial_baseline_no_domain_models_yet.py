"""initial baseline (no domain models yet)

Revision ID: bde0d99c826c
Revises: 
Create Date: 2026-07-21 22:47:46.777756
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'bde0d99c826c'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
