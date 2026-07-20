"""Reserved for the database engine/session layer.

No persistent store is wired up yet — every service currently operates on
in-memory dummy data (see app/services/*.py). This package exists so the
eventual SQLAlchemy engine/session setup (docs/07_DATABASE_DESIGN.md) has a
home without requiring another structural reorganization when it lands.
"""
