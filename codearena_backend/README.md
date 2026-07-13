# CodeArena Backend

FastAPI backend for CodeArena — a LeetCode-style challenge platform with (upcoming)
live collaborative workspaces. Architecture and conventions: see
[`../CODEARENA_DESIGN.md`](../CODEARENA_DESIGN.md) (the build contract).

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
.venv\Scripts\python -m scripts.seed_admin      # admin@codearena.dev / admin123
.venv\Scripts\python -m scripts.seed_problems   # two-sum, fizzbuzz, mean-of-list
```

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

## Tests

```powershell
.venv\Scripts\python -m pytest -q            # includes Piston contract tests when it's up
.venv\Scripts\python -m ruff check app scripts tests
```

Piston integration tests auto-skip when no engine is reachable on :2000.
