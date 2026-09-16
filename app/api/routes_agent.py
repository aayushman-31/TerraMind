from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.agent.orchestrator import AgentOrchestrator
from app.api.limiter import limiter
from app.db.session import get_db
from app.schemas.requests import AgentQueryRequest
from app.schemas.responses import AgentQueryResponse

router = APIRouter(prefix="/agent", tags=["agent"])
orchestrator = AgentOrchestrator()


@router.post("/query", response_model=AgentQueryResponse)
@limiter.limit("60/minute")
def query_agent(
    request: Request, body: AgentQueryRequest, db: Session = Depends(get_db)
) -> AgentQueryResponse:
    if not body.message and not body.environment:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="Provide message and/or environment.")
    return orchestrator.run(db, body.session_id, body.message, body.environment)
