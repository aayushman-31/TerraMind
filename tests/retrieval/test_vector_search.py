from app.db.session import get_session_factory
from app.retrieval.vector_search import VectorSearch


def test_vector_search_returns_ranked_hits(client):
    db = get_session_factory()()
    try:
        hits = VectorSearch().search(db, "soil organic carbon biodiversity agriculture", top_k=5)
        assert hits
        assert hits[0].score >= hits[-1].score
    finally:
        db.close()
