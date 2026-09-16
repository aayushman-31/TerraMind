from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk
from app.db.session import get_db
from app.retrieval.hybrid_search import get_hybrid_search
from app.schemas.environment import EnvironmentalState
from app.schemas.requests import KnowledgeSearchRequest
from app.schemas.responses import KnowledgeSearchResponse

router = APIRouter(tags=["knowledge"])


@router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
def search_knowledge(body: KnowledgeSearchRequest, db: Session = Depends(get_db)) -> KnowledgeSearchResponse:
    engine = get_hybrid_search()
    results = engine.search(
        db,
        body.query,
        state=EnvironmentalState(),
        top_k=body.top_k,
        filters=body.filters,
    )
    return KnowledgeSearchResponse(results=results)


@router.get("/evidence/{document_id}")
def get_evidence(document_id: str, db: Session = Depends(get_db)) -> dict:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    return {
        "document_id": document.document_id,
        "title": document.title,
        "authors": document.authors,
        "year": document.year,
        "publisher": document.publisher,
        "source_type": document.source_type,
        "url": document.url,
        "domain": document.domain,
        "region": document.region,
        "methodology": document.methodology,
        "limitations": document.limitations,
        "chunks": [{"chunk_id": c.chunk_id, "text": c.text, "metadata": c.metadata_json} for c in chunks],
    }
