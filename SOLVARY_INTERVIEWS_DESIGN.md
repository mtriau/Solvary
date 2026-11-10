# Solvary — Mock Interview Mode (design addendum, draft v0.1)

Date: 2026-11-04. Status: **accepted and implemented (I1 + I2, 2026-11-04)**; the
`SOLVARY_DESIGN.md` v2.3 changelog entry points here. I3 (interviewer mode) is not
built. Implementation notes that differ from the draft: `switch` is `questions`-only
(in `levels` earlier statements stay readable in the payload, so no server round
trip is needed to re-read them); strict `levels` auto-advance is applied lazily on
any touch, stamped at the deadline; admin `POST /v1/interviews/templates` landed
with I1 because the tests author templates through it.

Originally written against the codebase as of the 2026-11-04 audit fixes (Run button,
Ask AI, quota fix).

## 0. The problem we are solving

Timed, multi-part coding assessments (CodeSignal-style: 3–4 parts, 60–90 minutes)
are lost on **pacing**, not on ability: too long on part 1, no time for parts 3–4.
Solvary today has no clock, shows a whole problem at once, and runs every test on
every submit. Nothing in the app creates time pressure or teaches when to move on.

Goal: a **Mock Interview** mode that reproduces the pressure of the real thing —
a server-authoritative countdown, parts revealed one at a time, tests released with
each part — and then *coaches pacing* with per-part budgets, nudges, and a
post-interview timeline that shows where the minutes went.

Non-goals (this addendum): proctoring/anti-cheat beyond "no peeking at locked
parts", leaderboards, Elo, AI-generated interview content, function-signature judging.

## 1. The two formats we emulate

| Format | Shape | Navigation | Tests | Real-world analogue |
|---|---|---|---|---|
| **`levels`** | One evolving problem. Part N adds requirements on top of parts 1..N-1; the **same code buffer** carries forward. | Sequential: part N+1 is hidden until you advance. | Part N's test set is **cumulative** (regressions for 1..N-1 + new cases). | CodeSignal "Industry Coding" style 90-minute, 4-level assessments — the one that bit yesterday. |
| **`questions`** | 3–4 independent problems, usually rising difficulty, each with its own buffer. | Free: all parts visible from the start, jump between them. | Each part has its own tests. | CodeSignal "General Coding" style 70-minute, 4-question assessments. |

One model covers both: an **interview template** is an ordered list of **stages**, each
stage *is* a `Problem`. The format only changes unlock policy, buffer layout, and how
statements are displayed. Nothing new is needed inside `Problem`/`TestCase`.

## 2. Fit with the current codebase

What this feature leans on, untouched:

| Existing piece | Role in interviews |
|---|---|
| `Problem` + `TestCase` (`is_sample` / hidden, checker enum) | A stage is a Problem. "Tests released in parts" = each stage has its own cases. Cumulative tests (levels) are **authored** into the later stage's problem — no judge changes. |
| `Submission` + `JudgeWorker` + SSE replay-then-follow + `check_execution_quota` | Interview submits are ordinary submissions tagged with a session id. Verdict streaming, incremental persistence, reconnect, quotas: all free. |
| `Workspace` + CRDT doc store + RBAC + `ChallengePanel` | **A session owns a workspace** (§3 decision 2). Code persists across reloads via the Yjs doc, "Run"/"Submit" from a workspace already exist, and a pair/interviewer mode later is just a second member. |
| `useJudgeStream`, `useRunStream`, `VerdictPanel`, `RunPanel`, `CollabEditor` | Reused verbatim in the interview page. |
| `StatsService` (pure derivations over submissions) | Session results are derived the same way: *best submission per stage* is a query, not a write path the worker has to know about. |
| `Problem.is_public` + `get_by_slug(include_private)` | Interview-only problems are `is_public=False`: hidden from the catalog and from `GET /v1/problems/{slug}`; the session endpoint is their only reader (§11). |
| `editorial_md` | Shown on the review page after the interview ends. |

What changes (small, additive):

| Change | Why |
|---|---|
| `submissions.interview_session_id` (nullable, indexed) | Link submissions to a session so results derive from them; also lets the quota/rate story stay as-is. |
| `workspaces.kind` (`"standard"` \| `"interview"`) | Interview workspaces are hidden from `/workspaces` and deleted with their session. |
| `SubmissionService.create`: when `interview_session_id` is present, validate session active + stage unlocked + problem matches; the workspace-bound-to-problem check is replaced by the session's stage check (a session workspace binds to N problems, `workspace.problem_id` stays `NULL`). | One validation path per tag, same pattern as `workspace_id`. |
| `AssistService.build_messages`: refuse while the user has an active session that contains the problem; allow after finish via `interview_session_id` (non-public problem authorization). | No AI help during a mock interview; AI post-mortem after. |
| `WorkspaceService.create` grows an internal `create_for_interview(files: list[(path, seed)])` | Session start seeds one file per stage (questions) or one file (levels) via `doc_store.birth`. |
| New: models/tables/repos/service/routes for templates + sessions, one Alembic migration, a seed script, a React feature slice + 3 routes. | The feature itself. |

Nothing changes in the executor, worker, broker, queue, quota, collab manager, or
the SSE contract.

## 3. Decisions (proposed as locked)

| # | Decision | Choice | Rationale / rejected alternative |
|---|---|---|---|
| 1 | Stage unit | **A stage is a `Problem`** (template = ordered list of problem ids). | Rejected: `Problem.parts[]` + `TestCase.part` — touches the core model, every reader, and the judge's case selection, to get the same result authoring already gives us. |
| 2 | Where interview code lives | **One Workspace per session** (`kind="interview"`), CRDT doc = the buffers. | Guiding principle #1 ("one core abstraction — the Workspace"). Gives reload-safe persistence, Run/Submit-from-workspace, and pair mode for free. Rejected: a `drafts` JSON column + debounced autosave endpoint — a second persistence path for code, and no route to pair mode. |
| 3 | Timer authority | **Server**: `started_at`, `ends_at`, `server_time` in every session response; client only renders. Submissions after `ends_at + grace` are rejected (409). | A client-side timer is a suggestion, not pressure. Reload/second tab/clock skew all handled by the same three fields. |
| 4 | Expiry | **Lazy**: any read or mutation after `ends_at` transitions `active → expired` and the session is finalized then. No background sweeper. | Results are derived from submissions, so nothing is lost by finalizing late. Same spirit as badges being pure derivations. |
| 5 | Cumulative tests (levels) | **Authored** into each level's problem (level 3's cases include level 1–2 regressions). | Keeps `Submission.problem_id` single-valued and ordinals unique. Matches how the real assessments work: later levels re-test earlier behavior. Seed helper makes the duplication a list concat. |
| 6 | Advance policy (levels) | Template field `advance: "free" \| "on_submit" \| "on_accept"`, **default `free`** with a confirm dialog when the current part isn't accepted. | Moving on from an unsolved part *is* the pacing skill. `on_accept` exists for "practice the hard way". |
| 7 | Results | **Derived** at read time: per stage, the submission in this session with max `passed` (ties → latest). Score = Σ best passed / Σ total. | No worker changes, no write-after-verdict race. |
| 8 | Time attribution | Session keeps a `timeline: [{stage, at}]`; the server appends on start, advance, and stage switch. Time per stage = Σ intervals where that stage was current. | One mechanism for both formats; the review page's pace chart reads it directly. |
| 9 | AI assist during the interview | **Off**. On (with the session's problems authorized) on the review page. | It is a mock *interview*. The post-mortem is where AI earns its keep ("why did I burn 30 minutes on part 2?"). |
| 10 | Concurrency | One **active** session per user. Starting another → 409 with the active id (resume or abandon). | Simplifies the timer UI (one global banner) and the quota story. |
| 11 | Pausing | **None.** `abandon` ends the session without a score. | Interviews don't pause. |

## 4. Data model

Prefixes follow §3.3: `itpl_`, `istg_`, `isess_`.

### InterviewTemplate — `itpl_`
```
id, slug (unique), title, description_md,
format: Literal["levels", "questions"],
duration_s: int,                       # whole-interview clock (e.g. 5400)
advance: Literal["free","on_submit","on_accept"] = "free",   # levels only
pacing: Literal["coached","strict"] = "coached",              # §9
is_public: bool = True, created_by (FK user), created_at, updated_at
```

### InterviewStage — `istg_` (belongs to Template; ordered)
```
id, template_id (FK, CASCADE), ordinal: int (1-based), problem_id (FK problems, CASCADE),
title: str,                            # "Level 1 — Basic operations" / "Question 2"
budget_s: int | None,                  # suggested minutes for this part (pacing coach)
```
Unique `(template_id, ordinal)` and `(template_id, problem_id)`. Stage problems are
seeded with `is_public=False`.

### InterviewSession — `isess_`
```
id, template_id (FK, RESTRICT), user_id (FK user, CASCADE),
workspace_id (FK workspaces, SET NULL),   # the code store; kind="interview"
status: Literal["active","finished","expired","abandoned"],
started_at, ends_at, finished_at: datetime | None,
current_stage: int,                        # 1-based ordinal
unlocked_through: int,                     # levels: grows on advance; questions: = n at start
stage_files: dict[ordinal, file_id],       # which workspace file holds each stage's code
timeline: list[{stage: int, at: datetime}],# §3 decision 8
created_at, updated_at
```
Indexes: `(user_id, created_at)`, partial/filtered `(user_id) WHERE status='active'`
(Postgres) — SQLite dev just uses the plain index.

### Submission (modified)
`interview_session_id: str | None` (FK sessions, SET NULL), index `(interview_session_id, created_at)`.

### Workspace (modified)
`kind: Literal["standard","interview"] = "standard"`. `list_mine` filters
`kind == "standard"`. Deleting a session deletes its workspace.

### Derived (never stored) — `StageResult`
```
ordinal, title, unlocked: bool, budget_s, time_spent_s,
submissions: int, best_submission_id, best_verdict, best_passed, best_total
```

## 5. Session lifecycle and timer semantics

```
POST /sessions {template}        ┌──────────┐  advance / switch / submit   ┌──────────┐
 ─ create workspace(kind=interview)│  active  │ ───────────────────────────▶│  active  │
 ─ seed one file per stage        └────┬─────┘                              └────┬─────┘
 ─ started_at = now                    │ finish (user)                           │ now > ends_at on any touch
 ─ ends_at = now + duration_s          ▼                                         ▼
 ─ timeline = [{1, now}]          ┌──────────┐                              ┌──────────┐
                                  │ finished │                              │ expired  │
                                  └──────────┘                              └──────────┘
                                        abandon (user, any time while active) → abandoned
```

- **Clock.** Every session response carries `started_at`, `ends_at`, `server_time`.
  The client stores `offset = server_time - Date.now()` at receipt and renders
  `ends_at - (Date.now() + offset)`. TanStack refetches the session every 60 s to
  re-sync; the countdown itself ticks locally.
- **Grace.** `interview_grace_s = 3` (config). A submission whose request arrives after
  `ends_at + grace` → 409 `Interview time is up`. Judging that is already in flight
  continues past the deadline and counts (the code was submitted in time).
- **Finalize** (on `finish`, or lazily on first touch after `ends_at`): set status,
  `finished_at = min(now, ends_at)` for expiry, append a closing timeline entry,
  make the workspace read-only (member roles → `viewer`; owner keeps `owner` but
  the interview page mounts the editor `readOnly` and the server rejects
  submissions for non-active sessions anyway).
- **Advance (levels).** `POST …/advance`: requires `status=active`,
  `current_stage == unlocked_through < n`, and the template's `advance` policy
  (`on_submit`: ≥1 submission on the current stage; `on_accept`: an accepted one).
  Effect: `unlocked_through += 1`, `current_stage += 1`, timeline append. The code
  buffer is the same file — carry-forward is implicit.
- **Switch (questions).** `POST …/switch {stage}`: any unlocked stage; timeline append.
  In `levels` format switching backwards is allowed for *reading* earlier
  statements, but the current stage (what Submit targets) only moves forward.
- **Submit.** `POST /v1/submissions {problem_id, language, code, interview_session_id}`
  — see §7. The client always submits the session's **current stage**.

## 6. REST API (all under `/api`, auth required)

| Method | Path | Notes |
|---|---|---|
| GET | `/v1/interviews/templates` | public templates: id, slug, title, format, duration_s, stage count, per-stage titles + budgets (never problems), caller's last result summary. |
| GET | `/v1/interviews/templates/{slug}` | same + `description_md`. |
| POST | `/v1/interviews/sessions` | `{template_id}` → 201 session. 409 if the caller already has an active session (`{active_session_id}` in detail). |
| GET | `/v1/interviews/sessions` | mine, newest first, paginated (`PaginatedResponse`). Lazily expires any `active` row past `ends_at`. |
| GET | `/v1/interviews/sessions/{id}` | **the interview payload**: session fields + `server_time` + `stages[]`. For `ordinal ≤ unlocked_through` the stage carries the full `ProblemDetail` (statement, starter, sample tests) + `file_id`; locked stages carry only `ordinal`, `title`, `budget_s`, `locked: true`. Includes derived `StageResult`s. Owner or admin only. |
| POST | `/v1/interviews/sessions/{id}/advance` | levels only (§5). Returns the updated session payload (new stage revealed). |
| POST | `/v1/interviews/sessions/{id}/switch` | `{stage}` — mark the current stage (time attribution + which problem Submit targets in `questions`). |
| POST | `/v1/interviews/sessions/{id}/finish` | early finish → `finished`. |
| POST | `/v1/interviews/sessions/{id}/abandon` | → `abandoned`, no score. |
| GET | `/v1/interviews/sessions/{id}/review` | after end only (409 while active): everything in the session payload **plus** every stage unlocked, `editorial_md` per stage, the full submission list, and the pace timeline. |
| POST | `/v1/submissions` | body gains `interview_session_id?`. |
| POST | `/v1/assist/explain` | body gains `interview_session_id?` — authorizes the session's non-public problems **only when the session is not active**. |

Error semantics follow `app/core/exceptions.py`: 404 unknown session, 403 not
yours, 409 state conflicts (time up, already active, locked stage, policy not met).

## 7. Judge integration

> **Added 2026-11-04 — pytest-style stages.** Screens of the Perplexity kind hand the candidate a module stub plus a *provided* pytest suite per part. Such a stage is a Problem with `judge_mode="pytest"` and `harness={"module": "todo_tracker", "files": {"test_todo_tracker_p1.py": …}}`; Part N's files are parts 1..N. One TestCase per test function (its id is the `stdin`, expected `PASS`), all samples, so the session page shows the suite under *Provided tests* and the judge panel lists results by test name with the assertion/traceback on failure. The interview workspace file is named `<module>.py`; the executor runs the suite in a single sandbox execution (`pytest_harness.py`). Python-only. Seeded by `scripts/seed_perplexity.py`; the Sierra set (`content/sierra_prep/`, `scripts/seed_sierra.py`, 2026-11-05) uses the same layout and builders — seven 3-part screens at Sierra's reported 30-minute pacing, with interviewer notes that record which parts are reported vs. reconstructed.

`SubmissionService.create` with `interview_session_id`:

1. Load session; must belong to the caller and be `active` and `now ≤ ends_at + grace`
   (lazy-expire otherwise → 409).
2. Resolve the stage for `data.problem_id` in the session's template; must exist and
   `ordinal ≤ unlocked_through` (403 otherwise — this is the "no peeking" enforcement
   on the write path, mirroring the read path in §11). In `levels` the stage must also
   be the current one.
3. `workspace_id` may be present (it will be — the editor is a workspace) but the
   "workspace bound to this problem" check is skipped; the session is the binding.
4. Create the submission with `interview_session_id` set; enqueue exactly as today.

Everything downstream (worker, broker, SSE, quota release, reaper) is unchanged. The
interview page uses `useJudgeStream` as the problem page does.

Hidden-case visibility during the interview is unchanged from normal judging:
status + ordinal only, which matches what real assessments show ("7/12 tests passed").

## 8. Frontend

Routes (lazy chunks, under `ArenaLayout`, new nav item **Interviews** with a `Timer` icon):

| Route | Page |
|---|---|
| `/interviews` | Template list: format badge, duration, parts with budgets, "Start"; a banner to resume/abandon an active session; past sessions list with scores. |
| `/interviews/sessions/:id` | **The interview.** |
| `/interviews/sessions/:id/review` | Results + pace timeline + editorials + Ask AI. |

Interview page layout (levels format shown):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ⏱ 41:17 remaining  ▮▮▮▮▮▮▮▮▮▮▮▮░░░░░░░░   L1 ✓ 12/12 · L2 ● 15m (budget 20m) │  ← TimerBar (sticky)
│                                            L3 🔒 · L4 🔒        [Finish early] │
├──────────────────────────────┬──────────────────────────────────────────────┤
│ Level 1 — Basic ops   ✓      │  main.py                      [Run] [Submit]  │
│ (collapsed statement)        │                                               │
│                              │  (CollabEditor on the session's workspace,    │
│ Level 2 — Prefix scan  ●     │   same Yjs doc, readOnly after the end)       │
│ …statement_md for level 2…   │                                               │
│ Sample tests (level 2)       ├──────────────────────────────────────────────┤
│                              │  Judge | Run        (no "Ask AI" tab here)    │
│ [Next part →]  (confirm if   │  ✓1 ✓2 ✓3 ✗4 … running…                       │
│  current part not accepted)  │                                               │
└──────────────────────────────┴──────────────────────────────────────────────┘
```
`questions` format: the left column becomes tabs Q1…Q4 (all enabled), each with its
own statement; selecting a tab calls `switch` and sets the active file to that
stage's file. Editor and panels are identical.

Feature slice `src/features/interviews/`:

- `hooks/useInterviewSession.ts` — TanStack query (`['interview', id]`, `refetchInterval: 60_000`), mutations for advance/switch/finish/abandon, and the invariant that mutations replace the cached payload (they return it).
- `hooks/useCountdown.ts` — `(endsAt, serverTime) → {remainingS, phase: 'ok'|'warn'|'critical'|'over'}` using the offset trick in §5; fires `onExpire` once, which refetches the session and navigates to review.
- `components/TimerBar.tsx` — countdown, overall progress bar, per-stage chips (locked / current / best score), budget nudge text (§9).
- `components/StagePanel.tsx` — statement stack (levels) or tabs (questions) + sample tests + Next/Switch controls. Reuses `ReactMarkdown` styling from `ProblemPage`.
- `components/PaceTimeline.tsx` — review page: horizontal bars, one per stage, planned budget vs actual, submission markers.
- `pages/interviews/InterviewsPage.tsx`, `InterviewSessionPage.tsx`, `InterviewReviewPage.tsx`.

The session page composes `useCollab(session.workspace_id)` + `CollabEditor` (file tree
hidden, active file = `stage_files[current_stage]`) + `useJudgeStream` + `useRunStream`
+ `VerdictPanel` + `RunPanel`. `ChallengePanel` is *not* reused as-is (it assumes
`workspace.problem_id`); its judge/run pane toggle is lifted into a small shared
`JudgeRunTabs` component that both panels use.

Leaving the page does not stop the clock. `ArenaLayout` shows a compact "Interview in
progress · 23:10" pill (from a lightweight `GET /v1/interviews/sessions?status=active`
query) that links back to the session.

## 9. Pacing features (the coaching layer)

This is what makes it training rather than a stopwatch.

1. **Budgets.** Each stage carries `budget_s` (seeded for every template; e.g. a
   90-minute levels interview: 15 / 20 / 25 / 30). The TimerBar shows the current
   stage's budget and elapsed, and turns amber at 100 % and red at 150 %.
2. **Nudges.** At budget end: a non-blocking toast — "Budget for Level 2 is up.
   You have 3 parts and 54 minutes left. Move on?" with a *Next part* button. At the
   **point of no return** (remaining time < Σ budgets of locked stages) the toast
   becomes persistent. Nudges are client-side; the data (budgets, timeline) is server-side.
3. **Strict pacing** (`pacing: "strict"`, I2). Stage deadlines are hard:
   `levels` → auto-advance when a stage's cumulative budget elapses (server enforces:
   `advance` is implied by time on any touch, the same lazy pattern as expiry);
   `questions` → a question locks for submissions at its deadline. This is the
   "practice under the real constraint" mode.
4. **Review timeline.** Planned vs actual per stage, with each submission as a tick
   (green = accepted). One sentence of diagnosis is computed server-side from the
   timeline alone (no LLM): "Part 2 took 2.1× its budget; parts 3–4 got 11 minutes
   combined." The AI panel on the review page gets the same timeline + per-stage
   results as context for "What should I have done differently?".
5. **History.** `/interviews` lists past sessions: score, time used, and the pacing
   diagnosis, so the trend over a week of practice is visible. Two badges in
   `StatsService`: **Clock Beater** (finish a session with every stage accepted before
   time) and **Pacer** (every stage within 110 % of budget).

## 10. Authoring and seed content

`scripts/seed_interviews.py` (idempotent by slug, like `seed_problems.py`) reuses the
`_problem` helper and adds `_template(slug, title, format, duration_s, stages=[...])`,
where each stage is `(problem, budget_s)` and the problems are created `is_public=False`.

Seeded content for the first cut:

- **`kv-store-levels`** — `levels`, 90 min, 4 levels, stdio judge (stdin = one command per
  line, stdout = one result per query). Level 1: `SET k v` / `GET k` / `DELETE k`.
  Level 2: `SCAN prefix` (sorted) + `COUNT`. Level 3: `SET k v TTL t` with
  `AT timestamp` on every command (expiry semantics). Level 4: `BACKUP ts` / `RESTORE ts`
  (snapshot + TTL re-basing). Level N's cases = concat of level 1..N-1 regression cases
  + level N cases, so the ordinals stay unique per problem. Budgets 15/20/25/30.
- **`warmup-questions`** — `questions`, 60 min, 4 questions from the existing public
  catalog (two-sum, fizzbuzz, mean-of-list, + one new medium). Budgets 10/10/15/25.
  Note: a stage may reference a public problem; only *interview-only* problems are
  private. The template list never serves statements either way.

Admin REST for templates (`POST/PATCH /v1/interviews/templates`, `require_admin`) is
specified but can land after the seed script (same decision as problem authoring, §11.3
of the main design).

## 11. Security / no-peek

- Stage problems are `is_public=False`: absent from `GET /v1/problems`, 404 from
  `GET /v1/problems/{slug}`, 404 from the assist endpoint. The **only** read path is
  the session payload, which serves `ProblemDetail` for `ordinal ≤ unlocked_through`
  and a title-only stub otherwise.
- Write path mirrors it: submissions to a locked stage → 403 (§7).
- The timer cannot be extended by the client; `ends_at` is set once. Tests assert that
  a submission at `ends_at + grace + 1s` is rejected while the same request 2 s earlier
  succeeds (clock injected, see §12).
- Sample tests for locked stages are never serialized; hidden tests never are.
- The session workspace is member-gated like any workspace; the interview page never
  needs file CRUD (file metadata mutations are rejected for `kind="interview"` — the
  file set is fixed at start).

## 12. Testing

Backend (`tests/test_interviews.py`, seeded templates built in-test via repos, clock
injected through a `now()` callable on `InterviewService` so no sleeps):

- Lifecycle: start → payload shape (stage 1 full, 2..n stubs) → advance → stage 2 full
  → finish → review has all stages + editorials; 409 on review while active.
- No-peek: `GET /v1/problems/{slug}` on a stage problem → 404; submission to a locked
  stage → 403; after advance → 201.
- Timer: submission before/after `ends_at + grace`; lazy expiry on GET; `advance`
  after expiry → 409; `server_time` present and monotonic.
- Policies: `on_submit` / `on_accept` gating; `free` always allowed.
- Results: three submissions on one stage with passed 3/5, 5/5, 4/5 → best = 5/5;
  score aggregates across stages; `questions` time attribution via `switch`.
- One-active-session rule; abandon clears it; workspace of kind `interview` hidden from
  `GET /v1/workspaces` and cascaded on session delete.
- Assist: 404 during active session, 200 after finish with `interview_session_id`.
- RBAC: another user's session → 403; admin → 200.

Frontend: `useCountdown` unit test with a fake `Date.now` (offset handling, phase
thresholds, single `onExpire`). Build + lint in CI as today.

## 13. Build order

- **I1 — Timed, staged, solo.** Models + migration + repos + service + routes;
  `interview_session_id` on submissions; workspace `kind`; seed `kv-store-levels` and
  `warmup-questions`; templates page, session page with TimerBar + stage stack/tabs +
  reused editor/judge/run; review page with per-stage results and editorials; tests in
  §12. *Done when* you can run a 90-minute 4-level mock end-to-end, reload mid-way
  without losing code or time, be refused a submit after the clock, and see a scored
  review. **This alone reproduces yesterday's interview.**
- **I2 — Pacing coach.** Budgets in the TimerBar, nudges, point-of-no-return,
  strict pacing, pace timeline + diagnosis on review, history list, two badges,
  in-progress pill in the top bar.
- **I3 — Interviewer mode.** Add a second member to the session workspace as `viewer`
  (an "interviewer"); they see the live buffer and verdict stream (already works via
  awareness) and get a **Release next part** button (`advance` authorized for the
  interviewer role). Timer shared because it's server state. Optional live chat is
  the existing phase-2 "workspace chat" item.
- **Later.** AI-generated templates ("make me a 4-level problem about rate limiters"),
  function-signature judging for LeetCode-style `questions` interviews, Java/C++.

## 14. Defaults chosen (flag if you want them different)

1. `advance` defaults to **`free`** with a confirm — moving on is the skill being trained.
2. **Levels show hidden-test pass counts** during the interview (status + ordinal), like
   the real thing; no stdin/expected for hidden cases.
3. **Ask AI is disabled** during an active session, enabled on review.
4. **No pause.** Abandon exists.
5. Budgets are **advisory** in `coached` mode (the default); `strict` is opt-in per template.
6. The session workspace is **single-file per stage** (levels: one `main.py`; questions:
   `q1.py` … `q4.py`); no file CRUD during an interview.
7. The interview page **does not** offer the language dropdown; language is chosen at
   start (template lists supported languages, default python) — same one-language-per-
   workspace constraint as today.

## 15. Amendments to `SOLVARY_DESIGN.md` on acceptance

- Changelog: **v2.3 — Mock interviews** (this addendum, summarized).
- §2 Locked decisions: add rows for decisions 1–4 and 7 of §3 above.
- §3.1 config: `interview_grace_s: int = 3`.
- §3.2 module layout: `models/interview.py`, `schemas/interviews.py`,
  `repositories/interview_repository.py` (+ sqlalchemy), `services/interview_service.py`,
  `api/v1/routes_interviews.py`, `scripts/seed_interviews.py`.
- §3.3 IDs: `itpl_`, `istg_`, `isess_`.
- §4 data model: the three new entities, `Submission.interview_session_id`, `Workspace.kind`.
- §5 API: the §6 table; `SubmissionCreate.interview_session_id`; `AssistRequest.interview_session_id`.
- §6.2 flow step 1: the §7 validation branch.
- §8 feature slices: `interviews`.
- §10 build order: I1–I3 after the existing phase-2 list; "timed contests" in the
  deferred list is partially subsumed (solo timed mode lands here; leaderboards stay deferred).
