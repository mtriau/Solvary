# Solvary — Design Document (v2.2)

A LeetCode-style coding-challenge platform that also supports **live multi-person
collaborative workspaces**. Built as a new backend + frontend that reuses MattChat's
architecture, conventions, and swap-a-provider idioms.

Status: **design locked, pre-implementation.** This doc is the contract we build against.

## Changelog

**v2.4 (2026-11-04)** — **pytest judge mode** (`Problem.judge_mode = "pytest"`, `Problem.harness = {module, files}`; migration `9d2f4b7c1e55`). A problem ships a provided pytest suite; one TestCase per test function (`stdin` = test id, expected `PASS`), every case a sample. The executor runs the whole suite in ONE sandbox execution (`app/services/execution/pytest_harness.py`: runner + a minimal `pytest` shim, since the sandbox has no pytest) and fans the records out as ordinary `case_result` events — the worker and checkers are untouched. Python-only (submissions in other languages → 400). Seed content: `scripts/seed_perplexity.py` + `content/perplexity_prep/` (six multi-part Perplexity-style screens as `levels` interviews gated `on_accept`, four tier-2 problems public + a `questions` interview). **v2.4.1 (2026-11-05):** `scripts/seed_sierra.py` + `content/sierra_prep/` — seven three-part Sierra phone-screen reconstructions (25–30 min `levels` interviews, `on_accept`), built with the same `Spec`/`build_parts` helpers; sources and confidence per problem in `reports/Sierra coding interview problems.md`; `tests/test_sierra_content.py` keeps every reference green and every stub red. **v2.4.2 (2026-11-05):** ad-hoc Run on pytest-mode problems (`RunRequest.problem_id`) runs the provided suite — stdin = test ids, blank = all — and returns one transcript with printed output for every test (`pytest_harness.format_run_output`, `PistonExecutor._execute_pytest_run`); the Run panel relabels itself in that mode. Found while verifying on real Piston: its 1 KiB per-stdio default (`PISTON_OUTPUT_MAX_SIZE`) truncated every pytest-mode run after ~5 records — both compose files now set 1 MiB, and raise `PISTON_RUN_CPU_TIME` to 15 s (the executor now sends `run_cpu_time` = the time limit; Piston's separate 3 s CPU default was killing suites with one busy loop).  **Collab keepalive fix:** awareness updates are now echoed to their sender (as the reference y-websocket server does) — excluding the sender left a solo editor with zero inbound traffic, so y-websocket's 30 s silence check closed and reopened the socket about once a minute, flipping `synced` and remounting Monaco (page blink, cursor to line 1). **v2.4.3 (2026-11-09):** every Sierra statement (`content/sierra_prep/*/PARTn.md`) rewritten for solo practice — fixed sections *What you are given / What to implement / Rules / Worked example / Clarifications*, the last answering the questions a candidate would ask the interviewer, each answer checked against the provided tests (one real ambiguity fixed on the way: merch-catalog "catalog order" meant the item's own `related` list order). `scripts/seed_sierra.py --refresh` updates seeded problems in place (statement, editorial, stub; harness only when the test ids are unchanged). **v2.4.4 (2026-11-09):** past code is viewable in the UI. `SubmissionCode` (read-only Monaco, lazy `GET /v1/submissions/{id}`, copy button) sits under every part on the interview review page with a picker across that part's attempts (default: latest accepted, else latest); the Submissions list rows jump to the attempt; the shown code feeds the part's AI review; a **Final code** button opens the session's interview workspace (`/workspaces/{id}` — the buffer as left at the end). On the problem page every row of *My submissions* expands to its code with **Load into editor**. Fixed on the way: `SubmissionResponse.created_at` / `WorkspaceResponse.created_at` were naive datetimes from SQLite, serialized without `Z`, so browsers parsed them as local time and interview offsets showed hours off — both schemas now coerce to UTC; statement code blocks (`[&_pre]`) had no text colour override and rendered near-invisible on the light background. **v2.5 (2026-11-10) — Drills.** A fourth mode next to Problems / Workspaces / Interviews: very small Python exercises that each practise one idiom, for building habits by comparison. No new tables: a drill is a pytest-mode `Problem` with tags `drill`, `topic:<slug>`, `order:<nn>`, seeded `is_public=False` (out of the catalogue and the stats pool). `app/services/drill_service.py` (TOPICS table, grouping, per-user solved/attempts from submissions, prev/next/next-unsolved) behind `GET /v1/drills` and `GET /v1/drills/{slug}` (`app/schemas/drills.py`); the editorial (NOTES.md + reference) is always in the payload and gated client-side until the suite is green or the user reveals it. Content: `content/drills/<topic>/<slug>/` + `ORDER`, 32 drills in 8 topics, `scripts/seed_drills.py [--refresh]`, `tests/test_drills_content.py` (every reference green, every stub red through the fake-Piston harness), `tests/test_drills.py` (API). Frontend: `pages/drills/DrillsPage` (topics, progress, Continue → first unsolved) and `DrillPage` (statement · hidden idiomatic solution · provided tests | Monaco, Ctrl+Enter submits, Tests/Run/Ask AI panels, topic dots, Next drill → next unsolved). Several suites enforce the idiom behaviourally (laziness via exploding generators, `is True`, immutability, `KeyError` on a plain dict) since style itself cannot be judged. **v2.5.1 (2026-11-10) — Python prelude.** Common stdlib names are available in every Python run and submission without an import (LeetCode convention): `app/services/execution/python_prelude.py` defines the module → names table and ships a `solvary_prelude.py` into the sandbox whose `install()` copies them onto `builtins` (nothing is prepended to the source, so traceback line numbers hold; missing names are skipped, real builtins never overwritten). The pytest runner installs it before importing the candidate module; plain scripts now run via a small `main.py` runner that installs it and executes the code as `solution.py`/`__main__`, preserving stdin, exit code and a traceback that starts in the user's file (runner frame dropped, `SyntaxError` reported against `solution.py`). JavaScript is untouched. `GET /v1/execution/prelude` (public, static) describes the list; the **Auto-imports** popover (`features/execution/components/PreludeHint`) sits in the problem, drill and interview editor toolbars. `tests/test_python_prelude.py` runs scripts and a pytest module through the fake Piston. **v2.5.2 (2026-11-10) — assertion rewriting.** The pytest runner now rewrites every `assert` in the suite files at load time (`_AssertRewriter` in `pytest_harness.RUNNER`: operands evaluated once into temporaries, then `raise _sv_fail(...)` on the original line), so failures report `Expected:` / `Actual:` for `==` with a short diff (dicts, sequences, sets, strings, type mismatch), both operands for other operators, operand list for chained comparisons, and the value for bare `assert x` / `assert not x`; custom messages come first; `pytest.approx` gets no diff. Reprs via `pprint`, capped at 1200 chars. `tests/test_assert_rewrite.py`. **v2.5.3 (2026-11-11) — algorithm-skeleton drills.** Six new drill topics (30 drills, 62 total) appended to `drill_service.TOPICS` without touching the original eight: `hashing` (dict.fromkeys dedupe, one-pass two-sum, canonical-key grouping, next-with-default, prefix-sum counting), `stacks-queues` (bracket matching, monotonic stack, dispatch-dict RPN, `deque(maxlen)`, path stack), `loops` (divmod digit loop, tuple-assignment Euclid, two-argument `iter`, bounded `for`/`return`/`raise`, half-open binary search), `pointers` (write index, normalise-then-compare palindrome, converging pointers, last-seen-index window, grow-and-shrink window), `graphs` (`defaultdict(set)` adjacency, BFS mark-on-enqueue, iterative DFS components, Kahn's order, directed-cycle detection), `recursion` (`functools.cache`, choose/explore/un-choose subsets, path-carrying flatten, `max(..., default=)` depth, pruned parentheses). Enforcement is behavioural: 60k to 400k-element inputs that only the intended complexity finishes, a counting `Sequence` that caps binary-search reads at 25, 4,000 to 5,000-node chains that overflow recursion, exact callback counts for sentinel and fixed-point loops. Notes name the invariant and exit condition for every loop. Content-only change plus the TOPICS table; `test_drills_content.py` unchanged and green. **v2.5.4 (2026-11-11):** eighth Sierra template `sierra-event-streams` (`content/sierra_prep/event_streams/`, 30 min, tags heap/streams/generators), the heap problem the set lacked, hooked to report item S6 ("merging multiple streams", Feb 2026 screen): Part 1 merges time-ordered event lists (concat-and-sort accepted), Part 2 makes the sources live iterators with lazy, one-head-per-stream bounded look-ahead (2,000 streams x 100 events rejects a linear scan of heads by time; counting iterators check the look-ahead), Part 3 adds `deliver_at` with a second heap released once the input `ts` reaches the due time (ties by arrival; look-ahead and 100k random deferrals checked). Keyboard Part 3 statement now says what `home()`/`end()` do. `test_sierra_content.py` green at 8 folders.

**v2.3 (2026-11-04)** — **Mock interview mode** (addendum:
[`SOLVARY_INTERVIEWS_DESIGN.md`](SOLVARY_INTERVIEWS_DESIGN.md), implemented). New
entities `InterviewTemplate`/`InterviewStage`/`InterviewSession` (`itpl_`/`istg_`/`isess_`),
`Submission.interview_session_id`, `Workspace.kind`; `/v1/interviews/*` API; config
`interview_grace_s`; feature slice `interviews`. Locked: a stage **is** a Problem; one
workspace per session; server-authoritative clock with lazy expiry; results derived
from tagged submissions; no AI assist during a session. "Timed contests" in the
phase-2 list is partially subsumed (solo timed mode landed; leaderboards remain deferred).

**Naming (2026-07-13)** — the project is now **Solvary** (solve + -ary, "a place where solving happens"). The working name CodeArena collided with several existing products. Directories: `solvary_backend/` + `solvary_react/`; seeded accounts moved to `@solvary.dev`.

**v2.2 (2026-07-13)** — M3 implementation amendments. (1) The file-listing-changed
extension frame is message type **127**, not 0x03 as v2 specified — type 3 is
y-websocket's queryAwareness, inside the protocol tag space the design meant to avoid
(all references below updated). (2) Empty Yjs updates (`b"\x00\x00"`) are no-ops for
every role: the y-protocol handshake has every client answer step1 with a step2 reply,
and a fresh viewer's empty reply must not trigger the drop+resync path (it ping-pongs
forever) nor be persisted for editors. (3) WS auth-failure closes are accept-then-close
so the 4401/4403 codes actually reach the client (close-before-accept degrades to a
bare HTTP 403 handshake rejection).

**v2.1 (2026-07-10)** — decision #5 amended during M2: **Piston replaces Judge0** as the
real execution provider. Empirical grounds: Judge0 1.13.1's sandbox (isolate) requires
cgroup v1 and segfaults on this dev machine's Docker Desktop (cgroup v2, v1 fallback
removed); verified directly with `isolate --run` in the official image. Piston requires
cgroup v2 — matching the environment — and its API (raw stdout/time/memory per run,
no built-in output comparison) actually fits our worker-side-checker architecture
better. Judge0 remains a valid deploy-time alternative on cgroup-v1 hosts behind the
same `BaseExecutor` interface. Config: `judge0_*` keys replaced by `piston_base_url`.

**v2 (2026-07-10)** — revised after design review. Load-bearing decisions unchanged
(CRDT/Yjs, sandbox-behind-`BaseExecutor`, SSE transport, workspace-unifies-everything,
milestone ladder). Fixes cluster at the CRDT↔REST seams and the streamed↔durable gap:

- **Files:** killed the dual source of truth. File metadata is REST-authoritative;
  the CRDT holds content only, keyed by **file id** (not path) so rename preserves
  identity. New `127` file-listing-changed frame.
- **Doc birth:** adopted `pycrdt` server-side (M3) for initial snapshot + compaction —
  first-client-seeds had a duplication race in pair-interview creation.
- **SSE:** judge event streams are now **replay-then-follow**; the worker persists
  per-case results incrementally. Fixes the POST→subscribe race and gives reconnect.
- **Admin:** added `role` to User + `require_admin` dependency (was referenced, never
  defined).
- **Viewers:** read-only enforced client-side (`readOnly` editor) + server drop **+
  snapshot resync on drop** — silent drops forked the viewer's local doc.
- **Pagination:** new repos use tie-safe keyset pagination `(created_at, id)` — a
  deliberate deviation from MattChat's strictly-`created_at >` cursor, which skips
  timestamp ties.
- **Worker:** deconflated worker vs. executor — the **executor is the isolation
  boundary**; the worker runs in-process (async tasks) for M1–M2.
- **Endpoints:** merged `POST /workspaces/{id}/run` into `POST /execution/run`
  (optional `workspace_id`).
- **Visibility:** cut `public/unlisted` from MVP — it was decorative (content lives in
  the member-gated CRDT doc).
- **Checkers:** replaced free-form `checker_ref` (an RCE vector under third-party
  authoring) with a fixed checker enum.
- **Protocol:** committed to speaking real y-protocol (sync + awareness), not a
  half-compatible custom framing. WS auth via subprotocol only (no query-string tokens).
- Added: `DocUpdate` table, testing section, verdict = first-failing-test semantics,
  rate-limit locus, ad-hoc-run ephemerality made explicit, per-case events marked
  best-effort.

---

## 1. Guiding principles

1. **One core abstraction — the collaborative Workspace.** A challenge attempt is a
   workspace with a bound Problem + hidden tests, where "Run" becomes "Judge." A pair
   interview is a challenge attempt with >1 member. We do **not** build two disjoint apps.
2. **Reuse MattChat's spine verbatim.** Layered `routes → dependencies (DI) → services →
   repositories → models`, `@dataclass` domain models, ABC repository with Mock +
   SQLAlchemy implementations swapped by `use_mock_db`, `PaginatedResponse[T]`,
   prefixed-slug IDs, provider factory chosen by a config string, SSE via
   `StreamingResponse`, JWT auth via `get_current_user`. (One deliberate deviation:
   pagination — see §3.3.)
3. **Untrusted user code never runs in the API process.** The **executor** is the
   isolation boundary: with Piston, code runs inside Piston's sandbox and the worker is
   just an HTTP client that may safely live in-process. A separate worker *process* is
   only required if we ever build a DIY-Docker executor.
4. **The two new subsystems (realtime collab, code execution) hide behind clean
   interfaces** so they can swap implementations (in-memory ↔ Redis, Mock ↔ Piston) and
   can't destabilize the CRUD core.
5. **The CRDT holds document *content* only.** Everything the server must authorize,
   list, or query — file metadata, membership, verdicts — is REST/DB-authoritative.
   CRDT↔REST seams are design, not implementation detail.

---

## 2. Locked decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Collaboration model | **CRDT (Yjs)** | Auto-converges, tolerates reconnect, first-class editor bindings + awareness. OT needs a bespoke transform server. |
| 2 | Collab backend | **FastAPI WebSocket speaking real y-protocol** (sync + awareness), relaying opaque updates | Stays in the Python stack; the stock `y-websocket` client provider works unmodified. Half-compatible custom framing is the worst spot. Hocuspocus deferred. |
| 3 | Doc granularity | **One Yjs doc per workspace**: `Y.Map<file_id, Y.Text>` | One room, atomic presence. Keyed by **file id**, not path — rename preserves content identity and concurrent-edit safety. File create/rename/delete go through REST (§7.1), not CRDT map ops. |
| 4 | WS scaling | **Interface with `InMemoryBackplane` (MVP) + `RedisBackplane`** | Mirrors `use_mock_db` swap. Single instance ships first. |
| 5 | Sandbox | **`MockExecutor` (dev) + `PistonExecutor` (real)** behind `BaseExecutor` *(amended v2.1)* | Piston: multi-language, resource-capped, cgroup-v2-native (Judge0's isolate needs cgroup v1 — segfaults on modern Docker Desktop). Returns raw stdout, which fits our worker-side checkers. Judge0/DIY Docker/Firecracker remain alternatives behind the same interface. |
| 6 | Execution flow | **Async job queue + workers**; in-process async tasks for M1–M2 | Decouples expensive work from the request thread; enables streaming progress. Isolation comes from the executor (§1.3), not the worker's process boundary. |
| 7 | Judge protocol | **stdin/stdout + built-in checker enum first**, evolve to function-signature drivers | Language-agnostic, robust, easy to author. Free-form checker code is an RCE vector under third-party authoring — deferred until checkers run sandboxed. |
| 8 | Result transport | **SSE, replay-then-follow** | Reuses MattChat's `StreamingResponse` + fetch-streaming pattern; replay fixes the subscribe-after-fire race and gives reconnect for free. |
| 9 | Editor | **Monaco + `y-monaco`** | VS Code core; crowd-pleaser for a coding platform. CodeMirror is the fallback. |
| 10 | Launch languages | **Python + JavaScript** MVP; add C++/Java after | Two runtimes to harden first; more is a runtime package install in Piston. |
| 11 | AuthZ | **JWT (reused) + `User.role` admin flag + Workspace RBAC** (`owner`/`editor`/`viewer`) | Membership/role authorization MattChat skipped, plus the admin concept problem authoring requires. |
| 12 | AI tie-in | **Reuse `matt_llm/serve.py`** as hint/explain/review assistant | "Explain this problem," "Why did test 3 fail?" — reuses `BaseLLMService` + SSE. |
| 13 | Server-side CRDT | **`pycrdt`, adopted at M3**, used narrowly | Required for doc birth (seeding starter code without a first-client race) and snapshot compaction. "Client sends buffer" remains the Run path only. |

**Cut from MVP:** workspace `visibility` (public/unlisted) — content lives in the
member-gated CRDT doc, so "public" was decorative. Revisit with a proper sharing story
(read-only REST content endpoint) in phase 2.

**Deferred to phase 2+:** timed contests + live leaderboards, Elo ratings, interactive
PTY/terminal over WS (stdin programs), workspace chat, discussions/editorials, doc
time-travel/history, sandboxed custom checkers, function-signature judging, language
switching mid-attempt (§4 Workspace note).

---

## 3. Backend

### 3.1 New config (extends `Settings`)

```python
# execution
execution_provider: str = "mock"          # "mock" | "piston"
piston_base_url: str = "http://localhost:2000"
execution_max_code_bytes: int = 64_000
execution_default_time_limit_s: float = 5.0
execution_default_memory_kb: int = 256_000
execution_user_concurrency: int = 2       # concurrent jobs per user
execution_user_rate_per_min: int = 30

# realtime collaboration
realtime_backplane: str = "memory"        # "memory" | "redis"
redis_url: str = "redis://localhost:6379/0"
ws_snapshot_interval_updates: int = 200   # compact snapshot every N updates
ws_max_message_bytes: int = 1_000_000
```

Rate limiting is enforced in a FastAPI dependency (`check_execution_quota`) backed by an
in-memory counter for MVP. Known limitation: resets on restart and is wrong under
multi-instance — the counter moves behind the backplane interface when Redis lands.

### 3.2 Module layout (adds to the existing tree)

```
app/
  models/        problem.py testcase.py submission.py workspace.py
                 workspace_member.py workspace_file.py doc_snapshot.py doc_update.py
  schemas/       problems.py submissions.py workspaces.py execution.py
  repositories/  *_repository.py (+ mock_ / sqlalchemy_ pair each, per existing pattern)
  services/
     problem_service.py
     submission_service.py         # create submission → enqueue → stream verdicts
     workspace_service.py          # CRUD + membership + RBAC + file metadata
     execution/
        base.py                    # BaseExecutor, ExecJob, ExecEvent, Verdict
        checkers.py                # built-in checker enum implementations
        mock_executor.py
        piston_executor.py
        factory.py                 # create_executor(settings)
     collaboration/
        manager.py                 # CollaborationManager (rooms, relay, persistence)
        doc_store.py               # pycrdt: doc birth, snapshot compaction (M3)
        backplane.py               # BaseBackplane
        memory_backplane.py
        redis_backplane.py
     queue/
        job_queue.py               # BaseJobQueue + InMemory + Redis impls
        worker.py                  # judge worker loop — async task in-process for
                                   # M1–M2; shaped to run standalone if a local
                                   # (non-Piston) executor ever exists
  api/v1/
     routes_problems.py routes_submissions.py routes_workspaces.py
     routes_execution.py           # POST run + SSE event streams
     ws_collaboration.py           # WebSocket /ws/workspaces/{id}
```

### 3.3 Conventions inherited (do not reinvent)

- **IDs:** `f"{prefix}_{uuid.uuid4().hex[:8]}"`. Prefixes: `prob_`, `tc_`, `sub_`,
  `ws_`, `wsm_`, `wsf_`, `snap_`, `upd_`. Ad-hoc runs use `run_` but are **ephemeral**
  (in-memory only, no table — §6.5).
- **Domain models:** plain `@dataclass`, `created_at`/`updated_at` via
  `field(default_factory=lambda: datetime.now(timezone.utc))`.
- **Repositories:** `AbstractRepository[T]` ABC → `Mock*Repository` (in-memory list) +
  `SQLAlchemy*Repository`, chosen in `dependencies.py` by `settings.use_mock_db`.
- **Errors:** the existing `app/core/exceptions.py` hierarchy + handlers.
- **Pagination — deliberate deviation:** MattChat's SQLAlchemy cursor filters strictly
  `created_at > cursor.created_at`
  ([sqlalchemy_message_repository.py:26-29](matt_chat_backend/app/repositories/sqlalchemy_message_repository.py#L26-L29)),
  which **skips rows sharing the cursor's timestamp**. Ties are rare for chat messages
  but constant for burst-inserted rows (judge writing N case results, seed scripts).
  New repos use tie-safe keyset pagination: `ORDER BY (created_at, id)`, filter
  `(created_at, id) > (cursor.created_at, cursor.id)`. Response shape
  (`PaginatedResponse[T]`, opaque id cursor) is unchanged.
- **Auth additions (M0):** `role: Literal["user", "admin"] = "user"` on User (one
  Alembic column) + a `require_admin` dependency alongside `get_current_user`.

---

## 4. Data model

Domain `@dataclass` shown; the SQLAlchemy `*Row` mirrors it 1:1 with the noted
columns/indexes/FKs (all FKs `ON DELETE CASCADE` unless stated).

### User (modified) — `user_`
Existing MattChat model + `role: Literal["user", "admin"] = "user"`, **minus** the chat
`status` presence field (in Solvary, presence lives in Yjs awareness, not on the user
row). Problem authoring and testcase management require `admin`.

### Problem — `prob_`
```
id, slug (unique), title, difficulty: Literal["easy","medium","hard"],
statement_md, tags: list[str], starter_code: dict[lang,str],
function_signature: str | None, judge_mode: Literal["stdio","signature"] = "stdio",
time_limit_s: float, memory_kb: int, editorial_md: str | None,
is_public: bool = True, created_by (FK user), created_at, updated_at
```
Indexes: `slug` unique, `difficulty`, JSON/assoc table on `tags`.

### TestCase — `tc_`  (belongs to Problem)
```
id, problem_id (FK), ordinal: int, stdin: str, expected_stdout: str,
checker: Literal["exact","float_tolerance","unordered_lines"] = "exact",
checker_args: dict = {}            # e.g. {"epsilon": 1e-6}
is_sample: bool = False,           # sample = visible to user
weight: int = 1, time_limit_s: float | None, memory_kb: int | None
```
Index: `(problem_id, ordinal)`. Hidden cases (`is_sample=False`) never serialized to
non-admin clients. Checkers are a **fixed enum** implemented in
`services/execution/checkers.py` — free-form checker code is deferred until it can run
inside the sandbox (phase 2), because under third-party problem authoring it is
arbitrary code execution in our tier.

### Submission — `sub_`
```
id, user_id (FK), problem_id (FK), workspace_id (FK, nullable),
language: str, code: str,
verdict: Literal["queued","running","accepted","wrong_answer","tle","mle",
                 "runtime_error","compile_error","internal_error"] = "queued",
runtime_ms: int | None, memory_kb: int | None,
passed: int = 0, total: int = 0,
test_results: list[dict] = [],     # per-test {ordinal, status, runtime_ms, memory_kb}
created_at, updated_at
```
Indexes: `(user_id, created_at)`, `(problem_id, verdict)`.
**The worker updates this row incrementally** — verdict → `running`, then a
`test_results` append per completed case — not only at job end. This is what makes the
SSE replay contract (§6.4) possible.

### Workspace — `ws_`
```
id, name, owner_id (FK user), language: str,
problem_id (FK, nullable),    # set → this workspace is a challenge attempt
created_at, updated_at
```
Index: `owner_id`. No `visibility` in MVP (see §2 cuts).
Known limitation: one `language` per workspace forecloses LeetCode's mid-attempt
language dropdown; deferred, revisit with function-signature judging.

### WorkspaceMember — `wsm_`
```
id, workspace_id (FK), user_id (FK),
role: Literal["owner","editor","viewer"], created_at
```
Unique: `(workspace_id, user_id)`. This table **is** the RBAC source of truth.

### WorkspaceFile — `wsf_`  (server-authoritative metadata; content lives in the CRDT)
```
id, workspace_id (FK), path: str, language: str | None,
created_at, updated_at
```
Unique: `(workspace_id, path)`.
**Single-authority rule (v2):** file existence, path, and language are owned by this
table and mutated **only** via REST. The Yjs doc's `Y.Map` is keyed by this row's `id`
and holds only the `Y.Text` content. Rename = REST `PATCH` (metadata-only; CRDT content
identity untouched). After any file mutation the server broadcasts a `127`
file-listing-changed frame (§7.2) so clients refetch. Clients never create/delete Y.Map
keys except in response to REST-confirmed mutations; the server ignores content updates
for unknown file ids.

### DocSnapshot — `snap_`  (compacted binary CRDT state)
```
id, workspace_id (FK), state: bytes, update_seq: int, created_at
```
Index: `(workspace_id, created_at desc)`. Created at workspace birth by `doc_store`
(pycrdt) — for challenge attempts, seeded with the problem's starter code. **Server-side
seeding is mandatory**: first-client-seeds has a duplication race (two simultaneous
joiners each insert starter code; CRDT merge concatenates, it does not dedupe).

### DocUpdate — `upd_`  (append log of updates since the last snapshot)
```
id, workspace_id (FK), seq: int, payload: bytes, created_at
```
Unique: `(workspace_id, seq)`. On join: client receives latest snapshot + all
`DocUpdate`s after its `update_seq`. Every `ws_snapshot_interval_updates` updates,
`doc_store` folds the log into a new snapshot and deletes folded rows. Under the Redis
backplane, **any instance may persist and compact** — Yjs updates are commutative and
merges idempotent, so no single-writer election is needed; that property is the entire
reason the multi-instance story is simple.

---

## 5. REST + SSE API

All under `settings.api_prefix` (`/api`). Auth = `Depends(get_current_user)` unless
noted. List endpoints take `?cursor=&limit=` and return `PaginatedResponse[T]`.
SSE endpoints are consumed via **fetch-streaming with an `Authorization` header** (the
existing MattChat pattern —
[useStreamingMessage.ts:35-53](matt_chat_react/src/features/sessions/hooks/useStreamingMessage.ts#L35-L53));
native `EventSource` cannot send headers and is not used.

### Problems
| Method | Path | Notes |
|---|---|---|
| GET | `/v1/problems` | public; filters `?difficulty=&tag=&q=`; hides hidden tests |
| GET | `/v1/problems/{slug}` | public; includes sample tests + starter code only |
| POST | `/v1/problems` | `require_admin` |
| PATCH | `/v1/problems/{id}` | `require_admin` |
| GET | `/v1/problems/{id}/testcases` | `require_admin` (includes hidden) |
| POST | `/v1/problems/{id}/testcases` | `require_admin` |

### Submissions
| Method | Path | Notes |
|---|---|---|
| POST | `/v1/submissions` | body `{problem_id, language, code, workspace_id?}` → creates `queued`, enqueues job, returns `sub_…` |
| GET | `/v1/submissions/{id}` | poll final state |
| GET | `/v1/submissions` | `?problem_id=&user_id=`, mine by default |
| GET | `/v1/submissions/{id}/events` | **SSE, replay-then-follow** (§6.4) |

### Execution (ad-hoc "Run" — one endpoint, v2)
| Method | Path | Notes |
|---|---|---|
| POST | `/v1/execution/run` | body `{language, code, stdin?, workspace_id?}` → `run_…` id. `workspace_id` present → editor+ RBAC check + result tagged to the workspace. Rate-limited via `check_execution_quota`. |
| GET | `/v1/execution/{run_id}/events` | **SSE, follow-only** — ad-hoc runs are ephemeral (no table); a late/reconnecting subscriber may miss events. Acceptable: Run is fire-and-watch; graded history belongs to Submissions. |

### Workspaces
| Method | Path | RBAC |
|---|---|---|
| POST | `/v1/workspaces` | any user (becomes owner); server seeds the doc (§7.4) |
| GET | `/v1/workspaces` | mine (member of) |
| GET | `/v1/workspaces/{id}` | member |
| PATCH | `/v1/workspaces/{id}` | owner/editor |
| DELETE | `/v1/workspaces/{id}` | owner |
| GET/POST/DELETE | `/v1/workspaces/{id}/members` | owner manages roles |
| GET/POST/PATCH/DELETE | `/v1/workspaces/{id}/files` | editor+ for mutations, member for GET. **Sole authority for file metadata** (§4); mutations trigger the `127` broadcast. |

### AI assistant (reuses `BaseLLMService`)
| Method | Path | Notes |
|---|---|---|
| POST | `/v1/assist/explain` | **SSE**; `{problem_id?, code?, question}` → streamed help |

### WebSocket (collaboration)
| Path | Notes |
|---|---|
| `WS /ws/workspaces/{id}` | JWT via **subprotocol only** (query-string tokens land in access logs); RBAC checked on connect; speaks y-protocol (§7.2) |

---

## 6. Execution subsystem

### 6.1 Interfaces (`services/execution/base.py`)
```python
@dataclass
class ExecJob:
    id: str; language: str; code: str
    cases: list[ExecCase]          # empty for ad-hoc run (single stdin)
    time_limit_s: float; memory_kb: int; mode: Literal["run","judge"]

@dataclass
class ExecEvent:                   # streamed to the client over SSE
    kind: Literal["queued","compiling","case_started","case_result",
                  "verdict","error"]
    ordinal: int | None = None
    status: str | None = None      # per-case: passed/failed/tle/...
    runtime_ms: int | None = None; memory_kb: int | None = None
    verdict: str | None = None; message: str | None = None

class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, job: ExecJob) -> AsyncIterator[ExecEvent]: ...
```
`create_executor(settings)` picks `MockExecutor` / `PistonExecutor` — same shape as
`create_llm_service`.

**Per-case events are best effort.** Streaming `case_started`/`case_result` per test
implies one-at-a-time submission (N round-trips against Piston). An executor
that batches and polls — emitting coarser progress — is contract-conformant; only
`queued → … → verdict` ordering is guaranteed.

### 6.2 Flow
1. `POST /submissions` → persist `queued` → `job_queue.enqueue(ExecJob)` → return id.
2. **Worker = async task(s) in the API process (M1–M2).** The executor is the isolation
   boundary: MockExecutor runs no real code; PistonExecutor is an HTTP client and the
   untrusted code runs inside Piston's sandbox. `worker.py` is shaped to run standalone
   (own entrypoint, repo access via factory) but a separate process is only *required*
   if a local-execution (DIY Docker) executor ever exists.
3. Worker consumes `executor.execute(job)`; for judge mode compares each case via its
   checker (`exact` = trailing-whitespace-normalized match; `float_tolerance`;
   `unordered_lines`).
4. Worker **persists incrementally** (§4 Submission) and publishes each `ExecEvent` to a
   per-job channel (in-memory pub/sub → Redis in prod).

### 6.3 Verdict rules
Cases run in **ordinal order**; the **first failing case's status is the aggregate
verdict** and hidden-case execution stops there (sample cases always run, so the user
always sees full sample results). `accepted` iff all cases pass. `compile_error` verdict
when compilation fails before any case. Sample-test results are shown in full;
hidden-test results expose only status + ordinal, never stdin/expected output.

### 6.4 SSE contract: replay-then-follow
`GET /submissions/{id}/events` first **replays** events reconstructed from the
Submission row's current state (`running`, one `case_result` per persisted
`test_results` entry, `verdict` if terminal), **then follows** the live channel
(deduplicating by ordinal). Consequences: no subscribe-after-fire race (client may POST
then subscribe at leisure), reconnect works, terminal submissions replay entirely from
the row with no live channel needed. This is why §4 requires incremental persistence.

### 6.5 Ad-hoc runs are ephemeral — by design
`run_` jobs have no table. Events live only on the in-process channel; a server restart
or missed subscription loses them. Fine for fire-and-watch "Run"; anything needing
durability is a Submission.

### 6.6 Abuse controls (non-negotiable)
Per-user concurrency (`execution_user_concurrency`) + rate limit
(`execution_user_rate_per_min`) enforced by the `check_execution_quota` dependency
(§3.1), `execution_max_code_bytes`, per-case wall-clock cap, `--network=none` /
non-root / read-only FS enforced by Piston (isolate).

---

## 7. Collaboration subsystem

### 7.1 Server role (deliberately dumb about content, authoritative about structure)
The FastAPI WS endpoint does **not** parse document content. Per connection:
1. **Authenticate** (JWT via subprotocol) + **authorize** (must be a `WorkspaceMember`).
2. Join room keyed by `workspace_id` (via `CollaborationManager` + backplane).
3. On join: run the y-protocol sync handshake from the latest `DocSnapshot` + pending
   `DocUpdate`s.
4. Relay every inbound Yjs update / awareness frame to all other room members; append
   updates to `DocUpdate`.
5. **Viewer enforcement (three layers):** the client mounts the editor `readOnly`
   (primary); the server drops doc-update frames from viewers (safety net); **on any
   drop, the server immediately re-syncs the offender from server state** — a silent
   drop would permanently fork the viewer's local doc, since Yjs applies edits locally
   before broadcasting. Awareness frames from viewers are relayed (viewers have cursors).
6. Structure changes (file create/rename/delete) do **not** travel through the CRDT —
   they are REST mutations (§4 WorkspaceFile); the server broadcasts `127` so clients
   refetch the listing.

### 7.2 Wire protocol
**Real y-protocol** — `y-protocols/sync` (sync step 1/2 handshake + updates) and
`y-protocols/awareness`, so the stock `y-websocket` client provider works unmodified.
One extension message type, `127` file-listing-changed (server→client, payload empty),
outside the y-protocol tag space. We explicitly do **not** invent a half-compatible
custom framing.

### 7.3 Backplane interface
```python
class BaseBackplane(ABC):
    async def publish(self, room: str, frame: bytes, exclude: ConnId) -> None: ...
    def subscribe(self, room: str) -> AsyncIterator[tuple[ConnId, bytes]]: ...
```
`InMemoryBackplane` (single process, MVP) ↔ `RedisBackplane` (pub/sub, multi-instance),
selected by `realtime_backplane`. Same swap idiom as repositories. The execution rate
counter (§3.1) migrates here when Redis lands.

### 7.4 Server-side CRDT (`doc_store`, pycrdt — from M3)
Used narrowly, three jobs:
1. **Doc birth** — create the initial snapshot at workspace creation; for challenge
   attempts, seed starter code server-side (mandatory — see §4 DocSnapshot).
2. **Compaction** — fold `DocUpdate` log into a new `DocSnapshot` every
   `ws_snapshot_interval_updates`. Any instance may compact (commutative merges).
3. **(Later)** materialize buffers server-side so Run/Judge need not trust the client.

For MVP Run, the initiating client sends its current buffer. Note: CRDT convergence is
*eventual* — a client's buffer reflects the updates it has received, which is exactly
right for "run what I see" but is **not** a global-authority guarantee.

---

## 8. Frontend (React 19 + Vite, feature-sliced)

### State layering (extends MattChat's split)
- **Yjs doc + awareness** — live code + cursors/presence, *outside* React; React mounts
  the Monaco editor bound via `y-monaco`.
- **TanStack Query** — REST resources (problems, submissions, workspaces, members,
  file listing — invalidated on `127`).
- **Zustand** — UI state (active file, panel layout, run status).
- **Context** — auth (unchanged from MattChat).

### Feature slices
`problems` (list/detail/statement), `submissions` (history + verdict panel),
`workspace` (editor + file tree + presence avatars + run panel),
`collaboration` (Yjs provider hook, awareness → cursor overlays),
`execution` (SSE stream → per-test pass/fail — reuses `useStreamingMessage` almost
verbatim), `assist` (AI help panel).

The run/judge panel is the streaming-chat component with a verdict renderer instead of a
markdown renderer.

---

## 9. Testing

The swap-a-provider abstractions are the test seams — same philosophy as MattChat's
mock repos:

- **Judge flows:** `MockExecutor` + mock repos make the full submit → enqueue → worker →
  incremental persistence → SSE replay path unit-testable with zero infrastructure.
  Explicit cases: replay-then-follow after terminal verdict; replay+dedupe mid-job;
  first-failure short-circuit; checker enum behaviors.
- **Collaboration:** `InMemoryBackplane` + two fake WS clients (pytest, `TestClient`
  websockets) test relay, RBAC-on-connect, viewer drop→resync, join-time
  snapshot+update-log sync, and `127` broadcast on file mutation — no browser needed.
- **RBAC:** table-driven tests per endpoint × role (owner/editor/viewer/non-member/admin).
- **Executor conformance:** a shared contract-test suite run against `MockExecutor`
  (always) and `PistonExecutor` (behind an integration marker, needs Piston up) —
  guarantees event-ordering invariants of §6.1.
- **E2E (per milestone DoD):** M1 = solve a problem headlessly via API; M3 = two
  Playwright browsers converge on one document.

---

## 10. Build order (each milestone independently demoable)

- **M0 — Skeleton.** New backend + frontend from MattChat's shell: auth (+ `role`
  column + `require_admin`), users, config, DI, mock+sqlalchemy plumbing, Alembic
  baseline. *Done when* login works end-to-end and an admin user can be seeded.
- **M1 — Single-player challenges.** Problems + TestCases + Submissions + in-process
  job queue + `MockExecutor` + incremental persistence + SSE replay-then-follow +
  problem/submission UI. *Done when* you can solve a problem against sample+hidden tests
  with a streamed verdict that survives a page reload mid-judge. **Ships as a LeetCode
  clone (mock-judged).**
- **M2 — Piston.** Swap `MockExecutor` → `PistonExecutor`; Python + JS real sandboxing;
  abuse controls live. *Done when* real code runs isolated with TLE/MLE enforced and the
  executor contract tests pass against Piston.
- **M3 — Collaborative workspace.** Real WS `CollaborationManager` speaking y-protocol +
  `doc_store` (pycrdt birth/compaction) + Yjs + Monaco + presence + RBAC + REST file
  authority. *Done when* two browsers edit one workspace live with visible cursors, a
  viewer cannot mutate, and a rename mid-edit loses nothing.
- **M4 — Unify.** Bind a Problem to a workspace → collaborative problem-solving / pair
  interviews (challenge attempt = workspace + judge; starter code seeded server-side).
- **Phase 2** — Redis backplane (+ rate-counter migration), contests + leaderboards,
  ratings, PTY terminal, workspace chat, sandboxed custom checkers, function-signature
  judging, read-only sharing/visibility, AI hints deepened.

---

## 11. Final decisions (locked 2026-07-10 — nothing open)

1. **Layout:** siblings `solvary_backend/` + `solvary_react/` next to the MattChat
   dirs; `git init` the `MattChat/` folder as one monorepo.
2. **Job queue:** in-process `asyncio.Queue` for M1–M2 (consistent with §6.2); Redis
   queue arrives with the Redis backplane in phase 2.
3. **Authoring:** seed scripts (Python/JSON definitions + loader) for MVP. Admin API
   exists; authoring UI deferred to phase 2.
4. **Judge protocol:** stdin/stdout-first confirmed; function-signature drivers are
   phase 2.
