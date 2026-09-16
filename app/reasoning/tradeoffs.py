from __future__ import annotations

from app.schemas.responses import Recommendation


def describe_tradeoffs(recommendations: list[Recommendation]) -> list[str]:
    notes: list[str] = []
    for rec in recommendations:
        notes.extend(rec.tradeoffs)
    return notes
