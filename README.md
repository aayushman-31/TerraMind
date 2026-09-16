# Darukaa Biodiversity Intelligence Agent

Evidence-grounded **AI environmental scientist** for biodiversity and land-health recommendations. This is not a ChatGPT wrapper: environmental state, hybrid retrieval, a machine-readable relationship graph, and citation verification are deterministic components. The language model is optional and used only for phrasing and extra extraction.

## Problem statement

Land managers describe farms and ecosystems in natural language. Generic chat tools invent statistics and citations. This system converts conversation into a structured environmental state, retrieves FAO/IPCC/IPBES and peer-reviewed evidence from a real index, reasons across at least three variables (soil, water/climate, land use / human impact), and returns interventions with metrics, time horizons, assumptions, and sources that actually exist in the knowledge base.

## Architecture

```
Frontend (chat + state + evidence)
        ↓
FastAPI
        ↓
Agent orchestrator (state machine)
        ↓
Extraction → Memory → Completeness
        ↓
Hybrid retrieval (vector + BM25 + metadata + rerank)
        ↓
Multi-metric graph reasoning
        ↓
Recommendation engine → evidence verifier
```

See section 24 of the build spec for the full diagram. Modules live under `app/` exactly as specified: `agent`, `extraction`, `retrieval`, `reasoning`, `recommendations`, `evidence`, `memory`, `schemas`, `config`.

## Data flow

1. User message and/or JSON environment payload.
2. Entity extraction and merge into session environmental state.
3. Completeness check (high-value questions only).
4. Contextual retrieval query from state + problem + candidate practices.
5. Hybrid ranking with configurable weights in `config/retrieval.yaml`.
6. Graph pathways from activated variables.
7. Candidate interventions from `config/interventions.yaml`.
8. Claim verification (unsupported percentages removed).
9. Structured API response and UI panels.

## Knowledge-base design

Documents in `knowledge/corpus/*.json` are ingested at startup:

- parse JSON records
- clean/chunk text
- attach metadata (domain, metrics, region, URL, methodology, limitations)
- hashing or sentence-transformer embeddings
- BM25 lexical index

Sources are real institutional and peer-reviewed works (FAO, IPCC, IPBES, UNEP, Science Advances, Global Change Biology, and others). Chunk text is original synthesis for retrieval, not a dump of copyrighted PDFs. Citations always point at documents in this index.

## Database schema

PostgreSQL (Docker) or SQLite (local tests). Tables:

- `users`, `sessions`, `messages`
- `environmental_states`, `environmental_observations`
- `documents`, `document_chunks` (embeddings stored as JSON; pgvector-ready)
- `environmental_relationships`
- `recommendations`, `evidence_links`
- `evaluation_cases`

## Retrieval pipeline

`final_score = 0.40 semantic + 0.25 lexical + 0.15 domain + 0.10 geographic + 0.10 metric`

Weights are only in `config/retrieval.yaml`. Query construction uses user text + environmental state + problem + intervention terms, not the raw sentence "Biodiversity is declining" alone.

## Reasoning pipeline

`config/environmental_graph.yaml` encodes relationships such as:

- soil organic carbon → soil biological activity → vegetation/habitat → species richness
- rainfall → water availability → plant survival → habitat persistence → species richness
- monoculture → low structural diversity → fewer niches → biodiversity pressure

The LLM does not invent these edges.

## Recommendation pipeline

Interventions must address multiple activated nodes when possible. Each recommendation includes action, why, metrics, expected direction, time horizon, evidence, confidence, assumptions, tradeoffs, and a measurement plan. Internal ranking is not shown as a fake AI score.

## Environment variables

Copy `.env.example`. Important keys:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy URL |
| `OPENAI_API_KEY` | Optional LLM phrasing/extraction |
| `EMBEDDING_BACKEND` | `hashing` (default) or `sentence-transformers` |
| `RATE_LIMIT_PER_MINUTE` | API throttle |

Never commit secrets. Keys are not embedded in Python, frontend JS, Docker image layers, or this README.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
copy .env.example .env
```

## Local setup (SQLite)

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# In .env set:
# DATABASE_URL=sqlite+pysqlite:///./data/darukaa.db
python -m uvicorn app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000 — knowledge is ingested automatically on startup.

## Database setup

Docker Compose starts PostgreSQL 16 with pgvector. Local tests use SQLite so CI does not need Postgres.

## Knowledge ingestion

Startup calls `ingest_corpus`. To re-run:

```bash
python scripts/ingest.py
```

## How to run

```bash
docker compose up --build
```

This starts Postgres and the API+UI on port 8000.

## How to test

PowerShell, from the repo root, with the virtualenv active:

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check app tests
python -m mypy app
python evaluation/run_eval.py
```

Useful single checks:

```powershell
python -m pytest tests/e2e/test_complete_case.py -q
python -m pytest tests/e2e/test_clarification.py tests/e2e/test_memory.py -q
```

## API documentation

Interactive docs: http://127.0.0.1:8000/docs

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/session` | Create session |
| GET | `/api/v1/session/{session_id}` | Memory + state |
| POST | `/api/v1/agent/query` | Agent turn (text and/or JSON) |
| POST | `/api/v1/knowledge/search` | Debug hybrid retrieval |
| GET | `/api/v1/evidence/{document_id}` | Source record |
| GET | `/api/v1/health` | Liveness + index size |

### Example query

```json
{
  "message": "Biodiversity is declining on my farm. I grow wheat and rainfall has been low."
}
```

Expected: `clarification_required` asking for soil organic carbon, pH, and cropping system.

Follow-up:

```json
{
  "session_id": "<id>",
  "message": "Organic carbon is 0.3%, pH is 7.8, and it is continuous wheat monoculture."
}
```

Expected: `recommendation_ready` with multi-variable reasoning, retrieved FAO/IPBES/literature evidence, and no invented percentages.

Structured JSON is also valid in `environment` or as the message body.

## Evaluation methodology

`evaluation/cases.json` covers:

1. low SOC + low rainfall + monoculture
2. high rainfall + fragmentation + deforestation
3. pollution + low richness + disturbance
4. incomplete information
5. no relevant evidence / abstention
6. conflicting cover-crop evidence

Automated tests measure schema validity, clarification, memory, citation presence, unsupported-claim stripping, and multi-metric activation. Manual review should still judge scientific applicability.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) on push: install, lint, type-check, pytest. Docker image build is optional and not required for MVP cloud deploy.

## Limitations

- Default embeddings are deterministic hashing so the demo runs offline; semantic quality is better with `sentence-transformers`.
- Corpus is a curated retrieval layer, not a full-text library of paywalled PDFs.
- Geospatial APIs are architected (`latitude`/`longitude` on state) but not required for MVP.
- LLM keys improve phrasing; the scientist pipeline runs without them.

## Future improvements

- pgvector ANN indexes and a cross-encoder reranker
- Optional climate/land-cover lookup from coordinates
- Richer soil-taxonomy and regional species lists
- Human expert review queue for high-stakes restoration advice
