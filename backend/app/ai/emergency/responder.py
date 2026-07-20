"""Emergency Response Agent placeholder.

Not implemented yet — no router or service currently exposes emergency
recommendations. Kept as an empty seam so the `ai/` package already
reflects the full agent architecture in docs/11_AI_ARCHITECTURE.md §5
ahead of that endpoint being built.
"""


class EmergencyResponseEngine:
    """Placeholder for the future emergency protocol recommendation engine."""

    def recommend(self, zone_id: str, hazard_type: str) -> dict:
        raise NotImplementedError("Emergency Response Agent is not implemented yet.")
