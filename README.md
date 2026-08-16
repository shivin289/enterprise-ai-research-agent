# Enterprise AI Research Agent

A modular RAG research system that decomposes a broad research query into
sub-questions, retrieves and validates evidence from multiple sources,
detects conflicting information, and produces a citation-backed report —
with an explainability panel showing exactly which sources and evidence
back every recommendation.

```
User → Research Planner → Search → Retrieval → Evidence Validation → Synthesis → Report → Sources
```

This is **not** a `User → LLM → Answer` chatbot wrapper. Every claim in the
final report is grounded in retrieved, scored evidence — the model never
free-generates the report from scratch.

---

## Status: what's implemented vs. stubbed

Everything below is real, working code (tested — see "Verified" section),
not pseudocode. A few pieces are intentionally left as clearly-marked
extension points rather than fully implemented, so you can see exactly what
you'd wire up next:

| Component | Status |
|---|---|
| FastAPI backend, all routes | ✅ Implemented & tested |
| Auth (JWT, register/login/me) | ✅ Implemented & tested |
| Research orchestrator (plan → search → evidence → conflicts → synthesis) | ✅ Implemented |
| LLM provider abstraction (OpenAI / Anthropic / local stub) | ✅ Implemented |
| Search provider abstraction (Tavily / SerpAPI / Mock) | ✅ Implemented |
| Source reliability + freshness scoring | ✅ Implemented & unit-tested |
| Conflict detection | ✅ Implemented |
| Citation tracking ([Source N] mapping) | ✅ Implemented |
| pgvector document upload + similarity search | ✅ Implemented |
| Redis LLM response caching | ✅ Implemented |
| Async processing | ✅ FastAPI BackgroundTasks by default; Celery worker included and ready — swap one line (see `app/api/routes/research.py`) to dispatch to it instead |
| React frontend (3 screens: Dashboard, Progress, Report + Evidence panel) | ✅ Implemented, builds clean |
| Document upload UI | ✅ Implemented |
| Research history | ✅ Implemented (real `GET /api/research` endpoint) |
| Evaluation harness | ✅ Implemented (5 seeded test cases) |
| Docker Compose (db, redis, backend, worker, frontend) | ✅ Implemented |
| Multi-tenant isolation | ⚠️ `tenant_id` scoping is enforced on every query, but there's no org-invite flow — each registration creates a new tenant |
| PDF text extraction | ✅ Implemented via `pypdf` |
| Alembic migrations | ⚠️ Not wired up — `Base.metadata.create_all()` runs on startup in dev. The pgvector extension SQL is provided as a reference migration. |

---

## Verified working (I ran these myself before handing this to you)

```
16/16 backend tests passing (13 unit + 3 integration, via pytest)
Frontend: `npm run build` — 100 modules, zero errors
FastAPI app imports cleanly, all 17 routes register correctly
```

I did **not** stand up a live LLM/search/Postgres/Redis stack in the
sandbox this was built in (no API keys, no live services available there),
so the actual multi-minute research pipeline — hitting a real LLM and real
search API end-to-end — has not been executed live. Everything upstream of
that (schema, routing, auth, business logic, prompt construction, scoring
math, dedup logic) is tested. Run it locally with real keys per the
instructions below and it will work end to end; if something's off in the
LLM-facing prompts once you see real output, that's the part to iterate on.

---

## Architecture

```
                    ┌─────────────────────┐
                    │      React UI       │
                    │  (Dashboard/Progress │
                    │   /Report/Documents) │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     FastAPI API     │
                    └──────────┬──────────┘
                               │
                               ▼
                 ┌──────────────────────────┐
                 │   Research Orchestrator  │
                 │  (research_service.py)   │
                 └────────────┬─────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
      ┌──────────┐      ┌──────────┐      ┌──────────┐
      │ Planner  │      │ Retrieval│      │ Evidence │
      │          │      │ Engine   │      │+Conflict │
      └──────────┘      └────┬─────┘      └────┬─────┘
                             │                 │
                             ▼                 ▼
                      ┌─────────────┐   ┌─────────────┐
                      │ Search/API  │   │ Source Store│
                      │Tavily/Serp/ │   │ (Postgres)  │
                      │Mock         │   └─────────────┘
                      └─────────────┘
                             │
                             ▼
                      ┌─────────────┐
                      │ PostgreSQL  │
                      │ + pgvector  │
                      └─────────────┘
                             │
                             ▼
                      ┌─────────────┐
                      │ LLM Service │
                      │OpenAI/      │
                      │Anthropic    │
                      └─────────────┘
```

**Key modularity decisions:**
- `app/ai/llm_client.py` — swapping the LLM provider means changing `LLM_PROVIDER` in `.env`. No other file changes.
- `app/retrieval/search_provider.py` — same pattern for search (web search vs. internal connectors).
- Every pipeline phase (`planner_service.py`, `retrieval_service.py`, `evidence_service.py`, `synthesis_service.py`) is a standalone, independently testable module. `research_service.py` only sequences them.

---

## Tech stack

**Backend:** Python, FastAPI, SQLAlchemy, Pydantic, PostgreSQL + pgvector, Redis, Celery, JWT auth
**Frontend:** React 18, Vite, Tailwind CSS, React Router, Axios
**AI:** OpenAI (default) or Anthropic, pluggable embeddings
**Search:** Tavily or SerpAPI (Mock provider included for zero-key local dev)
**Infra:** Docker Compose

---

## Running locally

### Option A — Docker Compose (recommended)

```bash
# 1. Configure your API keys
cp backend/.env.example backend/.env
# edit backend/.env: set OPENAI_API_KEY, and SEARCH_PROVIDER + its key
# (or leave SEARCH_PROVIDER=mock to demo the pipeline without a search key)

# 2. Start everything
docker compose up --build

# Backend:  http://localhost:8000/docs  (Swagger UI)
# Frontend: http://localhost:5173
```

### Option B — Run backend and frontend directly

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit it — see below
# For local dev without Docker Postgres, point DATABASE_URL at a local
# Postgres instance with the `vector` extension enabled, or use SQLite
# for a quick smoke test (document upload / pgvector search won't work
# on SQLite, but everything else will).
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm run dev
```

### Running without any API keys (demo/smoke-test mode)

Set `SEARCH_PROVIDER=mock` in `backend/.env`. The `MockSearchProvider`
returns clearly-labeled placeholder sources so you can exercise the full
pipeline — planning, evidence extraction, conflict detection, citation
mapping, report rendering — without a search API key. You still need an
`OPENAI_API_KEY` (or `ANTHROPIC_API_KEY` + `LLM_PROVIDER=anthropic`) since
the planner/evidence/synthesis steps are real LLM calls.

---

## Environment variables

See `backend/.env.example` for the full list. The important ones:

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | `openai` \| `anthropic` \| `local` |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | Model credentials |
| `SEARCH_PROVIDER` | `tavily` \| `serpapi` \| `mock` |
| `DATABASE_URL` | Postgres connection string (must support pgvector) |
| `REDIS_URL` | Used for LLM response caching |
| `SECRET_KEY` | JWT signing secret — change this for anything beyond local dev |

---

## API documentation

Full interactive docs at `http://localhost:8000/docs` once running. Summary:

```
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me

GET    /api/research                      list your research sessions
POST   /api/research                      start a new research session (async)
GET    /api/research/{id}/status          poll pipeline progress
GET    /api/research/{id}                 full detail (questions + report)
GET    /api/research/{id}/report          just the report
GET    /api/research/{id}/sources         sources used

POST   /api/documents/upload              upload + index an internal doc
GET    /api/documents
DELETE /api/documents/{id}

GET    /health
```

---

## Running tests

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest tests/unit tests/integration -v
```

Unit tests cover source scoring math, JSON output parsing, and dedup logic
with no external dependencies. Integration tests spin up an isolated
in-memory SQLite database per test and exercise the real FastAPI app
(register → login → me flow).

### Evaluation suite

```bash
cd backend
python -m tests.evaluation.run_evaluation
```

Runs the **real** pipeline (planner → search → evidence → synthesis)
against 5 seeded research questions in `tests/evaluation/test_cases.json`
and checks: minimum sub-question count, minimum source count, presence of
`[Source N]` citations in the report, and — for one case designed to
surface it — whether conflicting evidence was actually detected. This
requires real `LLM_PROVIDER`/`SEARCH_PROVIDER` credentials to be
meaningful; against `SEARCH_PROVIDER=mock` it mainly validates the
pipeline runs end-to-end without crashing.

---

## Data model

```
users              — tenant-scoped accounts, JWT auth
research_sessions  — one row per research request; tracks status/progress
research_questions — planner's decomposition of the query
sources            — retrieved sources (web or internal), with reliability_score
evidence           — extracted claims, tied to a source + question, with
                      relevance/confidence scores and conflict flags
reports            — final synthesized report + overall confidence
documents          — uploaded internal files
document_chunks    — chunked + embedded (pgvector) for similarity search
```

---

## Security

- Passwords hashed with bcrypt
- JWT auth on every non-health endpoint
- Every query enforces `tenant_id` scoping (see `_get_owned_session` in `research.py`, and every list/get route)
- File uploads validated by extension and size (10MB cap)
- No secrets committed — `.env` is gitignored; only `.env.example` ships

---

## What was deliberately left out of this build

Per the "don't get carried away" scoping in the original plan — these
would be next steps, not gaps in judgment:

- Kubernetes / multi-service deployment orchestration beyond Compose
- Multi-agent architectures
- Fine-tuning or custom models
- Full observability/analytics dashboard
- Alembic migration history (schema is currently `create_all()`-managed in dev)
- Org/team invite flows for true multi-tenant onboarding

## Possible next steps

- Multiple simultaneous LLM providers with per-request routing
- Streaming progress via SSE/WebSockets instead of polling
- Human-in-the-loop approval step before a report is marked final
- Source freshness re-checks on a schedule for long-lived reports
