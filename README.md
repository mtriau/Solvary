# Solvary

**A coding-practice platform with four modes** — solve algorithm problems against a sandboxed judge, run timed multi-stage mock interviews judged by pytest, grind quick idiomatic-Python drills, or pair up and solve problems *together* in a live shared editor with presence cursors and a shared verdict stream.

[![CI](https://github.com/mtriau/Solvary/actions/workflows/ci.yml/badge.svg)](https://github.com/mtriau/Solvary/actions/workflows/ci.yml)

## What it does

- **Problems & judging** — a problem catalog (statement, starter code, sample + hidden tests) with real sandboxed execution via [Piston](https://github.com/engineer-man/piston). Verdicts stream live over SSE: `queued → running → test 3/4 → Accepted (12ms)`.
- **Mock interviews** — timed, multi-stage take-home style screens (markdown chunker, message history, …) judged with real `pytest` test files shown to the candidate. Stages advance on green tests, the clock keeps running, and a review page replays every stage with the submitted code and an AI code review. Ships with reconstructed Perplexity and Sierra practice sets.
- **Drills** — 62 tiny exercises in 14 topics: Python idioms (comprehensions, `Counter`/`defaultdict`, sorting keys, `zip`/`enumerate`, slicing, generators, EAFP/walrus/dataclasses) and interview building blocks (hash-map tricks, stacks and queues, loop exit conditions, two pointers and windows, graph skeletons, recursion and backtracking). Each enforces the idiom behaviourally where it can (linear-time inputs, recursion-depth chains, call counting) and reveals a worked solution once your tests pass.
- **Collaborative workspaces** — multiple people editing the same code simultaneously (CRDT via [Yjs](https://yjs.dev) + Monaco), with presence cursors, role-based access (owner/editor/viewer), and server-authoritative file management.
- **Challenge attempts = the two combined** — bind a problem to a workspace and pair-solve it: starter code seeded server-side, any editor can submit, and every member watches the same verdict stream live (pair-interview mode, essentially).
- **No boilerplate imports** — every Python run gets `Counter`, `defaultdict`, `deque`, `heapq`, `bisect`, `itertools`, `functools`, `math`, `typing` and friends preloaded, the way LeetCode does; an **Auto-imports** button lists them.
- **Stats & accolades** — a home page with solve counts, acceptance rate, streaks, a contribution-style activity heatmap, and 13 earnable badges. Every past submission's code is viewable from the problem page and the interview review.
- **AI assistant** — streamed tutoring hints and interview code review from any OpenAI-compatible LLM server (local or cloud); a canned mock provider is the default so nothing needs a key.
- **Auth** — email/password or Google sign-in, short-lived JWTs with rotated refresh tokens (httpOnly cookie), login rate limiting, per-user execution quotas.

## Architecture (the short version)

```
solvary_react  (React 19 + Vite + Monaco + Yjs)
      │  REST + SSE (fetch-streaming)        │  WebSocket (y-protocol)
      ▼                                      ▼
solvary_backend  (FastAPI) ── routes → services → repositories → SQLite/Postgres
      │                                      │
      │  job queue ──► judge workers         │  collab rooms (pycrdt docs,
      │  (memory or Redis)                   │   snapshots + update log)
      ▼                                      ▼
   Piston sandbox (Docker)              Redis backplane (multi-instance)
```

Design principles, decision register, and the full data model live in **[SOLVARY_DESIGN.md](SOLVARY_DESIGN.md)** — the build contract this was implemented against. Highlights:

- **Untrusted code never runs in the API process** — the executor (Piston) is the isolation boundary.
- **Provider seams everywhere** — mock ↔ real DB, mock ↔ Piston executor, memory ↔ Redis queue/backplane, all swapped by env var. The whole test suite runs with zero infrastructure.
- **Replay-then-follow SSE** — the judge worker persists progress incrementally, so a verdict stream survives page reloads and can be watched by late joiners (that's what makes shared verdict streams work).
- **Scales horizontally** — with `QUEUE_BACKEND=redis` + `REALTIME_BACKPLANE=redis`, any replica's worker judges any job and WebSocket clients on different replicas collaborate through the Redis backplane.

## Repository layout

| Path | What |
|---|---|
| [`solvary_backend/`](solvary_backend/) | FastAPI backend — API, judge pipeline, collab engine, Alembic migrations, tests |
| [`solvary_react/`](solvary_react/) | React frontend — problems, editor, mock interviews, drills, workspaces, home/stats |
| [`deploy/`](deploy/) | Production Docker Compose stack (Postgres + Redis + Piston + backend + nginx) |
| [`SOLVARY_DESIGN.md`](SOLVARY_DESIGN.md) | The design contract: decisions, data model, protocols, milestones, changelog |
| [`SOLVARY_INTERVIEWS_DESIGN.md`](SOLVARY_INTERVIEWS_DESIGN.md) | Design doc for the mock-interview mode |
| [`solvary_backend/content/`](solvary_backend/content/) | Interview sets and drills as files (statement, stub, reference, tests, notes) |
| [`reports/`](reports/) | Research behind the practice sets (e.g. the Sierra interview report) |

## Quickstart (dev)

Prereqs: Python 3.13+, Node 20+, and (only for real code execution) Docker.

```bash
# Backend — http://localhost:8010
cd solvary_backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt -r requirements-dev.txt   # Windows
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m scripts.seed_admin       # admin@solvary.dev / admin123
.venv/Scripts/python -m scripts.seed_problems    # starter catalog
.venv/Scripts/python -m scripts.seed_drills      # 62 Python idiom + algorithm-skeleton drills
.venv/Scripts/python -m scripts.seed_interviews  # mock interview + practice sets
.venv/Scripts/python -m scripts.seed_perplexity
.venv/Scripts/python -m scripts.seed_sierra
.venv/Scripts/python -m uvicorn app.main:app --port 8010 --reload

# Frontend — http://localhost:5173 (proxies /api and /ws to :8010)
cd solvary_react
npm install
npm run dev
```

Without Docker, the judge runs in **mock mode** (every submission accepted; steer verdicts with `__MOCK_WA__` / `__MOCK_TLE__` / `__MOCK_CE__` markers in the code). Mock interviews and drills need real execution, since they run `pytest` against your code:

```bash
cd deploy/piston
docker compose up -d
./install-runtimes.sh        # one-time: installs python + node runtimes
# then run the backend with EXECUTION_PROVIDER=piston
```

## Tests

```bash
cd solvary_backend
.venv/Scripts/python -m pytest -q
```

The suite is infrastructure-free by default; integration tests marked `piston` / `redis` auto-skip unless those services are reachable (CI runs everything: SQLite + Postgres + Redis matrix).

## Production

```bash
cd deploy
cp .env.example .env         # set SECRET_KEY + POSTGRES_PASSWORD
docker compose up -d --build
./piston/install-runtimes.sh
docker compose exec backend python -m scripts.seed_admin
docker compose exec backend python -m scripts.seed_problems
docker compose exec backend python -m scripts.seed_drills
docker compose exec backend python -m scripts.seed_interviews
docker compose exec backend python -m scripts.seed_perplexity
docker compose exec backend python -m scripts.seed_sierra
```

App on `http://localhost:8080`. Migrations run before serve; `/api/ready` gates traffic on DB + sandbox health; scale out with `docker compose up -d --scale backend=3`. Put TLS in front for real deployments. Details in [`solvary_backend/README.md`](solvary_backend/README.md).

## Key configuration

| Env var | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./solvary.db` | SQLite for dev, `postgresql+asyncpg://…` for prod |
| `EXECUTION_PROVIDER` | `mock` | `mock` or `piston` |
| `QUEUE_BACKEND` | `memory` | `memory` (single instance) or `redis` (scale-out) |
| `REALTIME_BACKPLANE` | `memory` | collab room fan-out: `memory` or `redis` |
| `ENVIRONMENT` | `dev` | `production` enables secure cookies + config fail-fasts |
| `GOOGLE_CLIENT_ID` | *(empty)* | set to enable Google sign-in (plus `VITE_GOOGLE_CLIENT_ID` at frontend build) |
| `LLM_PROVIDER` | `mock` | `mock` or `openai` (any OpenAI-compatible server via `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`) |
