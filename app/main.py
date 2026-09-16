from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.limiter import limiter
from app.api.routes_agent import router as agent_router
from app.api.routes_health import router as health_router
from app.api.routes_search import router as search_router
from app.api.routes_session import router as session_router
from app.config.settings import get_settings
from app.db.session import get_session_factory, init_db
from app.knowledge.ingest import ingest_corpus, sync_relationships
from app.reasoning.environmental_graph import load_graph

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = get_session_factory()()
    try:
        ingest_corpus(db)
        graph = load_graph()
        sync_relationships(db, graph["edges"])
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router, prefix=settings.api_prefix)
app.include_router(session_router, prefix=settings.api_prefix)
app.include_router(search_router, prefix=settings.api_prefix)
app.include_router(health_router, prefix=settings.api_prefix)

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
if FRONTEND.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND), name="assets")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND / "index.html")


@app.middleware("http")
async def isolate_retrieved_content(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response
