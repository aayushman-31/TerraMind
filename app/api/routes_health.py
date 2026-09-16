from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.db.models import Document
from app.db.session import get_db
from app.schemas.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    count = db.query(Document).count()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        database="up",
        documents_indexed=count,
    )
