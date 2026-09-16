#!/usr/bin/env python3
from app.db.session import get_session_factory, init_db
from app.knowledge.ingest import ingest_corpus, sync_relationships
from app.reasoning.environmental_graph import load_graph


def main() -> None:
    init_db()
    db = get_session_factory()()
    try:
        n = ingest_corpus(db)
        sync_relationships(db, load_graph()["edges"])
        print(f"Indexed {n} chunks.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
