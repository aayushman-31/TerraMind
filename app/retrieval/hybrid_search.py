from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk
from app.retrieval.config_loader import load_retrieval_weights
from app.retrieval.embeddings import get_embedding_provider
from app.retrieval.lexical_search import LexicalIndex
from app.retrieval.reranker import rerank
from app.retrieval.vector_search import VectorSearch
from app.schemas.environment import EnvironmentalState
from app.schemas.responses import EvidenceItem


def _list_match(values: list | None, wanted: set[str]) -> float:
    if not values or not wanted:
        return 0.0
    lowered = {str(item).lower() for item in values}
    return 1.0 if lowered & wanted else 0.0


class HybridSearch:
    def __init__(self) -> None:
        self.lexical = LexicalIndex()
        self.vector = VectorSearch()
        self._built = False

    def rebuild(self, db: Session) -> None:
        chunks = db.query(DocumentChunk).all()
        self.lexical.build([(chunk.chunk_id, chunk.text) for chunk in chunks])
        self._built = True

    def search(
        self,
        db: Session,
        query: str,
        state: EnvironmentalState | None = None,
        top_k: int | None = None,
        filters: dict | None = None,
    ) -> list[EvidenceItem]:
        if not self._built:
            self.rebuild(db)
        weights = load_retrieval_weights()
        k = top_k or weights.top_k
        semantic_hits = {hit.chunk_id: hit.score for hit in self.vector.search(db, query, top_k=40)}
        lexical_hits = {hit.chunk_id: hit.score for hit in self.lexical.search(query, top_k=40)}
        chunk_ids = set(semantic_hits) | set(lexical_hits)
        if not chunk_ids:
            return []

        wanted_domains = set()
        wanted_metrics = set()
        wanted_regions = set()
        if state:
            if state.scalar("soil.organic_carbon_pct") is not None:
                wanted_domains.add("soil")
                wanted_metrics.add("organic_carbon")
            if state.scalar("climate.rainfall") is not None:
                wanted_domains.add("climate")
                wanted_metrics.add("rainfall")
            if state.scalar("land.cropping_system") is not None:
                wanted_domains.add("land")
                wanted_metrics.add("cropping_system")
            if state.user_goal or state.scalar("biodiversity.species_richness") is not None:
                wanted_domains.add("biodiversity")
                wanted_metrics.add("species_richness")
            region = state.scalar("location.region")
            if region:
                wanted_regions.add(str(region).lower())
                wanted_regions.add("semi-arid")
        if filters:
            if filters.get("domain"):
                wanted_domains.add(str(filters["domain"]).lower())
            if filters.get("metric"):
                wanted_metrics.add(str(filters["metric"]).lower())

        items: list[EvidenceItem] = []
        embeddings: dict[str, list[float]] = {}
        for chunk_id in chunk_ids:
            chunk = db.get(DocumentChunk, chunk_id)
            if not chunk:
                continue
            document = db.get(Document, chunk.document_id)
            if not document:
                continue
            meta = chunk.metadata_json or {}
            domains = meta.get("domain") or document.domain or []
            metrics = meta.get("metrics") or []
            regions = meta.get("region") or document.region or []
            if filters and filters.get("domain"):
                if str(filters["domain"]).lower() not in {str(d).lower() for d in domains}:
                    continue
            score = (
                weights.semantic_weight * semantic_hits.get(chunk_id, 0.0)
                + weights.lexical_weight * lexical_hits.get(chunk_id, 0.0)
                + weights.domain_weight * _list_match(domains, wanted_domains)
                + weights.geographic_weight * _list_match(regions, wanted_regions)
                + weights.metric_weight * _list_match(metrics, wanted_metrics)
            )
            if chunk.embedding:
                embeddings[chunk_id] = chunk.embedding
            items.append(
                EvidenceItem(
                    document_id=document.document_id,
                    chunk_id=chunk.chunk_id,
                    title=document.title,
                    source=document.source_type,
                    year=document.year,
                    publisher=document.publisher,
                    source_url=document.url,
                    text=chunk.text,
                    score=score,
                    domain=list(domains),
                    metrics=list(metrics),
                    limitations=document.limitations,
                    methodology=document.methodology,
                )
            )
        items.sort(key=lambda item: item.score or 0.0, reverse=True)
        provider = get_embedding_provider()
        query_vec = provider.embed([query])[0]
        reranked = rerank(items[: max(k * 2, weights.rerank_k)], query_vec, embeddings)
        filtered = [item for item in reranked if (item.score or 0) >= weights.min_evidence_score]
        return filtered[:k]


_ENGINE: HybridSearch | None = None


def get_hybrid_search() -> HybridSearch:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = HybridSearch()
    return _ENGINE


def reset_hybrid_search() -> None:
    global _ENGINE
    _ENGINE = None
