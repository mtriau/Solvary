# Sierra (sierra.ai) coding interview problems — candidate reports from Glassdoor, Blind, Reddit, 1point3acres, Exponent/Aced, FrontendLead and personal blogs

Scope note: "Sierra" here means Sierra Technologies, Inc. / sierra.ai (Bret Taylor & Clay Bavor, SF, AI customer-service agents; Glassdoor employer ID 10032095). Sierra Space, Sierra Nevada Corp, Sierra Wireless, SIERA.AI (Glassdoor E1987769) and "Sierra Studio" (Glassdoor E9703551, a Rio de Janeiro posting) were excluded or flagged as unconfirmed.

Source-access caveats (important for the report writer):
- Every Glassdoor domain tried (glassdoor.com / .co.uk / .co.in / .sg / .ca, including the per-question QTN page) returned HTTP 403, so Glassdoor content is known only through search-engine snippets and through aggregator sites (Nora/norahq, Scoutify, Extern) that quote it. Treat those items as "Glassdoor via snippet".
- No Reddit threads about sierra.ai interviews surfaced in any of six Reddit-targeted searches (r/cscareerquestions, r/leetcode, r/ExperiencedDevs, r/csMajors); old.reddit.com cannot be fetched by the tool. The Extern guide mentions r/csMajors "discusses difficulty" without specifics. Net: no first-hand Reddit reports found.
- 1point3acres has 16 Sierra reports (Sept 2025–Oct 2026) but thread bodies are behind login; only titles and one-line summaries were readable.
- No Fishbowl or levels.fyi community posts about Sierra interviews were found.
- Sierra's own April 22, 2026 blog post "The AI-native interview" is first-party and fully readable; it materially changes the loop (coding/algorithms rounds removed), so reports must be read against that date.

---

## Key Question 1: What specific coding problems do candidates say Sierra asked (phone screen, OA, onsite, take-home)?

### Takeaway
The recurring, well-triangulated phone-screen problem (late 2025 – 2026) is a multi-part, practical "call a (mock/flaky) API with pagination → transform/merge the response objects → compact the result to a token budget" exercise on CoderPad with no AI allowed; other first-hand reports name a flaky-call retry/backoff fix, a product-catalog related-items tree traversal, a spreadsheet circular-reference (cycle detection) question, a "merge multiple streams" question, and a header-aware Markdown chunker. The take-home (Agent Engineer track, 2025 – early 2026) is "build a customer-service AI agent for a fictional outdoors company, pick 2 of 5 features, no agent framework, OpenAI key provided", and onsite debugging rounds are "find ~3–6 bugs in a 4–5 file agent codebase (Python or TypeScript/React) with a flowchart/diagram as source of truth".

### Cited Findings

Phone screen / technical screen problems (first-hand unless noted)

- **"Calling an API getting json array and creating a linked list"** — first-hand, OP RuyGuerra (Amazon tag), coding screening, posted Nov 25 2025, follow-ups Jan 2026; rejected within two days. Quote: "I've failed the screening. It wasn't hard though it was calling an API getting json array and creating a linked list." It was a mock API; "you have to know your language well (types etc.) to make sure Json parsing is not artificial making you stuck which was the case for me." — [Blind: "Sierra AI interview process?"](https://www.teamblind.com/post/sierra-ai-interview-process-z4clm77u)
- **"Phone screen is a coding question with multiple parts"** using "an API client the company provides"; parts 2 and 3 "involve transforming a response object"; difficulty "LeetCode Easy and Medium", "most of the time went to getting the code to run"; solved 2 of 3 parts and still passed to onsite; "it's not really leetcode. in my case the recruiter reached out to me." — first-hand, commenter NgBj65 (Amazon tag), Dec 17 2025 — [Blind: "Sierra AI hiring and future!"](https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v)
- **Technical screen example: "calling an API endpoint that fails occasionally but eventually succeeds"**, next part "a product list with fallback IDs that must be resolved into product objects"; each follow-up adds requirements to the existing code; on CoderPad (sometimes screen share); Python or TypeScript expected; "Not LeetCode — it simulates a real scenario you'd encounter working at Sierra." — first-person blog, role "Software Engineer, Agent", undated (process ~2–3 weeks) — [Gaijineer](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- **APX (entry-level/L3) 1-hour live technical in Python, with an agent product engineer; "LLMs were not allowed, but looking up Python syntax was."** Part 1 (debugging): fix Python code that throws a basic error by adding "exponential retries so it keeps trying until the desired functionality is reached" (candidate wrapped the failing call in a retry loop with sleep and async-style timeout). Part 2 (traversal): "Given a merchandise catalog, start from item A and find its related items, then their children"; follow-ups "how would you improve it, and why this approach over others?" (candidate used while+for loops; thought DFS/BFS would have been better). — first-hand, Aced/Exponent, interviewed ~a year before submission (submitted ~7 months before capture, i.e. roughly 2025), outcome "Waiting" — [Aced: Sierra AI APX Interview Experience](https://www.aced.io/experiences/sierra-ai-interview-67fe22)
- **Agent Engineer 1-hour technical screen (LeetCode-style): "Imagine an Excel-style spreadsheet where cells can reference other cells. How would you detect a circular reference?"** Follow-up: "Start with brute force, then optimize if you want." Candidate modeled it as graph cycle detection. — first-hand, Aced/Exponent, interview ~2 years before capture (≈2024), 6-week process, outcome Rejected — [Aced: Sierra AI Agent Engineer Interview Experience](https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc)
- **Staff Agent Engineer phone screen: "Building a paginated list + processing it to merge items."** Advice: handle "fetching every page (cursor/offset) cleanly before the merge step" and clarify "how duplicates should be merged." — first-hand, posted ~2 months before capture (≈mid/late 2026), 8 YOE, outcome not stated — [FrontendLead Discuss: Sierra Agent Engineer Experience](https://frontendlead.com/discuss/t/sierra-agent-engineer-experience/3624)
- **"Phone screen was LC hard for me (one of the easier/well-known ones though)."** — commenter "prattler" (Airbnb tag), Mar 19 (2026), first-hand but company not explicitly restated in the comment — [Blind: "Has anyone heard of Sierra AI?"](https://www.teamblind.com/post/has-anyone-heard-of-sierra-ai-kxr183qo)
- **Phone screen format: "scheduled for 45 min", "the interviewer said we would do coding for 30 minutes and leave 15 min for my questions", "asked a multi part question that wasn't too hard"** — first-person Blind post titled "Weird Sierra interview experience", ~7 months before capture; company shown only as "Sierra" (very likely sierra.ai given the author's other Sierra threads, but unconfirmed) — [Blind alter post](https://www.teamblind.com/alter/evanescer-4frjdcpc)
- **Glassdoor (via snippet): "Implement a keyboard object with expansion to support undo/redo operations"** — listed for a Staff Software Engineer interview at Sierra (employer 10032095); also quoted by Nora's guide as "object-oriented, multi-part" — [Glassdoor question page (403 on fetch)](https://www.glassdoor.co.uk/Interview/Implement-a-keyboard-object-with-expansion-to-support-undo-redo-operations-QTN_8481271.htm); [Nora SWE guide](https://interview.norahq.com/interview-guides/sierra-software-engineer-interview-guide-2026)
- **Glassdoor (via snippet): technical screen was "a standard DSA LC question" / "a standard medium/easy hard LC question"**; aggregate ~3.2/5 difficulty, ~52–56% positive; SWE average 14 days to hire — [Glassdoor Sierra SWE page (403 on fetch)](https://www.glassdoor.co.in/Interview/Sierra-Software-Engineer-Interview-Questions-EI_IE10032095.0,6_KO7,24.htm)
- **1point3acres titles/summaries (first-hand, bodies login-walled):**
  - "Sierra Tech Phone Screen: Handling Markdown File Trunks with Size Limits" — "Managing markdown file chunks under size limits, with previous headers carried into new chunks", full-time SWE, posted 2026-05-15 — [1point3acres thread 1176834](https://www.1point3acres.com/interview/thread/1176834)
  - "sierra Technical Phone Screen Coding Questions for Software Engineer" — "stream processing and merging multiple streams", posted 2026-02-16 — [1point3acres thread 1165332](https://www.1point3acres.com/interview/thread/1165332)
  - "Sierra New Grad Software Engineer Phone Screen Interview" — "a conversation agent, pagination, and token-based compaction", "with no AI tools allowed", posted 2026-10-17 — [1point3acres thread 1193376](https://www.1point3acres.com/interview/thread/1193376)
  - "Sierra Agent Engineer Fulltime Tech Phone Screen Interview Experience", posted 2026-03-10 (no summary) — [1point3acres thread 1168028](https://www.1point3acres.com/interview/thread/1168028)
  - "sierra Technical Phone Screen Experience for Agent Engineering Role", posted 2026-06-24 — [1point3acres listing](https://www.1point3acres.com/interview/company/sierra)
- **PracHub reconstructions of the above (aggregator, unattributed, but they match the 1point3acres summaries closely):**
  - "Fetch Every Page from a Data API, Then Compact Records to a Token Budget" — labelled Sierra / Software Engineer / Technical Screen / Medium, posted Oct 1 2026. Part 1: `fetch_all(fetch_data)` — call `fetch_data(cursor)` repeatedly (first cursor None) until an empty batch; return all records in order; handle repeated cursors/endless empty batches/transient failures. Part 2: `compact(records, trigger=20_000, target=10_000)` — if total tokens > 20,000, keep the longest contiguous run with total ≤ 10,000 (sliding window since tokens are non-negative); worked example `[4000,3000,5000,2000,1000,6000,3000]`. Follow-ups: keep within budget incrementally as records arrive; always keep the most recent record; maximize tokens instead of count; summarize dropped records instead of dropping. — [PracHub](https://prachub.com/interview-questions/fetch-every-page-from-a-data-api-then-compact-records-to-a-token-budget)
  - "Conversation Agent History: Paginated Fetching, Then Token-Limit Compaction" — Sierra / SWE / Technical Screen / Medium, posted Oct 6 2026. "You are building the message-history layer of a conversation agent"; frozen `Message` dataclass (`id, role, text, tokens`); `fetch_page(cursor)` returns a page plus next cursor or None. Part 1: paginate into one ordered list with a clear stop condition, handle empty pages/transient failures/misbehaving cursors, eager vs lazy. Part 2: when total tokens exceed the limit, drop oldest messages until it fits; must be cheap enough to run after every message (running total, O(1) front removal); edge cases: oversized single message, empty history, must-keep messages. Follow-ups: summarize instead of discard; keep tool calls with their results; new messages arriving during pagination; testing without a live service. — [PracHub](https://prachub.com/interview-questions/conversation-agent-history-paginated-fetching-then-token-limit-compaction)
  - "Split Markdown Into Header-Aware Chunks" — Sierra / SWE / Technical Screen / Hard, last updated May 19 2026. `split_markdown(markdown: str, max_size: int) -> list[str]`: split into ordered chunks ≤ max_size; a header is 1–6 `#` + space at column 0; a chunk starting mid-section must be prefixed by all active parent headers (which count toward size); level-L header clears levels ≥ L; greedy packing; `\n`-joined output; constraints len ≤ 200000. — [PracHub](https://prachub.com/coding-questions/split-markdown-into-header-aware-chunks)
  - "Process time intervals and detect overlaps/gaps" — Sierra / Medium, Nov 14 2025: "You are given n time intervals representing debug log segments. Each interval has a start time, an end time, and an associated text message…" with follow-up queries on overlaps and gaps. Matches the 1point3acres OA report "Sierra Software Engineer Online Assessment: Debug View Problem Overview" (posted 2025-11-25): "debug view problem involving time intervals and text sequencing, including follow-up queries on overlaps and gaps". — [PracHub](https://prachub.com/coding-questions/process-time-intervals-and-detect-overlaps-gaps); [1point3acres thread 1155857](https://www.1point3acres.com/interview/thread/1155857)
  - "Fixing a flaky async Python call path with timeouts and exponential-backoff retries" and "Product catalog lookup: item attributes plus a cycle-safe tree of related items" (both May 2026, mislabelled PM) — these mirror the APX account above. — [PracHub Sierra page](https://prachub.com/companies/sierra)
  - "Design an LLM-Powered Customer Service Chat System with Robust Failure Handling" (Aug 1 2026, SWE) — matches the 1point3acres onsite summary "customer service chat system, pub/sub, error handling". — [PracHub](https://prachub.com/interview-questions/design-an-llm-powered-customer-service-chat-system-with-robust-failure-handling)

Online assessment (OA)

- **New-grad SWE OA (posted 2026-10-10): "two easy coding questions, a TypeScript AI coding project, a video reflection, and a next-day interview invite."** — first-hand, body login-walled — [1point3acres thread 1192604](https://www.1point3acres.com/interview/thread/1192604)
- "Sierra Graduate AI Agent Online Assessment Experience and Interview Process" (new grad, 2027 start, posted 2026-09-16) — title only — [1point3acres thread 1189730](https://www.1point3acres.com/interview/thread/1189730)
- Blind user asked "what is the OA like for the apx program" (Nov 10 2025) — unanswered — [Blind](https://www.teamblind.com/post/is-sierra-ai-a-scam-vgp0n56z)

Take-home

- **"Build a customer service AI agent for a fake outdoors company, pick 2 of 5 possible features, and be ready to justify the choices." Written follow-up: "If this ran in production, what metrics would you track, and what observability dashboards would you want?" Tools: OpenAI API, a basic conversation loop, tool calls, "without a larger framework."** — first-hand, Agent Engineer, ≈2024, rejected — [Aced experience](https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc)
- **Take-home: receive an API key and a prompt to "build an agent that carries out different functions"; then a 60-minute onsite presentation where interviewers ask "Why this architecture? Why this approach to tool calling?"** — first-person blog, SWE Agent — [Gaijineer](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- **"Only major downside is that there is a take-home assignment." Cursor use is encouraged.** Onsite round 3 = "Discussion of the take-home, followed by adding a feature." — first-hand, Dec 17 2025 — [Blind](https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v)
- Glassdoor via Nora: "Discuss and extend your take-home assignment during the onsite", "walk through design decisions and trade-offs", estimated 2–4 hours — [Nora SWE guide](https://interview.norahq.com/interview-guides/sierra-software-engineer-interview-guide-2026)
- Glassdoor-snippet item "create a tool calling ai agent capable of cordinating a calendar app" (AI Engineer, Rio de Janeiro, Nov 2025) is attached to the "Sierra Studio" employer page (E9703551), NOT sierra.ai's page — treat as unconfirmed/likely different company — [Glassdoor Sierra Studio (403 on fetch)](https://www.glassdoor.com/Interview/Sierra-Studio-Interview-Questions-E9703551.htm)

Onsite debugging rounds

- **Debugging round: "A codebase of about 4-5 files implementing an agent, plus a diagram. 'The diagram is your source of truth.'" Find and fix ~3 bugs, one scenario at a time, in a CoderPad terminal; discuss optimization if time allows.** — first-person blog — [Gaijineer](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- **APX onsite debugging: "Given a user-journey flowchart, command-line output at each step, and the code, find and fix the bugs." Candidate found ~4 before time ran out; follow-ups: how each bug affects customer experience and why it would be harmful to users.** — first-hand — [Aced APX](https://www.aced.io/experiences/sierra-ai-interview-67fe22)
- **Agent Engineer final round: "Here's prewritten TypeScript and React code with several bugs. Debug and fix it." ~5–6 bugs, two interviewers, started 10–15 min late; candidate asked to use Python and was refused; "pretty much bombed"; cited as reason for rejection. "The big gotcha was a TypeScript and React debugging round that they framed as conceptual even though I think you really do need to know that stack to pass it."** — first-hand, ≈2024 — [Aced Agent Engineer](https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc)
- **Onsite round 1: "Code debugging: several parts, with starter code and known bugs to fix."** — first-hand, Dec 2025 — [Blind](https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v)
- "Sierra Agent Engineering Onsite Debug Round Interview Experience" (posted 2026-05-02): summary says the round covers "logic, design, and agent/LLM-related bugs" — [1point3acres thread 1175298](https://www.1point3acres.com/interview/thread/1175298)
- "Sierra Software Engineer Onsite Interview" (posted 2026-10-14): "customer service chat system, pub/sub, error handling, debugging, and AI coding exercises" — [1point3acres thread 1192971](https://www.1point3acres.com/interview/thread/1192971)
- Sierra first-party (Apr 22 2026): piloting a debugging interview where "Candidates get a medium-sized codebase and a draft PR from a colleague that introduces a cross-cutting feature"; they "pull down the code, inspect output, and iterate with coding agents"; "The level of AI used in this interview is still TBD, as new models can zero-shot many fixes." — [Sierra blog: The AI-native interview](https://sierra.ai/blog/the-ai-native-interview)

Onsite build / presentation

- Sierra first-party: Build = interviewer leaves for 2 hours; candidate uses "the AI tooling and frameworks of their choice", may "pivot or adjust scope as they go"; advice given in advance: "it's OK to cut your scope as you build, and to skip boilerplate (CRUD, auth) to focus on what's unique." Example outputs: "A trivia enthusiast built an AI-powered game meant to keep the user in a state of flow"; "A backend engineer built a headless simulation tool and used an agent with a markdown file to walk through the demo." — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- Presentation round (Agent Engineer, ≈2024): "Walk us through the agent you built and why you made the design choices you made" plus "a short 5 to 10 minute explanation of a technical topic of your choice" (candidate chose RAG); code had already been run from submitted instructions so the demo stayed high level. — [Aced Agent Engineer](https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc)

### Inferences
- The "paginated API fetch → transform/merge → token-budget compaction" problem family is the single most corroborated Sierra phone-screen item: it appears independently in Blind (Dec 2025, "API client… transforming a response object"), FrontendLead (Staff, ≈2026, "paginated list + merge"), 1point3acres (new grad, Oct 2026, "pagination and token-based compaction"), Gaijineer (flaky endpoint → resolve product IDs), and PracHub (two fully-specified variants). It is practical/multi-part, not LeetCode.
- A second corroborated family is "retry/backoff on a flaky call" (APX account; PracHub) and "catalog related-items tree traversal with cycle safety" (APX; PracHub) — again domain-flavoured (commerce/customer-support) rather than abstract.
- The Markdown header-aware chunker (1point3acres May 2026 + PracHub "Hard") and the debug-log interval overlap/gap problem (1point3acres OA Nov 2025 + PracHub) look like RAG-ingestion and observability tasks from Sierra's actual product domain.
- The only clearly LeetCode-style report (spreadsheet cycle detection) is the oldest (≈2024); later reports consistently say "not really leetcode".

### Gaps
- Glassdoor review bodies were unreadable (403 on all domains); the undo/redo keyboard problem's parts, date and outcome are unknown beyond the snippet.
- 1point3acres thread bodies (16 reports, the richest 2025–2026 first-hand corpus) are login-walled; only summaries were captured.
- No first-hand report of the post-April-2026 system-design phone screen content was found (one Blind user said "I just finished their phone interview" on Mar 22 2026 but gave no details).
- No report gives the exact take-home feature list (the "5 possible features") or its time limit.

---

## Key Question 2: What is the loop structure and what does each round test?

### Takeaway
Pre-April-2026 (and still reported for the Agent Engineer / SWE-Agent track through 2026): recruiter screen → 45–60 min practical multi-part CoderPad coding screen (no AI) → take-home agent build → onsite of three ~60-min rounds (debugging; take-home presentation/extension; hiring-manager behavioral). From April 22 2026 Sierra officially replaced the coding phone screen with system design and the onsite coding/algorithms rounds with an AI-native Plan → Build (2 h, any AI tools) → Review loop, plus a piloted debugging round, with the infrastructure track "amended slightly".

### Cited Findings
- **Old loop (first-party):** "Two coding interviews, plus interviews for algorithms, system design, and culture fit, followed by reference checks. The coding phone screen required candidates to write code without AI in an online editor." Signal was "mostly about mechanics: typing syntax, recalling algorithm details, and stitching frameworks together." — [Sierra blog, Apr 22 2026, by Vijay Iyengar, Arya Asemanfar, Angie Wang](https://sierra.ai/blog/the-ai-native-interview)
- **New loop (first-party):** "removed our coding and algorithms interviews and replaced them with an AI-native onsite"; phone screen → system design interview (focus on "getting it into production in a scalable way" rather than "vibe-coding an app"); onsite = Plan (candidate-driven ideation working session) → Build (2 h alone, any AI tooling) → Review (demo; product flows; code review of "data model, abstractions, and extensibility"; path to production; how the candidate used AI); rubric "agnostic to what the candidate builds", shared in advance; interviews run in pairs; screens for "agency" (pivoting when stuck) and "judgment" (scoping). Infrastructure track "amended the interview slightly to better capture the signal we need for infrastructure" (unspecified). — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview); summarized by [Four-Leaf (Sep 10 2026)](https://four-leaf.ai/blog/sierra-interview-process); announced by Bret Taylor on X — [x.com/btaylor](https://x.com/btaylor/status/2046996207898366248)
- **Candidate loop, Dec 2025 (first-hand, passed to onsite):** phone screen (multi-part API coding) → take-home → onsite of 3 rounds in SF or NY: (1) code debugging, several parts, starter code with known bugs; (2) behavioral with hiring manager ("rude and questioned their background"; "passed all rounds except this one, per the recruiter"); (3) take-home discussion then "adding a feature". Travel paid, generous hotel budget; "Most of my interviewers had been there less than a year." — [Blind](https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v)
- **Candidate loop, SWE Agent (first-person blog, ~2–3 weeks):** 30-min recruiter call (asks preferred language) → CoderPad multi-part technical screen → debugging round (4–5 file agent codebase + diagram) → take-home agent + 60-min onsite presentation → 60-min hiring-manager behavioral ("The questions are specific and they dig into details"). — [Gaijineer](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- **Candidate loop, Agent Engineer (≈2024, 6 weeks, rejected):** ~60-min recruiter screen → 1-h LeetCode-style screen → take-home → onsite: TS/React debugging; presentation + technical topic; hiring manager (resume walk, stakeholders, proudest project). "Every interviewer was an agent engineer"; "the role seemed to have a forward-deployed, customer-implementation focus." — [Aced](https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc)
- **Candidate loop, APX (≈2025, 3 weeks):** 30-min third-party recruiter screen ("Why Sierra?", "How do you keep up with AI news?") → 1-h live Python technical (debug + traversal) → onsite: product-heavy debugging (flowchart + CLI output) and product design with head of product ("How would you make an AI agent for a streaming service?", pushback: "Those ideas are already common and Sierra already uses them for customer support"). — [Aced APX](https://www.aced.io/experiences/sierra-ai-interview-67fe22)
- **Candidate loop, new grad SWE (Oct 2026):** OA ("two easy coding questions, a TypeScript AI coding project, a video reflection") → next-day interview invite → phone screen ("conversation agent, pagination, token-based compaction", no AI tools). — [1point3acres 1192604](https://www.1point3acres.com/interview/thread/1192604); [1point3acres 1193376](https://www.1point3acres.com/interview/thread/1193376)
- **Blind, Mar 1 2026 (hearsay):** OP "knows they have an algos interview, which seems harder than coding because syntax is not important" and asks about system design; thread yields no first-hand onsite account; one commenter (Mar 22 2026) "just finished their phone interview" and asked for "insight on the system design interview". — [Blind: Sierra AI Onsite](https://www.teamblind.com/post/sierra-ai-onsite-3l31zi3c)
- **Blind, Oct 2026 (unverified):** "Sierra senior/staff offer?" — "the interview will require lots of prep"; reply "Easy interview." — [Blind](https://www.teamblind.com/post/sierra-seniorstaff-offer-fip4lt7x)
- Aggregator (Aced guide, "verified", undated): recruiter 30 min → 60-min technical screen "single data-structures challenge; no added complexity during the round" → take-home → onsite 3×60 min (TS/React debugging, "historically… without AI coding tools"; agent presentation + technical topic for a non-technical audience; HM behavioral); 2–5 weeks total. — [Aced guide](https://www.aced.io/guides/sierra-agent-engineer-interview)
- Aggregator (Nora, Jul 11 2026): 4–6 rounds over 2–5 weeks; onsite "often in San Francisco"; two undated candidate quotes: "The interview was pretty well thought out, was not super difficult things that you need to study for" (Agent Engineer, accepted offer) and "it was not super difficult but I think a strong product experience shines" (SWE/Agent Developer). — [Nora](https://interview.norahq.com/interview-guides/sierra-software-engineer-interview-guide-2026)
- Glassdoor via snippet: Agent Engineer page has 7 reviews, 3.8/5 difficulty, 75% positive, avg 18 days to hire. — [Glassdoor Agent Engineer (403 on fetch)](https://www.glassdoor.com/Interview/Sierra-Agent-Engineer-Interview-Questions-EI_IE10032095.0,6_KO7,21.htm)
- Blind, Mar 2025 (first-hand but no round detail): "Currently interviewing with them...so far everyone seems sharp"; interviewers "love to sing praises for Clay and Bret". — [Blind: Is Sierra AI a scam?](https://www.teamblind.com/post/is-sierra-ai-a-scam-vgp0n56z)
- 1point3acres title "sierra Recruiter Phone Screen Experience and Unexpected Rejection" (2026-02-27) shows rejections can happen at recruiter stage. — [1point3acres listing](https://www.1point3acres.com/interview/company/sierra)

### Inferences
- Candidate reports from Feb–Oct 2026 (1point3acres phone-screen coding titles, FrontendLead Staff phone screen, Blind "Mar 22 just finished phone interview") suggest the practical coding phone screen persisted for at least some tracks (Agent Engineer, new grad) well after Sierra's April 2026 post; the official post may describe the core/product SWE loop rather than every track.
- The onsite "take-home discussion then add a feature" (Dec 2025) is the precursor of the official Review round's "path to production / extensibility" focus.

### Gaps
- No report describes the content of the new system-design phone screen or the Plan round from a candidate's side.
- No candidate report found for Infra/Platform track specifics (Blind "platform vs agent dev" thread has no interview detail).

---

## Key Question 3: LeetCode-style vs. practical multi-part?

### Takeaway
Overwhelmingly practical and progressive: nearly every 2025–2026 first-hand report describes a multi-part scenario (API client, retries, pagination, merging, compaction, catalog traversal) where later parts extend earlier code, graded on clean extensible code; the only clearly abstract items are the ≈2024 spreadsheet cycle-detection screen and one "LC hard" comment.

### Cited Findings
- "Not LeetCode — it simulates a real scenario you'd encounter working at Sierra"; "each follow-up adds requirements to the existing code"; advice: "Practice writing clean, extensible code and class design, not just algorithms." — [Gaijineer](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- "it's not really leetcode"; "LeetCode Easy and Medium" difficulty; "most of the time went to getting the code to run". — [Blind, Dec 2025](https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v)
- "Prep less for classic LeetCode and more for practical debugging: reading unfamiliar Python, tracing bugs through logs or flowcharts, and explaining customer impact." — [Aced APX](https://www.aced.io/experiences/sierra-ai-interview-67fe22)
- Counter-example: "Prep graph and tree LeetCode problems, since the phone screen was essentially that" (spreadsheet cycle detection, ≈2024). — [Aced Agent Engineer](https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc)
- Counter-example: "Phone screen was LC hard for me (one of the easier/well-known ones though)" (Mar 2026, company not restated). — [Blind](https://www.teamblind.com/post/has-anyone-heard-of-sierra-ai-kxr183qo)
- Glassdoor via snippet: "a standard DSA LC question" in the technical screen. — [Glassdoor SWE page](https://www.glassdoor.co.in/Interview/Sierra-Software-Engineer-Interview-Questions-EI_IE10032095.0,6_KO7,24.htm)
- Sierra's own framing of the old loop: signal was "typing syntax, recalling algorithm details" — the stated reason for removing coding/algorithms rounds. — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)

### Inferences
- Where sources conflict, date explains most of it: ≈2024 reports lean LeetCode, late-2025/2026 reports lean practical, and from April 2026 the official SWE loop has no algorithm round at all.

### Gaps
- The Glassdoor "LC" reviews could not be read, so their dates and roles are unknown.

---

## Key Question 4: Differences by role (SWE, Senior/Staff, Agent Engineer, FDE, MTS, Frontend, Infra, New Grad/Intern/APX)?

### Takeaway
Agent Engineer / "Software Engineer, Agent" (the FDE-like track) has the take-home agent build + presentation and a TypeScript/React-flavoured debugging round; APX and new-grad tracks use a 1-hour Python live technical or an OA (two easy problems + TypeScript AI coding project + video reflection) and product-flavoured debugging; Staff reports (undo/redo keyboard object; paginated list + merge) are the same practical style; Infra is "amended slightly" per Sierra with no candidate detail; Agent Development Strategist is a non-coding onsite with no reports.

### Cited Findings
- Agent Engineer / SWE-Agent: take-home + presentation + TS/React debugging + HM; "Every interviewer was an agent engineer"; role "forward-deployed, customer-implementation focus"; Sierra "primarily works in Python and TypeScript, and they want you to interview in one of those." — [Aced Agent Engineer](https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc); [Gaijineer](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- Role naming: forward-deployed work is hired as "Software Engineer, Agent" / "Agent Engineer"; Blind poster: "mix of building enterprise AI agents and contributing to AI SDK/platform, somewhat similar to FDE" (Jul 2026, YOE 6, TC 450K). — [Blind](https://www.teamblind.com/post/sierra-agent-engineer-prospect-6rhvs21e); [Aced FDE page](https://www.aced.io/jobs/fde/sierra)
- APX (entry-level L3 rotational: PM + coding + customer-facing): 1-h Python technical, no LLMs, syntax lookup OK; onsite product-heavy debugging + product design with head of product. — [Aced APX](https://www.aced.io/experiences/sierra-ai-interview-67fe22)
- New grad SWE (Oct 2026): OA with "two easy coding questions, a TypeScript AI coding project, a video reflection"; phone screen on conversation-agent pagination/compaction with no AI tools. — [1point3acres 1192604](https://www.1point3acres.com/interview/thread/1192604); [1point3acres 1193376](https://www.1point3acres.com/interview/thread/1193376)
- Staff SWE (Glassdoor via snippet): "Implement a keyboard object with expansion to support undo/redo operations". — [Glassdoor QTN](https://www.glassdoor.co.uk/Interview/Implement-a-keyboard-object-with-expansion-to-support-undo-redo-operations-QTN_8481271.htm)
- Staff Agent Engineer phone screen: paginated list + merge. — [FrontendLead](https://frontendlead.com/discuss/t/sierra-agent-engineer-experience/3624)
- Infra: onsite "amended slightly" (first-party, unspecified). — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- Platform vs Agent Dev: a candidate was asked to choose a track; commenters claim "WLB for agent dev is awful. Many try to move over to core product" (hearsay, Mar 2026). — [Blind](https://www.teamblind.com/post/sierra-platform-vs-agent-dev-562s3kqi)
- Agent Development Strategist: two Blind asks (Oct/Nov 2026) about the onsite loop with no answers. — [Blind](https://www.teamblind.com/post/sierra-ai-strategist-4hcz6cpn)
- Senior/Staff offer thread: "Comparable to l6 offer at tier 1 FAANG, lower than OAI ANT" (Databricks commenter, Oct 2026). — [Blind](https://www.teamblind.com/post/sierra-seniorstaff-offer-fip4lt7x)
- Extern internship guide (secondary, projections for 2026–27): "take-home or online" OA, LC medium-hard graph traversal / spreadsheet dependency detection / grid search, onsite coding + AI-agent system design + behavioral on five values — largely recycled from Exponent/Glassdoor, not independent. — [Extern](https://www.extern.com/post/sierra-internship-guide)

### Inferences
- The TypeScript/React debugging round appears specifically in the Agent Engineer track (customer-facing agent code is TS); Python-only candidates have been refused a language switch there.
- "Member of Technical Staff" and "Frontend" titles produced no distinct reports; frontend skill is tested inside the Agent Engineer debugging round rather than as a separate round.

### Gaps
- No first-hand Infra/Platform, MTS, Frontend, or Intern-track interview content found.
- InterviewSense's new-grad page claims (sliding window, hash maps/strings, "scale a notification service") have no attribution and look generated; could not be fetched (403) — not relied upon.

---

## Key Question 5: Difficulty, time pressure, tools, AI policy?

### Takeaway
Screens are 45–60 minutes on CoderPad in Python or TypeScript with no LLM use (syntax lookup allowed), rated easy-to-medium but time-tight because of real I/O plumbing; the take-home encourages Cursor; the post-April-2026 Build round explicitly allows any AI tools for 2 hours; debugging rounds historically ran without AI and the AI-assisted version is a pilot with policy "TBD".

### Cited Findings
- CoderPad (sometimes screen share) for the technical screen; CoderPad terminal for the debugging round; Python or TypeScript. — [Gaijineer](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- "LLMs were not allowed, but looking up Python syntax was" (1-h live technical). — [Aced APX](https://www.aced.io/experiences/sierra-ai-interview-67fe22)
- Phone screen "scheduled for 45 min… coding for 30 minutes and leave 15 min for my questions". — [Blind alter](https://www.teamblind.com/alter/evanescer-4frjdcpc)
- New-grad phone screen "with no AI tools allowed" (Oct 2026). — [1point3acres 1193376](https://www.1point3acres.com/interview/thread/1193376)
- Take-home: "Cursor use is encouraged"; difficulty "not especially difficult for a good fit"; solved 2/3 parts and advanced. — [Blind Dec 2025](https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v)
- Take-home: OpenAI API key provided; no heavy framework expected. — [Aced Agent Engineer](https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc)
- Debugging round language policy: candidate "asked to use Python and was refused" for TS/React debugging; interviewers 10–15 min late; "cold and critical". — [Aced Agent Engineer](https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc)
- Aced guide: debugging round "historically… has run without AI coding tools". — [Aced guide](https://www.aced.io/guides/sierra-agent-engineer-interview)
- Official Build round: 2 hours, "AI tooling and frameworks of their choice"; debugging pilot "level of AI used… still TBD". — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- Glassdoor aggregate difficulty 3.2/5 (all roles) and 3.8/5 (Agent Engineer, 7 reviews). — [Glassdoor](https://www.glassdoor.co.in/Interview/Sierra-Software-Engineer-Interview-Questions-EI_IE10032095.0,6_KO7,24.htm); [Glassdoor Agent Engineer](https://www.glassdoor.com/Interview/Sierra-Agent-Engineer-Interview-Questions-EI_IE10032095.0,6_KO7,21.htm)
- Hiring manager round is the most-cited failure/complaint point: "rude and questioned their background" (Dec 2025); another Blind career-changer reported "a rude hiring manager who questioned their first degree" (search snippet, thread not fetched). — [Blind Dec 2025](https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v)

### Inferences
- Time pressure in the screen comes from I/O and type-handling (JSON parsing, cursors, retries) rather than algorithmic difficulty — two independent first-hand reports (RuyGuerra; NgBj65) say exactly this.

### Gaps
- No report states whether HackerRank/CodeSignal is used for the new-grad OA (platform unknown).
- No candidate report yet on how AI use is judged in the Review round.
