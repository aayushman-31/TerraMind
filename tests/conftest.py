from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "darukaa.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("EMBEDDING_BACKEND", "hashing")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.chdir(ROOT)
    from app.config.settings import get_settings
    from app.db.session import reset_engine
    from app.retrieval.hybrid_search import reset_hybrid_search

    get_settings.cache_clear()
    reset_engine()
    reset_hybrid_search()
    from app.retrieval.embeddings import get_embedding_provider

    get_embedding_provider.cache_clear()

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
    reset_engine()
    get_settings.cache_clear()
