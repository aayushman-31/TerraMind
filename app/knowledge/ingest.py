from __future__ import annotations

import json
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.db.models import Document, DocumentChunk, EnvironmentalRelationship
from app.retrieval.embeddings import get_embedding_provider
from app.retrieval.hybrid_search import reset_hybrid_search

CHUNK_SIZE = 900
CHUNK_OVERLAP = 120


def semantic_chunk(text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()]
    if paragraphs:
        units = paragraphs
    else:
        units = [text]
    chunks: list[str] = []
    buf = ""
    for unit in units:
        if len(buf) + len(unit) + 1 <= CHUNK_SIZE:
            buf = f"{buf} {unit}".strip()
        else:
            if buf:
                chunks.append(buf)
            if len(unit) <= CHUNK_SIZE:
                buf = unit
            else:
                start = 0
                while start < len(unit):
                    end = min(start + CHUNK_SIZE, len(unit))
                    chunks.append(unit[start:end])
                    start = end - CHUNK_OVERLAP
                buf = ""
    if buf:
        chunks.append(buf)
    return chunks or [text]


def ingest_corpus(db: Session, corpus_dir: str | None = None) -> int:
    settings = get_settings()
    root = Path(corpus_dir or settings.corpus_path)
    if not root.is_dir():
        root = Path(__file__).resolve().parents[2] / "knowledge" / "corpus"
    provider = get_embedding_provider()
    count = 0
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        document = db.get(Document, payload["document_id"])
        if document is None:
            document = Document(document_id=payload["document_id"])
            db.add(document)
        document.title = payload["title"]
        document.authors = payload.get("authors")
        document.publisher = payload.get("publisher")
        document.year = payload.get("year")
        document.source_type = payload.get("source_type", "unknown")
        document.url = payload.get("url")
        document.domain = payload.get("domain")
        document.region = payload.get("region")
        document.methodology = payload.get("methodology")
        document.limitations = payload.get("limitations")
        existing = db.query(DocumentChunk).filter(DocumentChunk.document_id == document.document_id)
        existing.delete()
        texts: list[str] = []
        metas: list[dict] = []
        for raw in payload.get("chunks", []):
            text = raw["text"]
            for i, piece in enumerate(semantic_chunk(text)):
                texts.append(piece)
                metas.append(
                    {
                        "chunk_id": raw["chunk_id"] if i == 0 else f"{raw['chunk_id']}_{i}",
                        "domain": raw.get("domain") or payload.get("domain"),
                        "metrics": raw.get("metrics") or payload.get("metrics"),
                        "region": payload.get("region"),
                        "title": payload["title"],
                        "authors": payload.get("authors"),
                        "year": payload.get("year"),
                        "source_type": payload.get("source_type"),
                        "publisher": payload.get("publisher"),
                        "source_url": payload.get("url"),
                        "methodology": payload.get("methodology"),
                        "limitations": payload.get("limitations"),
                    }
                )
        embeddings = provider.embed(texts)
        for meta, text, embedding in zip(metas, texts, embeddings, strict=True):
            db.add(
                DocumentChunk(
                    chunk_id=meta["chunk_id"],
                    document_id=document.document_id,
                    text=text,
                    embedding=embedding,
                    metadata_json=meta,
                )
            )
            count += 1
    db.commit()
    reset_hybrid_search()
    return count


def sync_relationships(db: Session, edges: list[dict]) -> None:
    db.query(EnvironmentalRelationship).delete()
    for edge in edges:
        db.add(
            EnvironmentalRelationship(
                source_variable=edge["source"],
                relationship=edge["relationship"],
                target_variable=edge["target"],
                direction=edge["direction"],
                evidence_required=1 if edge.get("evidence_required", True) else 0,
            )
        )
    db.commit()
