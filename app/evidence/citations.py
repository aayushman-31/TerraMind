from app.schemas.responses import EvidenceItem, Recommendation


def attach_citations(rec: Recommendation) -> list[str]:
    return [item.document_id for item in rec.evidence]
