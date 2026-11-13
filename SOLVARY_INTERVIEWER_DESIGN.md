# Solvary — Interviewer Agent (design addendum, v1.0)

Date: 2026-11-12. Status: **implemented (V1–V3, 2026-11-12)**; the `SOLVARY_DESIGN.md`
v2.6 changelog entry points here. Builds on `SOLVARY_INTERVIEWS_DESIGN.md` (I1 + I2
shipped) and replaces its sketched "I3 — Interviewer mode" (a second human in the
workspace) with an **AI interviewer** that sits in a third, resizable pane of the
interview page, sees what the candidate sees, listens to the candidate's microphone,
and speaks only when an interviewer would.

Written against the codebase at commit `9c228ca` (2026-11-12). Implementation notes
that differ from the draft:

- **The current code rides on every turn** (§4.3). The draft substituted
  `code: unchanged (N lines)` when the buffer had not changed; but earlier turns are
  replayed as digests without code, so the model would have had no code at all. The
  newest turn always carries the buffer plus a `code changed since your last reply:
  yes|no` line.
- **Lock placement** (§2.4). `prepare_turn` answers 409 when the session's lock is
  held; the lock itself is acquired inside the SSE generator (with a 90 s wait) so a
  request that never starts streaming cannot leak it.
- **Persistence from inside the stream** (§6). FastAPI closes the request's DB session
  before (or independently of) the streamed body, so the two turns are written on a
  fresh session (`open_interviewer_turn_repository` in `app/api/dependencies.py`);
  the route commits the request session before streaming so SQLite never waits on it.
- **Fallbacks are self-healing** (§5.4). The real client sends `fallbacks: "default"`
  with the beta header; if the API answers 400 mentioning fallbacks (a model without
  server-side fallback), it retries once without and stays off for the process.
- `app/services/ai_keys.py` (key resolution shared by `UserService` and
  `InterviewerService`) was added to the §9 map; `UserService` takes `settings` and
  the Claude client.
- Installed SDK is `anthropic` 2.8 (`>=1.0` pinned); `httpx2` coexists with the
  `httpx` 0.28 that Piston uses — verified in the venv.
- No frontend unit tests were added: the React app has no test runner today (§12
  lists them as the next hygiene step).

## 0. What we are building

A mock interview today is a timer, a statement, an editor and a judge. What it lacks
is the other half of a real screen: someone who asks "what are you thinking?",
notices you have been silent for three minutes, says "that's fine, move on", and asks
about the trade-off you just made. The candidate's weakness is pacing and narrating
while coding; the thing that trains that is being *talked to* while coding.

Goals:

1. **An interviewer pane** on `/interviews/sessions/:id`, right of the editor,
   resizable, collapsible. It shows a running transcript and a composer.
2. **Context awareness.** Every turn the agent gets a *context package*: the stage
   statement and provided tests, the code in the editor right now, the latest judge
   result (which tests fail and why), the latest Run output, the clock, the stage
   budget, and the conversation so far.
3. **Bring your own key.** The user pastes their Anthropic API key once in the app;
   the backend stores it encrypted and calls Claude with it. No key in the browser's
   requests to Anthropic.
4. **Microphone input.** Speech is transcribed in the browser and delivered to the
   agent as the candidate's utterances, only the candidate's, with sensible
   turn-taking: the agent answers when spoken to, and may chime in on events (a
   verdict, a budget blown, a long silence) or stay silent.
5. **Model:** Claude Sonnet (the user's call; see §3 decision 6). Configurable.

Non-goals for v1: the agent editing code, releasing parts by itself, grading the
interview, voice *output* beyond an optional browser text-to-speech toggle, multi-user
sessions, any change to the judge or the timer.

## 1. How it fits the current code

What this leans on, untouched:

| Existing piece | Role here |
|---|---|
| `InterviewService` + `SessionDetail` (`app/services/interview_service.py`) | Authoritative session state. The agent service calls `_load` through a new public `load_for_agent` and reuses `scaled_budgets`, `stage_times`, `session_end`, `_results`. |
| `AssistService` + `BaseLLMService` SSE pattern (`app/services/assist_service.py`, `app/services/llm_service.py`, `app/api/sse.py`) | Same stream shape to the browser: `{"content": …}` frames then `{"done": true, …}`. Validation happens before the `StreamingResponse` starts so 4xx codes survive. |
| `assist_limiter` (`app/core/rate_limit.py`) | Pattern for the new `interviewer_limiter`. |
| `settings.secret_key`, `python-jose[cryptography]` | The encryption key for stored API keys is derived from `secret_key`; `cryptography` is already installed. |
| `useJudgeStream`, `useRunStream`, `useCollab` + `CollabEditor` (Yjs `files` map) | The page already holds everything the agent must see. `currentCode()` in `InterviewSessionPage.tsx` is how the code is read; judge `events` carry per-test `stdout` with the traceback. |
| `ResizeHandle`, `usePersistedNumber` | Third column uses the same splitter as the left column. |
| `useAssistStream` fetch-reader loop | Copied verbatim for the turn stream. |
| Review page `AssistPanel` | Stays. The review page additionally shows the interviewer transcript. |

What changes (additive):

| Change | Why |
|---|---|
| `users.anthropic_api_key_enc`, `users.anthropic_api_key_last4` | Per-user key, encrypted at rest. |
| New table `interviewer_turns` | Transcript persists across reloads and into the review page; it is also the model's conversation history. |
| New service `InterviewerService`, new Claude client wrapper `app/services/claude_client.py` | The agent. |
| New routes `/v1/interviews/sessions/{id}/interviewer/*`, `/users/me/ai-key` | Turns, transcript, key management. |
| `SessionReview` gains `interviewer_turns` | Transcript on the review page. |
| `InterviewSessionPage` grows a third column; new feature slice `features/interviewer/` | The pane, the mic, the context package builder. |
| `InterviewsPage` gains an "Interviewer" card | Where the key is pasted. |
| Config: `anthropic_api_key`, `interviewer_model`, `interviewer_effort`, `interviewer_max_tokens`, `interviewer_enabled` | Server defaults; the per-user key overrides the server key. |
| `pyproject.toml` / `requirements.txt`: `anthropic>=1.0` | Official SDK. |

Nothing changes in the judge, the worker, the SSE broker, the collaboration manager,
the timer, or the no-peek rules.

## 2. The interaction model

### 2.1 Turns

Everything the agent does is a **turn**: one request to Claude, one streamed reply.
A turn has a trigger:

| Trigger | Source | Example user-side text |
|---|---|---|
| `speech` | microphone, after endpointing (§7) | "I'm going to use a dict keyed by the sorted word" |
| `typed` | composer text box | same, typed |
| `event` | the page, automatically (§2.3) | `[event] Submission judged: 5/7 passing. Failing: test_groups_follow_first_appearance…` |
| `opening` | session start, once | `[event] The interview has started.` |

Every turn carries the **context package** (§4). The reply is streamed into the pane.
A reply may be **silent**: the model answers with the exact string `[silent]` when an
interviewer would not speak (candidate thinking aloud mid-sentence, a verdict the
candidate is clearly already reading). Silent replies are stored but not rendered.

### 2.2 Turn-taking rules the model is given

The system prompt (§5) tells the model:

- Speak when addressed, when asked a question, or when the candidate pauses after
  explaining a plan. Otherwise prefer `[silent]`.
- Keep spoken replies to one to three sentences. Ask one question at a time.
- Do not give the solution. Hints only when asked, or when the candidate has been
  stuck on the same failing test for a long time (the context says how long).
- Watch the clock and the stage budget; say so once when a budget is exceeded.
- Never reveal locked parts, reference solutions, or hidden test inputs.

### 2.3 Automatic event turns

The page fires an `event` turn, with no speech, when:

| Event | Coalescing |
|---|---|
| Session starts (first mount of an active session with no turns yet) | once |
| A judge verdict arrives | one per submission |
| A Run finishes with a crash or a non-zero status | one per run |
| The stage advances or switches | one per change |
| The stage budget is exceeded | once per stage |
| No speech, no typed message and no code change for `IDLE_S` (default 180 s) | at most once per 5 minutes |

Events are queued behind any in-flight turn and merged: if two events fire while a
turn streams, one `event` turn is sent listing both. Speech always takes priority
over queued events (its utterance is sent as the next turn and the pending events are
folded into the same context package under "since your last reply").

### 2.4 Concurrency

One in-flight turn per session, enforced client-side (a queue) and server-side (an
in-process `asyncio.Lock` per session id in `InterviewerService`; a second concurrent
request gets 409 `A turn is already in progress`). This keeps the stored transcript
strictly ordered, which is what makes it replayable as the model's history.

## 3. Decisions (proposed as locked)

| # | Decision | Choice | Rationale / rejected alternative |
|---|---|---|---|
| 1 | Where Claude is called | **Backend**, Python SDK (`anthropic`), streamed to the browser over the existing SSE shape. | Rejected: browser-direct calls with `anthropic-dangerous-direct-browser-access`. The server already owns the session state and the problem content (including non-public stages), so the prompt is assembled where the truth is; the key never leaves the server; rate limits, logging and tests follow existing patterns. |
| 2 | Key storage | **Per-user, encrypted at rest** with Fernet, key derived from `secret_key` (HKDF-SHA256, info `solvary-user-secrets`). `ANTHROPIC_API_KEY` in server config is a fallback for single-user dev. The raw key is never returned by any endpoint; `last4` is. | Rejected: plaintext column; browser `localStorage` only (then the backend cannot call). Rejected for v1: a general secrets vault. |
| 3 | What the client sends | **The screen**: code, judge result with failure details, run output, which pane is visible, stage ordinal. **The server adds the truth**: statement, provided tests, stage results, clock, budgets, timeline, locked-part metadata. | The judge's per-test stdout/traceback exists only in the SSE stream the browser consumed; the server stores `{ordinal, status}` per test. Reading the Yjs doc server-side (`CollaborationManager` rooms hold a pycrdt `Doc`) is possible but couples the agent to room lifecycle for no gain; the page already has the exact buffer. |
| 4 | History | **Stored server-side** in `interviewer_turns`, replayed as the model's `messages`. Old turns carry only a one-line context digest; the full code snapshot rides only on the newest user turn. | Keeps the prompt prefix append-only and small (prompt-cache friendly, see §5.3) and gives the review page a transcript for free. Rejected: client-held history (lost on reload). |
| 5 | Silence | The model emits the literal `[silent]`; the server detects it in the first chunk and ends the stream with `{"done": true, "spoke": false}`. | Rejected: structured JSON output (cannot stream the spoken text); a `stay_silent` tool (adds a tool loop for a boolean). |
| 6 | Model and effort | `claude-sonnet-5-5`, adaptive thinking (SDK default), `output_config.effort = "low"`, `max_tokens = 1024`, streaming. Server-side refusal fallback enabled (`fallbacks: "default"`, beta `server-side-fallback-2026-07-01`). | User's choice of Sonnet; `low` is the documented starting point for chat-shaped latency-sensitive routes on Sonnet 5.5 and keeps thinking short. Refusals arrive as HTTP 200 `stop_reason: "refusal"`; the fallback retries the retryable categories and the stream handler reports the rest as an error frame. Model and effort are config, so Opus is one env var away. |
| 7 | Speech-to-text | **Browser Web Speech API** (`SpeechRecognition`, Chrome/Edge), continuous, interim results, auto-restart on `end`. | Anthropic has no STT endpoint and the user has only a Claude key. Rejected for v1: server-side Whisper (a second service), a paid STT key. Firefox/Safari: the mic button is disabled with a tooltip; typing still works. |
| 8 | Endpointing ("only what I'm saying, when I'm done") | A final recognition result starts a **settle timer** (`SETTLE_MS`, default 1200). More final results extend it. When it fires, the accumulated text is one `speech` turn. A **push-to-talk** mode (hold the mic button or `Ctrl+Shift+Space`) sends on release. Recognition is **paused while TTS speaks** and for 400 ms after, so the agent never hears itself. | The recognizer's own end-of-phrase detection is too eager for someone narrating code; the settle timer lets you take a breath. Push-to-talk is the fallback for noisy rooms. |
| 9 | Voice output | **Optional** `speechSynthesis` toggle, off by default. | Zero cost, no key, and it makes the mic-mute rule in #8 necessary. Real voices (ElevenLabs etc.) are out of scope. |
| 10 | What the agent knows | **The whole template**: every stage's statement, provided tests (sample cases only, never hidden stdin), interviewer notes, and the reference solution, locked parts included, all marked. | A real interviewer has the answer key and knows what part 3 is; that is what lets them pace you and judge an approach. The system prompt forbids revealing any of it. Leakage risk is accepted for a single-user practice tool; `interviewer_knows_solutions` config can turn the reference solutions off. |
| 11 | Ask AI during the interview | Stays **disabled** (`AssistService` unchanged). The interviewer is not a tutor. | Decision 9 of the interviews addendum stands. |
| 12 | Agent actions | **None in v1.** No tools. "Release the next part" and a post-interview debrief are v2 (§11). | The user asked for a basic agent; tool use adds a loop, an approval question and cache churn. |

## 4. The context package

### 4.1 Client → server (`InterviewerTurnRequest`)

```python
class JudgeFailure(BaseModel):
    name: str                      # "test_event_streams_p2.py::test_at_most_one_unread_event_per_stream" or "Test 3"
    detail: str = Field(max_length=800)   # assertion / traceback, already stripped of PASS/FAIL

class JudgeSnapshot(BaseModel):
    submission_id: str | None
    verdict: str                   # accepted | wrong_answer | tle | ...
    passed: int
    total: int
    failures: list[JudgeFailure] = Field(max_length=12)
    age_s: int                     # seconds since the verdict arrived

class RunSnapshot(BaseModel):
    status: str | None
    stdin: str = Field(max_length=1000)
    stdout: str = Field(max_length=2000)
    stderr: str = Field(max_length=2000)
    age_s: int

class ScreenContext(BaseModel):
    stage: int                     # ordinal the candidate is looking at
    code: str                      # current buffer; bounded by execution_max_code_bytes
    code_changed_since_last_turn: bool
    judge: JudgeSnapshot | None
    run: RunSnapshot | None
    visible_pane: Literal["judge", "run", "none"]
    seconds_since_last_edit: int
    mic: Literal["open", "push", "off"]

class InterviewerTurnRequest(BaseModel):
    trigger: Literal["speech", "typed", "event", "opening"]
    utterance: str | None = Field(default=None, max_length=2000)   # required for speech/typed
    events: list[str] = Field(default_factory=list, max_length=8)  # event lines (§2.3)
    screen: ScreenContext
```

Server-side bounds: `code` ≤ `execution_max_code_bytes` (64 KB, the same check as
assist); failure details truncated to 800 chars each, run output to 2000 chars.
Oversize → 400, before the stream starts.

### 4.2 Server-added truth (built in `InterviewerService._truth`)

From the session (via `InterviewService`): status, `remaining_s` (server clock, not
the client's), current stage and its budget, `stage_elapsed_s` (from the timeline),
per-stage results so far, format, advance policy, the template title. From the
problems: the current stage's title and statement; for pytest stages, the harness
file names and sizes (the content is in the cached template package, §5.2).

### 4.3 What the model sees per turn

The newest user turn is a list of text blocks in this order:

1. `<screen>` block: the truth (4.2) and the screen (4.1), rendered as compact
   key: value lines plus a fenced code block of the buffer. The buffer is always
   included (earlier turns never carry it); a `code changed since your last reply:
   yes|no` line tells the model whether to re-read it.
2. `<events>` block, if any (one line each).
3. The utterance, verbatim, or `(no speech)` for event turns.

Previous turns are stored as the one-line **digest** that was true at the time
(`stage 2 · 14:05 left · judge wrong_answer 5/7 · code 41 lines`) followed by the
utterance or event lines, never the old code. The model is told this in the system
prompt ("earlier turns show a digest; the current buffer is always in the latest
turn").

## 5. Prompt assembly and caching

### 5.1 System prompt, part 1 (static, byte-identical across sessions)

Persona + rules (§2.2), the `[silent]` protocol, the digest convention, the length
rule, "you are evaluating communication, design reasoning and pacing, not only
correctness", and the no-reveal rules. Lives in `app/services/interviewer_prompt.py`
as a module constant so it is frozen and testable.

### 5.2 System prompt, part 2 (per template, stable for the session)

The **template package**, rendered deterministically from the template and its
stages (sorted by ordinal): ground rules (`description_md`), then per stage: title,
budget, `statement_md`, provided tests (harness files for pytest stages; sample
cases for stdio stages; hidden cases never), interviewer notes and the reference
solution (both come from `editorial_md`; `split_reveal`'s "Interviewer notes" footer
is already moved there by the seeder, and the reference is the fenced block under
"Reference solution"), each section labelled `LOCKED` or `UNLOCKED` as of this turn
only in the *screen* block, never here (so the bytes do not change when a part is
released). This block carries `cache_control: {"type": "ephemeral"}`.

Size check: the largest Sierra template (event streams) is about 9 KB of statements
plus 12 KB of tests plus 3 KB of reference, well under 10K tokens. Cached reads at
Sonnet 5.5 prices make the per-turn cost dominated by output.

### 5.3 Messages

```
[... stored turns: user(digest + utterance) / assistant(text or "[silent]") ...]
user: [<screen>, <events>, utterance]      ← cache_control on the last block
```

Append-only. Assistant turns are replayed as text only; thinking blocks are never
stored or replayed, so the preserved-thinking history check cannot trip. If a stored
assistant turn is `[silent]`, it is replayed verbatim so the model sees its own past
choice.

### 5.4 The request

```python
async with client.beta.messages.stream(        # beta namespace: `fallbacks` lives there
    model=settings.interviewer_model,            # claude-sonnet-5-5
    max_tokens=settings.interviewer_max_tokens,  # 1024
    system=[
        {"type": "text", "text": STATIC_SYSTEM},
        {"type": "text", "text": template_package, "cache_control": {"type": "ephemeral"}},
    ],
    messages=history + [current_user_turn],
    output_config={"effort": settings.interviewer_effort},   # "low"
    betas=["server-side-fallback-2026-07-01"],
    fallbacks="default",
) as stream:
    async for text in stream.text_stream: ...
    final = await stream.get_final_message()   # usage, stop_reason
```

`stop_reason == "refusal"` after fallback → one `{"error": "The interviewer declined
to answer that."}` frame, then done; the user turn is still stored (so the transcript
shows what was asked), with an assistant turn `[refused]`. `max_tokens` → the reply is
kept as-is and flagged `truncated: true` in the done frame.

`fallbacks` and `betas` are accepted only on the `client.beta.messages.*` methods, so
this one call goes through the beta namespace. If the installed SDK predates the
parameter, the wrapper falls back to the plain `client.messages.stream` without
`fallbacks` and logs once (§13 question 7). A refusal that survives the fallback is
still `stop_reason: "refusal"` on the final message.

## 6. Data model

Prefix convention (§3.3 of the main design): `ivt_` for interviewer turns.

### User (modified)

```
anthropic_api_key_enc: str | None   # Fernet token, Text
anthropic_api_key_last4: str | None # "…k3Qa" for the settings UI
```

### InterviewerTurn — `ivt_`

```
id, session_id (FK interview_sessions, CASCADE), user_id (FK users, CASCADE),
ordinal: int                      # 1-based within the session; unique (session_id, ordinal)
role: Literal["user", "assistant"]
trigger: Literal["speech", "typed", "event", "opening"] | None   # user turns only
content: Text                     # utterance / event lines, or the reply / "[silent]" / "[refused]"
digest: str                       # one line, user turns only (§4.3)
silent: bool = False              # assistant turns
model: str | None                 # assistant turns
input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens: int | None
created_at
```

Index `(session_id, ordinal)` unique. A `user` turn and its `assistant` reply are
written in one transaction after the stream ends (the user turn first, so a crash
mid-stream leaves a user turn with no reply; the next request's history builder
tolerates a trailing user turn by folding it into the new one).

Migration `b7e4d2c9a1f0_interviewer_agent.py` (revises `9d2f4b7c1e55`): batch-mode
`ALTER TABLE users ADD COLUMN …` ×2, `CREATE TABLE interviewer_turns`, index.

## 7. Microphone and turn-taking (frontend)

`features/interviewer/hooks/useSpeechInput.ts`:

- Feature-detects `window.SpeechRecognition ?? window.webkitSpeechRecognition`.
  TypeScript's `lib.dom` ships the `SpeechRecognitionResult*` types but not the
  `SpeechRecognition` constructor; add `src/shared/types/speech.d.ts` with the
  ambient declarations (constructor, `continuous`, `interimResults`, `lang`,
  `onresult`, `onend`, `onerror`, `start`, `stop`, `abort`).
- Modes: `off`, `open` (continuous; settle timer), `push` (start on press, stop on
  release, send immediately). Mode persisted in `localStorage` (`interviewer.mic`).
- Returns `{ supported, mode, setMode, listening, interim, error, pressStart, pressEnd, pause, resume }`.
- Open mode: `continuous = true`, `interimResults = true`. `onresult` splits final
  from interim transcripts; each final segment appends to `pendingRef` and (re)starts
  the settle timer; the timer flushes `pendingRef` via `onUtterance(text)`. `onend`
  restarts recognition unless the mode is off or paused (Chrome stops after ~60 s of
  silence and on network hiccups). `onerror` with `not-allowed` turns the mode off and
  surfaces the permission error.
- `pause()` / `resume()` are called by the TTS hook around every utterance it speaks
  and by the turn queue while a turn is streaming when TTS is on. Interim text is
  shown in the pane in grey so the candidate sees what will be sent.

`features/interviewer/hooks/useInterviewer.ts`:

- `useQuery(['interviewer', sessionId])` for the transcript (`GET …/interviewer/turns`).
- A FIFO turn queue. `enqueue({trigger, utterance?, events?})`; the worker pops one,
  builds the `ScreenContext` by calling `buildScreen()` (passed in by the page),
  streams `POST …/interviewer/turns`, appends the growing reply to local state,
  then invalidates the transcript query. Queued `event` items merge into a single
  turn; a queued `speech`/`typed` item absorbs pending events into its `events`.
- Exposes `{ turns, streaming, partial, enqueue, speak, error }`.

`features/interviewer/lib/screen-context.ts`: pure function
`buildScreenContext({ collab, fileId, stage, judgeEvents, verdict, runState, pane, lastEditAt, mic, lastCode })`
→ `ScreenContext`. Failures come from `events.filter(kind === 'case_result' && status !== 'passed')`
with `testLabels` for names and `VerdictPanel`'s `failureDetail` rule for the detail
(extract that helper into `features/execution/lib/failure-detail.ts` and use it in both
places).

`features/interviewer/hooks/useSpeechOutput.ts` (optional TTS): `speechSynthesis`
with a single queued utterance per reply (spoken when the stream ends, not per
chunk, to avoid robotic chunk boundaries); `onstart` → `speech.pause()`, `onend` →
`setTimeout(speech.resume, 400)`.

Edge rules:

- Mic is force-paused while `streaming && tts.enabled`; otherwise open mic stays on
  during a reply so the candidate can keep narrating.
- `Ctrl+Shift+M` toggles the mic mode between `off` and the last non-off mode;
  `Ctrl+Shift+Space` is push-to-talk (keydown start, keyup send). Both are ignored when
  Monaco has focus and the key chord is being used by the editor (checked via the
  default-prevented flag).
- The session page's `beforeunload` is unchanged; recognition stops on unmount.

## 8. REST API (under `/api`, auth required)

| Method | Path | Notes |
|---|---|---|
| GET | `/users/me/ai-key` | `{configured: bool, last4: str \| null, source: "user" \| "server" \| "none"}` |
| PUT | `/users/me/ai-key` | `{api_key}` → validates shape (`sk-ant-` prefix, length), encrypts, stores; returns the GET shape. Never echoes the key. |
| DELETE | `/users/me/ai-key` | clears; falls back to the server key if configured. |
| POST | `/users/me/ai-key/test` | one `messages.create` with `max_tokens: 8` on the configured key → `{ok: true, model}` or 400 with Anthropic's error message (401 → "invalid key"). Rate limited 5/min. |
| GET | `/v1/interviews/sessions/{id}/interviewer/turns` | transcript, oldest first. Owner or admin. Works for finished sessions. |
| POST | `/v1/interviews/sessions/{id}/interviewer/turns` | body `InterviewerTurnRequest`; SSE `{"content"}`* then `{"done": true, "spoke": bool, "turn_id": …, "truncated": bool}`; or `{"error": …}` then done. 409 if the session is not active, 409 if a turn is in flight, 402 `NO_API_KEY` if no key is configured anywhere, 400 on oversize context, 429 over the limiter. |
| DELETE | `/v1/interviews/sessions/{id}/interviewer/turns` | admin/testing: wipe the transcript (not exposed in the UI). |
| GET | `/v1/interviews/sessions/{id}/review` | **modified:** `SessionReview` gains `interviewer_turns: list[InterviewerTurnResponse]`. |

Rate limit: `interviewer_limiter = _make_limiter("interviewer", limit=40, window_s=60)`
per user (speech turns are frequent; event turns are coalesced).

Error codes follow `app/core/exceptions.py`; a new `PaymentRequiredException(402,
"NO_API_KEY")` is added there for the no-key case so the pane can render its setup
state from the code alone.

## 9. Backend module map (files to touch, in order)

### New

| File | Contents |
|---|---|
| `app/core/secrets.py` | `encrypt_secret(plain) -> str`, `decrypt_secret(token) -> str`, `derive_key()` (HKDF-SHA256 over `settings.secret_key`, salt `b"solvary"`, info `b"user-secrets"`, 32 bytes, urlsafe-b64 → `Fernet`). Refuses to encrypt when `secret_key == "change-me"` and `environment == "production"` (same fail-fast spirit as `main.create_app`). |
| `app/services/claude_client.py` | `ClaudeClient` protocol: `stream_turn(api_key, system, messages, *, model, effort, max_tokens) -> AsyncIterator[ClaudeChunk]` where `ClaudeChunk` is `{text}` or terminal `{stop_reason, usage, model}`; `AnthropicClaudeClient` (real, `anthropic.AsyncAnthropic(api_key=…)` built per call, 60 s timeout, `max_retries=2`); `FakeClaudeClient` (scripted replies for tests; a reply can be `"[silent]"`). Factory `get_claude_client()` keyed on `settings.interviewer_provider` (`"anthropic"` \| `"fake"`). |
| `app/services/interviewer_prompt.py` | `STATIC_SYSTEM: str`; `render_template_package(template, stages, problems, cases, include_solutions: bool) -> str`; `render_screen(truth, screen, events) -> str`; `digest(truth, screen) -> str`; `split_editorial(editorial_md) -> (notes, reference)` (inverse of `seed_perplexity.editorial`). Pure functions, unit-tested. |
| `app/services/interviewer_service.py` | `InterviewerService(session_repo?, turn_repo, interview_service, problem_repo, testcase_repo, template_repo, stage_repo, user_repo, claude, settings)`. Methods: `resolve_api_key(user) -> str` (user key → server key → `PaymentRequiredException`), `list_turns(user, session_id)`, `prepare_turn(user, session_id, req) -> PreparedTurn` (validation + prompt assembly, raises before streaming), `stream_turn(prepared) -> AsyncIterator[dict]` (holds the per-session lock, streams, detects `[silent]`, persists both turns, yields SSE payloads), `clear(user, session_id)`. Per-session `asyncio.Lock` map in a module-level dict keyed by session id (single-instance, like the memory limiter; §13 question 8 for Redis). |
| `app/models/interviewer.py` | `InterviewerTurn` dataclass. |
| `app/repositories/interviewer_repository.py` | `InterviewerTurnRepository(AbstractRepository)`: `list_by_session`, `next_ordinal`, `delete_by_session`; `MockInterviewerTurnRepository`. |
| `app/repositories/sqlalchemy_interviewer_repository.py` | SQLAlchemy implementation (same shape as `sqlalchemy_interview_repository.py`). |
| `app/schemas/interviewer.py` | §4.1 request models, `InterviewerTurnResponse`, `AiKeyStatus`, `AiKeySet`. |
| `app/api/v1/routes_interviewer.py` | the turn endpoints (prefix `/v1/interviews/sessions/{session_id}/interviewer`). |
| `alembic/versions/b7e4d2c9a1f0_interviewer_agent.py` | §6 migration. |
| `tests/test_interviewer.py` | §12. |

### Modified

| File | Change |
|---|---|
| `app/config.py` | `anthropic_api_key: str = ""`, `interviewer_provider: str = "anthropic"` (`"fake"` in tests), `interviewer_model: str = "claude-sonnet-5-5"`, `interviewer_effort: str = "low"`, `interviewer_max_tokens: int = 1024`, `interviewer_knows_solutions: bool = True`, `interviewer_idle_s: int = 180` (served to the client via the turns GET so the page and server agree). |
| `app/db/tables.py` | `UserRow`: two columns. New `InterviewerTurnRow`. |
| `app/models/user.py`, `app/repositories/sqlalchemy_user_repository.py` (`create`, `update`, `_to_domain`), `app/repositories/user_repository.py` (mock), `app/mock_data/users.py` | carry the two new fields. |
| `app/schemas/users.py`, `app/services/user_service.py`, `app/api/v1/routes_users.py` | the three `/users/me/ai-key` endpoints (`UserService.get_ai_key_status`, `set_ai_key`, `clear_ai_key`, `test_ai_key(claude)`). `UserResponse` is unchanged (no key material in `/users/me`). |
| `app/core/exceptions.py` | `PaymentRequiredException` (402, `NO_API_KEY`). |
| `app/core/rate_limit.py` | `interviewer_limiter`, `ai_key_test_limiter`. |
| `app/api/dependencies.py` | `get_interviewer_turn_repository`, `get_interviewer_service`; `get_user_service` gains the claude client for the test endpoint. |
| `app/api/router.py` | include `routes_interviewer.router`. |
| `app/services/interview_service.py` | add public `load_for_agent(user, session_id) -> (session, template, stages)` (thin wrapper over `_load` so the agent service does not reach into a private method), and `results_for(session, stages)` exposing `_results`. |
| `app/schemas/interviews.py`, `InterviewService.review` | `SessionReview.interviewer_turns`. |
| `app/repositories/mock_registry.py` | register the mock turn repo. |
| `tests/conftest.py` | `os.environ["INTERVIEWER_PROVIDER"] = "fake"`; reset `interviewer_limiter`. |
| `pyproject.toml`, `requirements.txt` | `anthropic>=1.0`. |
| `.env.example`, `README.md` (new "Interviewer agent" section after "Mock interviews"), `SOLVARY_DESIGN.md` changelog, `SOLVARY_INTERVIEWS_DESIGN.md` §13 I3 note | docs. |

## 10. Frontend module map

### New (`src/features/interviewer/`)

| File | Contents |
|---|---|
| `components/InterviewerPane.tsx` | The third column. Header: "Interviewer" + model badge + collapse button + mic mode segmented control (`Off / Open / Push`) + TTS toggle. Body: transcript (user bubbles right, interviewer left; event turns as small grey system lines; `[silent]` turns hidden; a "listening…" row showing interim speech). Footer: composer (textarea, Enter sends, Shift+Enter newline; send button; a "Nudge" button that fires an `event` turn "The candidate asked for a check-in"). Empty states: no key (link to `/interviews` card), unsupported browser (mic controls disabled), inactive session (read-only transcript). |
| `components/ApiKeyCard.tsx` | On `InterviewsPage`: status (`Server key` / `Your key ····k3Qa` / `Not configured`), paste field, Save, Test, Remove. Uses `useAiKey`. |
| `components/TranscriptList.tsx` | shared by the pane and the review page. |
| `hooks/useInterviewer.ts` | §7. |
| `hooks/useSpeechInput.ts` | §7. |
| `hooks/useSpeechOutput.ts` | §7. |
| `hooks/useAiKey.ts` | TanStack query + mutations over the three key endpoints. |
| `lib/screen-context.ts` | §7. |
| `lib/events.ts` | event-line formatters (`verdictEvent(verdict, labels)`, `budgetEvent(stage)`, …). |

### Modified

| File | Change |
|---|---|
| `src/pages/interviews/InterviewSessionPage.tsx` | Add `rightWidth` via `usePersistedNumber('interview.interviewerWidth', 360, 280, …)` and `interviewerOpen` via `localStorage`; render `<ResizeHandle direction="col" onDrag={(dx) => setRightWidth((w) => w - dx)} />` + `<InterviewerPane …/>` after the editor column. Track `lastEditAt` by observing the Y.Text (`ytext.observe`) once `collab && fileId`. Fire the §2.3 events from existing effects: the `verdict` effect (already invalidates the session) also enqueues the verdict event; `runState.status` change → run event; `session.current_stage` change → stage event; `overBudget` rising edge → budget event; an idle interval. Pass `buildScreen` to `useInterviewer`. When `!active`, the pane shows the transcript read-only. The left/center/right max widths need re-clamping: `leftWidth` max becomes `window.innerWidth - 420 - rightWidth`. |
| `src/features/interviews/components/TimerBar.tsx` | A small "Interviewer" toggle button (icon `MessageSquare`) at the right of the bar to open/collapse the pane. |
| `src/pages/interviews/InterviewReviewPage.tsx` | New card "Interviewer transcript" (`TranscriptList` over `review.interviewer_turns`) above the per-part results; hidden when empty. |
| `src/pages/interviews/InterviewsPage.tsx` | `ApiKeyCard` at the top of the page (below the active banner). |
| `src/features/execution/components/VerdictPanel.tsx` | `failureDetail` moves to `features/execution/lib/failure-detail.ts` and is imported. |
| `src/shared/lib/api.ts` | `fetchAiKey`, `setAiKey`, `clearAiKey`, `testAiKey`, `fetchInterviewerTurns`, `clearInterviewerTurns`. The turn POST uses a raw `fetch` reader (SSE) inside `useInterviewer`, like `useAssistStream`. |
| `src/shared/types/api.ts` | `AiKeyStatus`, `InterviewerTurn`, `InterviewerTurnRequest` and the §4.1 shapes, `InterviewSessionReview.interviewer_turns`. |
| `src/shared/types/speech.d.ts` | ambient `SpeechRecognition` declarations (new). |

Layout after the change (levels format):

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ⏱ 24:10  ▮▮▮▮▮▮░░░░  P1 ✓ · P2 ● 9:12 / 12:00 · P3 🔒            [Interviewer ▣] [Finish] │
├──────────────────────┬────────────────────────────────────┬──────────────────────────────┤
│ Part 2 — Lazy k-way  │ event_streams.py        [Run][Submit]│ Interviewer · sonnet   🎙 Open │
│ merge …statement…    │                                    │──────────────────────────────│
│                      │  (CollabEditor)                    │ ▸ Started. Talk me through    │
│ Provided tests       │                                    │   how you read part 1.        │
│ test_event_streams…  │                                    │ ◂ I'll prime one head per     │
│                      ├────────────────────────────────────┤   stream and keep a heap…     │
│ [Next part →]        │ Judge | Run                        │ ▸ Why a heap and not a scan   │
│                      │ ✓ ✓ ✗ test_two_thousand_streams…   │   over the heads?             │
│                      │                                    │ · judged: 14/15 (silent)      │
│                      │                                    │ ┈ listening: "because the…"   │
│                      │                                    │──────────────────────────────│
│                      │                                    │ [type to the interviewer…][⏎]│
└──────────────────────┴────────────────────────────────────┴──────────────────────────────┘
```

## 11. Build order

- **V1 — Key + typed turns.** Secrets helper, user columns + migration, key endpoints
  and `ApiKeyCard`; `ClaudeClient` (real + fake); `InterviewerService` with
  `prepare_turn`/`stream_turn`; turns table and transcript; the pane with the
  composer only (no mic); opening turn and verdict event. *Done when* you can run a
  Sierra mock, type "I'm thinking of a heap here", get a one-sentence reply that
  references the exact failing test name, reload and still see the transcript.
- **V2 — Microphone.** `useSpeechInput` (open + push), settle endpointing, interim
  display, keyboard chords, TTS toggle with the mute rule. *Done when* you can
  narrate for 20 minutes hands-free, the agent answers only when you stop, and never
  transcribes its own voice.
- **V3 — Events + review.** Remaining §2.3 events with coalescing, idle nudge,
  transcript card on the review page, token usage shown in the pane header
  (`Σ in / out / cached` from the done frames).
- **Later.** Tools: `release_next_part` (calls `InterviewService.advance`, respects the
  template's policy, confirmed in the pane), `request_run` (the agent asks the page to
  run a specific test). Debrief: `POST …/interviewer/debrief` after finish, a
  structured (`output_config.format`) assessment on communication, design, pacing,
  stored on the session and shown on the review page. Server-side STT. Redis-backed
  per-session lock for multi-replica deployments.

## 12. Testing

Backend (`tests/test_interviewer.py`, `INTERVIEWER_PROVIDER=fake`, clock via
`interview_service.utcnow` as in `test_interviews.py`):

- Key endpoints: PUT stores encrypted (row value ≠ key, `last4` right), GET never
  returns the key, DELETE clears, invalid shape → 422, `test` calls the fake client.
- `secrets`: round trip; a different `secret_key` fails to decrypt (`InvalidToken` →
  402 `NO_API_KEY` with a log line, not a 500).
- Turn: 402 without a key; 409 on a finished session; 403 on another user's session;
  400 on oversize code; 429 past the limiter.
- Stream shape: `content` frames then `done` with `spoke: true`; fake reply
  `"[silent]"` → no `content`, `spoke: false`, assistant turn stored with `silent`.
- Prompt assembly (unit, `interviewer_prompt`): template package contains every
  stage's statement and provided tests, reference solution present when
  `interviewer_knows_solutions`, absent otherwise; hidden stdio case stdin absent;
  screen block shows the server's `remaining_s`, not the client's; second turn's
  history shows the first turn as a digest with no code; `code: unchanged` when the
  client says so and the previous snapshot exists.
- Persistence: two turns → `GET turns` returns four rows in order; review payload
  carries them; a trailing user turn with no reply is folded into the next request.
- Concurrency: two overlapping POSTs → one 409.
- Refusal: fake client yields `stop_reason: "refusal"` → `error` frame, user turn
  stored, assistant `[refused]`.

Frontend: `useSpeechInput` unit test with a stubbed `SpeechRecognition` (final results
accumulate, settle timer flushes once, pause suppresses, restart on `end`);
`screen-context` builder test (failures named via `testLabels`, details truncated);
`useInterviewer` queue test (events coalesce behind an in-flight turn). Build + lint
in CI as today.

Manual: the Sierra event-streams template end to end with the real key, Chrome, open
mic, TTS on; confirm the mic never captures the synthesized voice.

## 13. Open questions — resolved with the proposed defaults (2026-11-12)

The implementation went ahead on the defaults below; each line says how to change
the choice.

1. **Key location.** Per-user encrypted column **and** `ANTHROPIC_API_KEY` fallback,
   both built. Single-user shortcut: set the env var and ignore the card.
2. **What the interviewer may know.** The whole template including locked parts and
   reference solutions. `INTERVIEWER_KNOWS_SOLUTIONS=false` drops the solutions;
   statements of locked parts stay (that is what lets it pace you).
3. **Voice output.** Browser TTS toggle, off by default (speaker button in the pane).
4. **Mic default.** Off until you pick *Open* or *Push* in the pane; the choice is
   remembered (`localStorage` `interviewer.mic`). Settle timer 1.2 s
   (`useSpeechInput` `settleMs`).
5. **Model.** `claude-sonnet-5-5` at `effort: low`; `INTERVIEWER_MODEL` /
   `INTERVIEWER_EFFORT` switch to Opus or a higher effort.
6. **Agent actions in v1.** None. "Release the next part" stays in §11 *Later*.
7. **SDK coexistence.** Verified: `anthropic` 2.8 + `httpx2` 2.16 installed next to
   `httpx` 0.28; the suite and the Piston path are unaffected.
8. **Multi-replica.** In-process lock; a second replica would not see it. Redis lock
   stays in §11 *Later*.
9. **Transcript on review.** Shown and kept with the session. `DELETE
   …/interviewer/turns` exists (owner or admin) but has no button.
10. **Opening line.** Yes: an `opening` turn fires once on a fresh session with a
    configured key; the model may still answer `[silent]`.
11. **Ask AI.** Still disabled during the session; unchanged on the review page.
