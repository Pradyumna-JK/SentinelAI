"""Business logic for the Risk module.

Thin orchestration layer over the Compound Risk Engine (app/ai/risk) —
formats/aggregates engine output for the API. Contains no scoring logic
of its own.
"""

from fastapi import Depends

from app.ai.risk.engine import RiskEngine, get_risk_engine
from app.schemas.risk import RiskResponse


class RiskService:
    """Aggregates compound risk scores produced by the Risk Engine."""

    def __init__(self, engine: RiskEngine) -> None:
        self._engine = engine

    def list_scores(self) -> RiskResponse:
        scores = self._engine.list_scores()
        average = round(sum(score.score for score in scores) / len(scores), 1)
        highest = max(scores, key=lambda score: score.score)
        return RiskResponse(
            average_score=average,
            highest_risk_zone=highest.zone_name,
            scores=scores,
        )


def get_risk_service(engine: RiskEngine = Depends(get_risk_engine)) -> RiskService:
    return RiskService(engine)
