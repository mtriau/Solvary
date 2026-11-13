# Solvary

Solvary is a coding-practice platform: a judged problem catalogue, quick
Python idiom drills, live collaborative workspaces, and timed mock
interviews with a pacing coach, plus a home page of stats and accolades.
This folder is the FastAPI backend; the React frontend is in
[`../solvary_react`](../solvary_react). Architecture and conventions: see
[`../SOLVARY_DESIGN.md`](../SOLVARY_DESIGN.md) (the build contract, with a
changelog) and [`../SOLVARY_INTERVIEWS_DESIGN.md`](../SOLVARY_INTERVIEWS_DESIGN.md).

The four modes in the top nav:

| Mode | What it is | Section |
|---|---|---|
| **Problems** | LeetCode-style catalogue: Run, Submit, verdict stream, Ask AI, past submissions with code | [Ad-hoc Run](#ad-hoc-run), [AI assistant](#ai-assistant) |
| **Drills** | 62 two-minute Python idiom and algorithm-skeleton exercises with a gated idiomatic solution and notes | [Drills](#drills) |
| **Workspaces** | Live multi-user editing (Yjs) with RBAC; bind one to a problem to solve together | [Collaborative workspaces](#collaborative-workspaces-m3), [Challenge attempts](#challenge-attempts-m4) |
| **Interviews** | Timed, staged mock interviews (Perplexity and Sierra practice sets), review with editorials and your code | [Mock interviews](#mock-interviews) |

## Run locally

Backend (API on :8010, which the frontend's Vite proxy expects):

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m scripts.seed_admin        # admin@solvary.dev / admin123
.venv\Scripts\python -m scripts.seed_problems     # two-sum, fizzbuzz, mean-of-list
.venv\Scripts\python -m scripts.seed_drills       # the 62 drills
.venv\Scripts\python -m scripts.seed_interviews   # kv-store-levels + warmup-questions
.venv\Scripts\python -m scripts.seed_perplexity   # Perplexity coding-screen set
.venv\Scripts\python -m scripts.seed_sierra       # Sierra phone-screen set
.venv\Scripts\python -m uvicorn app.main:app --port 8010 --reload
```

Frontend (http://localhost:5173; `/api` and `/ws` are proxied to :8010):

```powershell
cd ..\solvary_react
npm install
npm run dev
```

Real code execution needs Piston (Docker); without it the default `mock`
provider simulates verdicts. See [Code execution providers](#code-execution-providers).
Settings come from `.env` (see `.env.example`); every seeder is idempotent
and skips what already exists.

Known Windows quirk: uvicorn's `--reload` sometimes misses a change (new
router modules in particular). If the live API disagrees with the code,
restart the backend.

## Deploy (Docker)

The full production stack (Postgres 16 + Redis + Piston + backend + nginx
frontend) lives in [`../deploy/compose.yml`](../deploy/compose.yml):

```powershell
cd ..\deploy
cp .env.example .env          # set SECRET_KEY + POSTGRES_PASSWORD
docker compose up -d --build
# one-time: language runtimes (compose network — piston is not host-exposed)
docker compose exec backend python -c "import httpx; [print(httpx.post('http://piston:2000/api/v2/packages', json={'language':l,'version':v}, timeout=600).text) for l,v in [('python','3.12.0'),('node','20.11.1')]]"
docker compose exec backend python -m scripts.seed_admin
docker compose exec backend python -m scripts.seed_problems
docker compose exec backend python -m scripts.seed_drills
docker compose exec backend python -m scripts.seed_interviews
docker compose exec backend python -m scripts.seed_perplexity
docker compose exec backend python -m scripts.seed_sierra
```

App on http://localhost:8080. Production posture baked in: migrations run
before serve (lifespan create_all is disabled under ENVIRONMENT=production),
non-root containers, `/api/ready` reports per-dependency health (DB +
Piston) for orchestrator traffic gating, nginx proxies SSE unbuffered and
upgrades `/ws`. Put TLS in front for real deployments — the refresh cookie
is `Secure` in production. The backend image ships `content/` so the
practice-set seeders work inside the container.

**Scaling out**: with `QUEUE_BACKEND=redis` and `REALTIME_BACKPLANE=redis`
(the compose defaults), the backend scales horizontally:

```powershell
docker compose up -d --scale backend=3
```

The job queue (Redis list), SSE event broker (Redis streams), execution
quota, and collab room backplane (Redis pub/sub + INCR seq allocation +
compaction lock) are all shared — any replica's worker runs any job, any
replica serves any SSE stream, and WebSocket clients on different replicas
collaborate through the backplane. A stale-job reaper on every instance
marks submissions abandoned by a dead worker (fresh updated_at is the
liveness signal — the worker persists incrementally) as internal_error.
In-memory backends remain the dev default (`QUEUE_BACKEND=memory`).

## Authentication

- Access tokens are short-lived JWTs; a **refresh token** (httpOnly cookie,
  rotated on every use, revocable server-side) keeps sessions alive. The
  frontend auto-refreshes on 401. `POST /auth/logout` revokes.
- Login/register are **rate limited** (per IP + per target email). The
  windows live in memory by default and in Redis when `QUEUE_BACKEND=redis`,
  so they hold across replicas.
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
  [Piston](https://github.com/engineer-man/piston). Needs Docker Desktop running:

  ```powershell
  cd ..\deploy\piston
  docker compose up -d
  # one-time: install language runtimes (persist in a volume)
  curl -X POST http://localhost:2000/api/v2/packages -H "Content-Type: application/json" -d '{\"language\":\"python\",\"version\":\"3.12.0\"}'
  curl -X POST http://localhost:2000/api/v2/packages -H "Content-Type: application/json" -d '{\"language\":\"node\",\"version\":\"20.11.1\"}'
  ```

  Then run the API with `EXECUTION_PROVIDER=piston` (a `.env` with that line
  works). Both compose files set `PISTON_OUTPUT_MAX_SIZE=1048576`: Piston's
  default is 1024 bytes per stdio buffer, which kills any pytest-mode suite
  (one run reports every test) after the first few records. They also raise
  `PISTON_RUN_CPU_TIME` to 15 s (default 3 s of CPU per run, independent of the
  wall timeout) and the executor sends `run_cpu_time` with every request.

  Why Piston and not Judge0: Judge0's isolate needs cgroup v1 and segfaults on modern
  Docker Desktop (cgroup v2). Design decision #5, amended v2.1.

### pytest judge mode

`Problem.judge_mode = "pytest"` problems ship a **provided pytest suite**
(`Problem.harness = {"module": "todo_tracker", "files": {"test_…_p1.py": src}}`)
instead of stdin/stdout cases: the candidate implements the module, Submit
runs the suite inside the sandbox, and every test reports by name with its
assertion on failure. One TestCase per test function (`stdin` =
`file.py::test_name`, expected `PASS`, all samples).
`app/services/execution/pytest_harness.py` holds the runner and a minimal
`pytest` shim (`raises`, `approx`, `fixture`, `mark`); the Piston executor
runs the whole suite in ONE execution (15 s cap, 5 s per test) and fans the
records out as normal `case_result` events, so the worker/checkers are
unchanged. Python only. Drills, the Perplexity set and the Sierra set all
use this mode. `tests/test_pytest_harness.py` runs the runner for real
through a fake Piston, including the full 97-test todo-tracker suite.

Failures read like pytest's: the runner rewrites every `assert` in the suite
files at load time, so a failed comparison reports what it compared instead
of a bare `AssertionError`:

```
AssertionError: assert word_lengths(['hi', 'yo']) == {'hi': 2, 'yo': 2}
  Expected: {'hi': 2, 'yo': 2}
  Actual:   {'hi': 3, 'yo': 3}
  Differences:
    'hi': expected 2, got 3
    'yo': expected 2, got 3
```

`==` shows Expected / Actual plus a short diff (dict keys and values, sequence
length and first differing indexes, set members, first differing character of
a string); other operators show both operands; a bare `assert x` shows the
value. Each operand is evaluated once and the traceback keeps the original
line. `tests/test_assert_rewrite.py`.

### Python prelude (no imports needed)

Every Python run and submission, in every mode, can use the common standard
library names without importing them: `Counter`, `defaultdict`, `deque`,
`heappush`/`heappop`, `bisect_left`, `accumulate`/`pairwise`/`product`,
`reduce`/`lru_cache`/`cache`, `gcd`/`inf`/`ceil`, `List`/`Optional`/…,
`dataclass`/`field`, `itemgetter`, `ascii_lowercase`, `deepcopy`, plus the
modules themselves (`collections`, `itertools`, `math`, `re`, `json`, `random`,
`sys`, …). The list lives in `app/services/execution/python_prelude.py` and is
served by `GET /v1/execution/prelude`; the **Auto-imports** button next to the
editor shows it. Writing the import anyway is fine.

How: a small `solvary_prelude.py` is shipped into the sandbox and its
`install()` copies the names onto `builtins`, so nothing is prepended to the
user's source and traceback line numbers stay right. The pytest runner calls
it before importing the candidate's module; plain scripts now run through a
tiny `main.py` that installs the prelude and executes the code as
`solution.py` / `__main__` (stdin, exit code and a traceback starting at the
user's code are preserved). A name the sandbox's Python lacks is skipped; an
existing builtin is never overwritten. `tests/test_python_prelude.py`.

## Ad-hoc Run

`POST /v1/execution/run` (+ `GET /v1/execution/{run_id}/events` SSE) runs a
buffer against custom stdin without judging. Runs are ephemeral by design
(design §6.5): no table, events live in the broker only, unknown/evicted ids
404. With `workspace_id` the caller must be an editor+ member. The problem
page, drill page, interview page and challenge workspaces all have a
**Run** button next to Submit. With `problem_id` on a pytest-mode problem
the run executes the provided suite instead of the buffer: stdin lists test
ids (one per line, blank = whole suite) and the output is a transcript —
status per test, tracebacks, and anything the code printed, for passing
tests too.

Quota note: `check_execution_quota` reserves a per-user concurrency slot as a
route dependency and releases it if the handler rejects the request — a
rejected submission must never cost a slot (it used to, locking users out
after two 400s).

## Submissions and past code

Every submission stores the code it was judged with. `GET /v1/submissions`
lists yours (`?problem_id=` / `?workspace_id=` filters) without code;
`GET /v1/submissions/{id}` returns it with the code; `GET …/{id}/events`
streams the verdict (replay-then-follow). In the UI, every row under *My
submissions* on a problem page expands to its code with **Load into
editor**, and the interview review page shows each part's attempts with a
picker (see [Mock interviews](#mock-interviews)).

Timestamps are serialized as UTC (`…Z`); SQLite hands back naive datetimes,
and the response schemas attach the zone so browsers do not read them as
local time.

## AI assistant

`POST /v1/assist/explain` streams a tutoring reply over SSE
(`{"content": …}` chunks, then `{"done": true}`) from the problem statement,
sample tests, the user's current code and their latest verdict. Hidden test
cases are never sent to the model. Rate limited to 20 questions/min per user.
Refused while a mock interview session is active.

Provider via `LLM_PROVIDER`:

- **`mock`** (default) — canned streamed reply, no network.
- **`openai`** — any OpenAI-compatible `/chat/completions` server (vLLM, Ollama,
  a cloud API, or a self-hosted model). Point `LLM_BASE_URL` / `LLM_API_KEY` /
  `LLM_MODEL` at it, e.g. `LLM_PROVIDER=openai LLM_BASE_URL=http://localhost:8001/v1 LLM_MODEL=my-model`.

The **Ask AI** tab on the problem page and the drill page, and **Ask AI
about this part** on the interview review page, are the UI.

## Drills

Quick Python exercises (`/drills` in the UI): 62 two-minute problems in 14
topics. Eight are language idioms (comprehensions, strings, dicts &
collections, sorting, iteration, slicing & unpacking, generators & itertools,
pythonic patterns); six are interview building blocks meant to be typed
without thinking so the attention goes to design and explanation (hash-map
idioms, stacks & queues, loops & exit conditions, two pointers & windows,
graph skeletons, recursion & backtracking). Solve one, and the idiomatic solution opens with notes on why it is written
that way; the habits come from the comparison. The solution can also be
revealed early. The list page tracks progress per topic and **Continue**
jumps to the first unsolved drill; inside a drill, **Next drill** goes to the
next unsolved one and Ctrl+Enter submits.

Each drill is a private pytest-mode `Problem` tagged `drill`, `topic:<slug>`,
`order:<nn>` (out of the catalogue and the stats pool). `GET /v1/drills`
groups them by topic with the user's progress (solved / attempts, derived
from submissions) and `GET /v1/drills/{slug}` adds the editorial and
prev/next navigation; judging is the ordinary submission pipeline. Content
lives in `content/drills/<topic>/<slug>/` (`PROBLEM.md` whose first line is
the title, `<module>.py` stub, `reference.py`, `test_<module>.py`,
`NOTES.md`) with a per-topic `ORDER` file; topics are described in
`app/services/drill_service.py`. Where possible the suites enforce the idiom
behaviourally (laziness via generators that fail if read too far, `is True`,
non-mutation, a plain `dict`, `FrozenInstanceError`; for the algorithm
drills, inputs sized so only the linear or logarithmic solution finishes,
chains longer than the recursion limit, and counted callbacks).
`tests/test_drills_content.py` keeps every reference green and every stub
red; `tests/test_drills.py` covers the API.

```powershell
.venv\Scripts\python -m scripts.seed_drills             # seed the drills (skips existing)
.venv\Scripts\python -m scripts.seed_drills --refresh   # update statements, notes, stubs, tests in place
```

## Mock interviews

Timed, staged practice runs (design: [`../SOLVARY_INTERVIEWS_DESIGN.md`](../SOLVARY_INTERVIEWS_DESIGN.md)).
A **template** is an ordered list of stages, each stage is a `Problem`; a
**session** is one user's run through it with a **server-authoritative clock**
(`started_at` / `ends_at` / `server_time` on every response, lazy expiry, 3 s
grace on submissions). Two formats: `levels` (one evolving buffer, parts
unlocked sequentially, cumulative tests authored into later levels) and
`questions` (independent problems, free navigation). The duration can be
overridden per session (15–180 min; stage budgets scale). Code lives in a
workspace of `kind="interview"` (hidden from `/v1/workspaces`, fixed file set),
results are derived from submissions tagged `interview_session_id`, and AI
assist is refused while a session is active (allowed on the review page via
`interview_session_id`). Stage problems are seeded `is_public=False`, so the
session payload is their only reader — locked stages are served as stubs.

Endpoints under `/v1/interviews`: `GET templates`, `POST templates` (admin),
`POST sessions`, `GET sessions`, `GET sessions/active`, `GET sessions/{id}`,
`POST …/advance|switch|finish|abandon`, `GET …/review`. Pacing coach:
per-stage budgets, nudges, strict mode (`pacing="strict"` → hard per-stage
deadlines), a planned-vs-actual timeline and a one-line diagnosis on review,
plus the **Clock Beater** and **Pacer** badges.

The review page shows every part's statement and editorial, **Your code**
with a picker across that part's attempts (default: the latest accepted),
clickable rows in the submissions list, and a **Final code** button that
opens the session's workspace as you left it.

Practice sets (all pytest mode, seeded private):

```powershell
.venv\Scripts\python -m scripts.seed_interviews   # kv-store-levels (90 min, 4 levels) + warmup-questions (60 min)
.venv\Scripts\python -m scripts.seed_perplexity   # Perplexity coding-screen set: six multi-part levels + a tier-2 questions set
.venv\Scripts\python -m scripts.seed_sierra       # Sierra phone-screen set (8 x 3 parts, 25–30 min)
.venv\Scripts\python -m scripts.seed_sierra --refresh   # re-read content/sierra_prep: update statements, editorials, stubs in place
.venv\Scripts\python -m scripts.seed_ai_prep      # AI-company set: 5 multi-part problems (2 CodeSignal-style 90-min 4-level, 3 live screens)
.venv\Scripts\python -m scripts.seed_ai_prep --refresh
```

The AI-company set (`content/ai_prep/`, report in
[`../reports/AI company coding interview problems.md`](../reports/AI%20company%20coding%20interview%20problems.md))
reconstructs the most-reported multi-part problems of Nov 2025 – Nov 2026:
`memory_db` and `bank_system` are CodeSignal Industry Coding Assessment
shapes (Anthropic, OpenAI, Coinbase, Meta, Airbnb: 90 min, four levels,
level 3 is where time enters), `grid_infection` is OpenAI's five-part
simulation, `recipe_cart` Decagon's discounts → versions → nested transactions
screen, `rate_limiter` Snowflake's tiers → runtime updates → injected clock →
compound rules and a shared store. `tests/test_ai_prep_content.py` checks
every reference is green, every stub red, and every folder matches its `Spec`.

Content lives in `content/perplexity_prep/<problem>/` and
`content/sierra_prep/<problem>/` (`PARTn.md`, stub, `test_*_pn.py`,
`reference.py`). The Sierra set is reconstructed from candidate reports
(sources and confidence per problem in
[`../reports/Sierra coding interview problems.md`](../reports/Sierra%20coding%20interview%20problems.md));
its statements are written for solo practice with a *Clarifications*
section answering what you would ask the interviewer, and a
`---\nInterviewer notes` footer that the seeder moves into the editorial.
The seeders skip templates that already exist; after editing a `PARTn.md`,
stub or reference under `content/sierra_prep/`, run `seed_sierra --refresh`
(statement, editorial, starter code, and the harness when the test ids are
unchanged; sessions and test cases are untouched).
`tests/test_sierra_content.py` checks every reference is green and every
stub is red.

## Interviewer agent

An AI interviewer sits in a third, resizable pane of the interview page
(design: [`../SOLVARY_INTERVIEWER_DESIGN.md`](../SOLVARY_INTERVIEWER_DESIGN.md)).
It runs on the **user's own Anthropic API key** — pasted once in the
*Interviewer* card on the interviews page, stored Fernet-encrypted
(`app/core/secrets.py`, key derived from `SECRET_KEY`), never returned by any
endpoint — or on `ANTHROPIC_API_KEY` as a server-wide fallback. Model and
effort are config (`INTERVIEWER_MODEL=claude-sonnet-5-5`,
`INTERVIEWER_EFFORT=low`); `INTERVIEWER_PROVIDER=fake` scripts replies for tests.

Every **turn** is one streamed Claude request assembled server-side
(`app/services/interviewer_service.py` + `interviewer_prompt.py`): a static
persona, the whole template (every part's statement, provided tests,
interviewer notes and — unless `INTERVIEWER_KNOWS_SOLUTIONS=false` — the
reference solution, all marked never-reveal; this block carries the prompt-cache
breakpoint), the stored transcript as history (earlier turns as a one-line
digest, never old code), and the newest turn: the server's truth (clock, part,
budget, results) plus the **screen** the page sends (the editor buffer, the
latest judge result with failing test names and tracebacks, the latest Run
output, which pane is open, seconds since the last edit, mic mode). Turns are
triggered by speech, typing, or page events (session start, verdict, a Run
crash, part change, budget exceeded, `INTERVIEWER_IDLE_S` of silence); the
model answers `[silent]` when an interviewer would not speak, and the pane
hides those. Transcripts persist in `interviewer_turns` (migration
`b7e4d2c9a1f0`) and show on the review page.

Microphone input is the browser's Web Speech API (Chrome/Edge): *Open* mic
sends what you said once you pause for 1.2 s, *Push* sends on release
(`Ctrl+Shift+Space`; `Ctrl+Shift+M` toggles the mic). An optional voice reads
replies aloud and the mic is muted while it speaks, so the agent never hears
itself. Ask AI stays disabled during a session.

Endpoints: `GET|PUT|DELETE /users/me/ai-key`, `POST /users/me/ai-key/test`
(5/min); `GET|POST|DELETE /v1/interviews/sessions/{id}/interviewer/turns`
(POST streams SSE `{"content"}`* then `{"done", "spoke", …}`; 402 `NO_API_KEY`
without a key, 409 when the session is over or a turn is in flight, 40/min).

## Home: stats and accolades

`GET /v1/stats/me` powers the home page: totals (solved, submissions,
acceptance rate), breakdowns by difficulty and language, current and
longest streaks, a year activity heatmap, recent submissions, and badges
(First Blood, One Shot, Hat Trick, Week Warrior, Polyglot, Sharpshooter,
Century, Comeback Kid, Night Owl, Speed Demon, Pair Programmer, Better
Together, plus the interview badges). Only public problems count toward
solved totals; drills and interview stages do not.

## Collaborative workspaces (M3)

Live multi-user editing via Yjs CRDTs. The server speaks real y-protocol over
`WS /ws/workspaces/{id}` (JWT rides the subprotocol), relays updates, persists
snapshot + update log, and enforces owner/editor/viewer RBAC — viewers get a
readOnly editor and the server drops (and resyncs) any doc update they send.
File metadata is REST-authoritative; content is CRDT-only, keyed by file id.
Try it: two browsers, same workspace, `/workspaces` — live cursors included.
Awareness updates are echoed to their sender on purpose: a solo editor's
15 s renewals are the only inbound traffic that keeps y-websocket from
reconnecting every 30 s.

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
Content suites (`test_pytest_harness.py`, `test_sierra_content.py`,
`test_drills_content.py`) run every reference and stub through the harness
with a fake Piston that executes the local interpreter.

To run the suite against Postgres (what CI does):

```powershell
docker run -d --name solvary-pg -e POSTGRES_USER=solvary -e POSTGRES_PASSWORD=solvary -e POSTGRES_DB=solvary_test -p 5433:5432 postgres:16
$env:TEST_DATABASE_URL = "postgresql+asyncpg://solvary:solvary@localhost:5433/solvary_test"
.venv\Scripts\python -m pytest -q
```

Frontend: `npm run lint` and `npm run build` (typecheck + Vite build) in
`../solvary_react`.

## CI

`.github/workflows/ci.yml` runs on every push/PR: backend ruff + pytest on
SQLite, the full suite plus the Alembic migration chain on Postgres 16,
frontend eslint + build, and both Docker image builds.
