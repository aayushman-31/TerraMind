from __future__ import annotations

from app.retrieval.embeddings import cosine
from app.schemas.responses import EvidenceItem


def rerank(items: list[EvidenceItem], query_embedding: list[float], embeddings: dict[str, list[float]]) -> list[EvidenceItem]:
    scored: list[EvidenceItem] = []
    for item in items:
        extra = 0.0
        embedding = embeddings.get(item.chunk_id or "")
        if embedding:
            extra = cosine(query_embedding, embedding)
        cloned = item.model_copy(deep=True)
        cloned.score = float((cloned.score or 0.0) * 0.7 + extra * 0.3)
        scored.append(cloned)
    scored.sort(key=lambda item: item.score or 0.0, reverse=True)
    return scored
