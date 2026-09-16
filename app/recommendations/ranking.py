from __future__ import annotations

from app.schemas.responses import Recommendation


def rank_recommendations(recommendations: list[Recommendation]) -> list[Recommendation]:
    def key(item: Recommendation) -> tuple:
        evidence_strength = min(1.0, len(item.evidence) / 3.0)
        variables = len(item.metrics_impacted)
        return (
            evidence_strength,
            variables,
            item.internal_rank or 0.0,
        )

    ranked = sorted(recommendations, key=key, reverse=True)
    for item in ranked:
        item.internal_rank = None
    return ranked
