from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentQueryRequest(BaseModel):
    session_id: str | None = None
    message: str | None = None
    environment: dict[str, Any] | None = None


class KnowledgeSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] | None = None


class SessionCreateRequest(BaseModel):
    title: str | None = None
