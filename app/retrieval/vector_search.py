from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.retrieval.embeddings import cosine, get_embedding_provider


@dataclass
class VectorHit:
    chunk_id: str
    score: float


class VectorSearch:
    def search(self, db: Session, query: str, top_k: int = 20) -> list[VectorHit]:
        provider = get_embedding_provider()
        query_vec = provider.embed([query])[0]
        hits: list[VectorHit] = []
        chunks = db.query(DocumentChunk).all()
        for chunk in chunks:
            if not chunk.embedding:
                continue
            hits.append(VectorHit(chunk_id=chunk.chunk_id, score=cosine(query_vec, chunk.embedding)))
        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]
