# Solvary Backend

FastAPI backend for Solvary — a LeetCode-style challenge platform with (upcoming)
live collaborative workspaces. Architecture and conventions: see
[`../SOLVARY_DESIGN.md`](../SOLVARY_DESIGN.md) (the build contract).

## Run

```powershell
# API on :8010 (the frontend's Vite proxy expects this port)
.venv\Scripts\python -m uvicorn app.main:app --port 8010 --reload
```

One-time setup:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m scripts.seed_admin      # admin@solvary.dev / admin123
.venv\Scripts\python -m scripts.seed_problems   # two-sum, fizzbuzz, mean-of-list
```

## Deploy (Docker)

The full production stack (Postgres 16 + Piston + backend + nginx frontend)
lives in [`../deploy/compose.yml`](../deploy/compose.yml):

```powershell
cd ..\deploy
cp .env.example .env          # set SECRET_KEY + POSTGRES_PASSWORD
docker compose up -d --build
# one-time: language runtimes (compose network — piston is not host-exposed)
docker compose exec backend python -c "import httpx; [print(httpx.post('http://piston:2000/api/v2/packages', json={'language':l,'version':v}, timeout=600).text) for l,v in [('python','3.12.0'),('node','20.11.1')]]"
docker compose exec backend python -m scripts.seed_admin
docker compose exec backend python -m scripts.seed_problems
```

App on http://localhost:8080. Production posture baked in: migrations run
before serve (lifespan create_all is disabled under ENVIRONMENT=production),
non-root containers, `/api/ready` reports per-dependency health (DB +
Piston) for orchestrator traffic gating, nginx proxies SSE unbuffered and
upgrades `/ws`. Put TLS in front for real deployments — the refresh cookie
is `Secure` in production. Backend is single-replica until the Redis
queue/backplane lands.

## Authentication

- Access tokens are short-lived JWTs; a **refresh token** (httpOnly cookie,
  rotated on every use, revocable server-side) keeps sessions alive. The
  frontend auto-refreshes on 401. `POST /auth/logout` revokes.
- Login/register are **rate limited** (per IP + per target email, in-memory).
- With `ENVIRONMENT=production`, the app **refuses to boot** on the default
  `SECRET_KEY`.
- **Google sign-in**: create an OAuth client ID (type "Web application") in
  Google Cloud Console with your origin (e.g. http://localhost:5173) as an
  authorized JavaScript origin, then set `GOOGLE_CLIENT_ID` in the backend
  `.env` and `VITE_GOOGLE_CLIENT_ID` in the frontend `.env`. The button
  appears automatically; the backend verifies Google's ID token against its
  JWKS and creates or links the account (verified emails only).

## Code execution providers

Selected by `EXECUTION_PROVIDER` (env or `.env`; see `.env.example`):

- **`mock`** (default) — no real execution; deterministic simulation for dev/tests.
  Steer verdicts with magic markers in submitted code: `__MOCK_WA__`, `__MOCK_TLE__`,
  `__MOCK_RTE__`, `__MOCK_CE__` (otherwise: accepted).
- **`piston`** — real sandboxed execution (Python 3.12, Node 20) via self-hosted
  [Piston](https://github.com/engineer-man/piston). Needs Docker:

  ```powershell
  cd ..\deploy\piston
  docker compose up -d
  # one-time: install language runtimes (persist in a volume)
  curl -X POST http://localhost:2000/api/v2/packages -H "Content-Type: application/json" -d '{\"language\":\"python\",\"version\":\"3.12.0\"}'
  curl -X POST http://localhost:2000/api/v2/packages -H "Content-Type: application/json" -d '{\"language\":\"node\",\"version\":\"20.11.1\"}'
  ```

  Then run the API with `EXECUTION_PROVIDER=piston`.

  Why Piston and not Judge0: Judge0's isolate needs cgroup v1 and segfaults on modern
  Docker Desktop (cgroup v2). Design decision #5, amended v2.1.

## Collaborative workspaces (M3)

Live multi-user editing via Yjs CRDTs. The server speaks real y-protocol over
`WS /ws/workspaces/{id}` (JWT rides the subprotocol), relays updates, persists
snapshot + update log, and enforces owner/editor/viewer RBAC — viewers get a
readOnly editor and the server drops (and resyncs) any doc update they send.
File metadata is REST-authoritative; content is CRDT-only, keyed by file id.
Try it: two browsers, same workspace, `/workspaces` — live cursors included.

## Challenge attempts (M4)

A workspace bound to a problem IS a challenge attempt: "Solve together" on any
problem page creates one seeded with the starter code. Members edit the same
buffer live; any editor can Submit (workspace-tagged), and every member —
viewers included — follows the same verdict stream (the submission id rides
Yjs awareness). Shared history: `GET /v1/submissions?workspace_id=...`.

## Tests

```powershell
.venv\Scripts\python -m pytest -q            # includes Piston contract tests when it's up
.venv\Scripts\python -m ruff check app scripts tests
```

Tests are fully isolated: they run against `solvary_test.db` (schema rebuilt
each session, admin seeded by conftest) and never touch the dev database.
Piston integration tests auto-skip when no engine is reachable on :2000.

To run the suite against Postgres (what CI does):

```powershell
docker run -d --name solvary-pg -e POSTGRES_USER=solvary -e POSTGRES_PASSWORD=solvary -e POSTGRES_DB=solvary_test -p 5433:5432 postgres:16
$env:TEST_DATABASE_URL = "postgresql+asyncpg://solvary:solvary@localhost:5433/solvary_test"
.venv\Scripts\python -m pytest -q
```

## CI

`.github/workflows/ci.yml` runs on every push/PR: backend ruff + pytest on
SQLite, the full suite plus the Alembic migration chain on Postgres 16, and
frontend eslint + build.
