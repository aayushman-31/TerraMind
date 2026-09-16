from sqlalchemy.orm import Session

from app.db.models import Document


def get_document(db: Session, document_id: str) -> Document | None:
    return db.get(Document, document_id)
