from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Session as SessionModel
from app.db.session import get_db
from app.memory.session import SessionMemory
from app.schemas.requests import SessionCreateRequest

router = APIRouter(prefix="/session", tags=["session"])
memory = SessionMemory()


@router.post("")
def create_session(body: SessionCreateRequest | None = None, db: Session = Depends(get_db)) -> dict:
    title = body.title if body else None
    session_id = memory.create_session(db, title=title)
    return {"session_id": session_id}


@router.get("/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)) -> dict:
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    state = memory.load_state(db, session_id)
    messages = memory.messages(db, session_id)
    return {
        "session_id": session.session_id,
        "title": session.title,
        "environmental_state": state.model_dump(),
        "messages": [
            {"role": item.role, "content": item.content, "created_at": str(item.created_at)}
            for item in messages
        ],
    }
