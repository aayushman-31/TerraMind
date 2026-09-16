from __future__ import annotations

from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from app.retrieval.embeddings import tokenize


@dataclass
class LexicalHit:
    chunk_id: str
    score: float


class LexicalIndex:
    def __init__(self) -> None:
        self.chunk_ids: list[str] = []
        self.corpus_tokens: list[list[str]] = []
        self.bm25: BM25Okapi | None = None

    def build(self, chunks: list[tuple[str, str]]) -> None:
        self.chunk_ids = [chunk_id for chunk_id, _ in chunks]
        self.corpus_tokens = [tokenize(text) for _, text in chunks]
        self.bm25 = BM25Okapi(self.corpus_tokens) if self.corpus_tokens else None

    def search(self, query: str, top_k: int = 20) -> list[LexicalHit]:
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
        max_score = max((score for _, score in ranked), default=0.0) or 1.0
        return [
            LexicalHit(chunk_id=self.chunk_ids[idx], score=float(score / max_score))
            for idx, score in ranked
            if score > 0
        ]
