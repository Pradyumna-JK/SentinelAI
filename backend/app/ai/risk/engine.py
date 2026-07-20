"""Compound Risk Engine.

Currently returns static, representative risk scores. Will be replaced with
real vision/sensor signal fusion (docs/11_AI_ARCHITECTURE.md §3) — the
public interface (`RiskEngine.list_scores`) is already the shape that
implementation will fill in, so `services/risk_service.py` will not need to
change when that happens.
"""

from functools import lru_cache

from app.models.enums import RiskLevel
from app.schemas.risk import RiskScore
from app.utils.generators import utc_now


class RiskEngine:
    """Computes/retrieves compound risk scores per zone."""

    def __init__(self) -> None:
        self._scores = [
            RiskScore(
                id="risk-001",
                zone_id="zone-001",
                zone_name="Loading Dock A",
                score=82.0,
                level=RiskLevel.HIGH,
                rationale=(
                    "Elevated due to PPE violation (conf. 0.94) correlated with gas sensor "
                    "reading 40% above baseline."
                ),
                confidence="full",
                created_at=utc_now(),
            ),
            RiskScore(
                id="risk-002",
                zone_id="zone-002",
                zone_name="Assembly Line 3",
                score=41.0,
                level=RiskLevel.MEDIUM,
                rationale="Vibration anomaly on conveyor motor with no corroborating vision signal.",
                confidence="partial",
                created_at=utc_now(),
            ),
            RiskScore(
                id="risk-003",
                zone_id="zone-003",
                zone_name="Chemical Storage",
                score=12.0,
                level=RiskLevel.LOW,
                rationale="All sensor and vision signals within normal operating range.",
                confidence="full",
                created_at=utc_now(),
            ),
        ]

    def list_scores(self) -> list[RiskScore]:
        return self._scores


@lru_cache
def get_risk_engine() -> RiskEngine:
    return RiskEngine()
