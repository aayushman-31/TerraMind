from __future__ import annotations

from app.schemas.responses import Recommendation


REQUIRED_FIELDS = [
    "action",
    "why_it_works",
    "metrics_impacted",
    "estimated_effect",
    "time_horizon",
    "confidence",
    "measurement_plan",
]


def validate_recommendations(recommendations: list[Recommendation]) -> list[Recommendation]:
    valid: list[Recommendation] = []
    for rec in recommendations:
        if not rec.action or not rec.why_it_works:
            continue
        if not rec.metrics_impacted or not rec.time_horizon:
            continue
        missing = [field for field in REQUIRED_FIELDS if not getattr(rec, field)]
        if missing:
            continue
        if not rec.evidence:
            rec.confidence = "low"
            rec.estimated_effect = (
                "I found insufficient evidence to make a reliable quantitative estimate for this specific condition. "
                "A qualitative recommendation is offered, but the expected magnitude of improvement is uncertain."
            )
        valid.append(rec)
    return valid
