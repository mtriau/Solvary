# Sierra (sierra.ai) engineering interview: official picture + candidate/employee accounts outside the big review sites

Scope: Sierra Technologies, Inc. / sierra.ai (Bret Taylor + Clay Bavor, SF, founded 2023). Sierra Space, Sierra Nevada Corp, Sierra Studio, SIERA.AI (Austin) etc. were excluded. Glassdoor entries were deliberately not used (big review site); Blind is included once, flagged, because it is the only account that names the AI tool permitted on the take-home. Research date: 2026-11-04.

Provenance legend used below: **[OFFICIAL]** = Sierra-authored; **[FIRST-HAND]** = the writer says they personally interviewed; **[HEARSAY/GUIDE]** = third-party prep site compiling reports; **[SNIPPET-ONLY]** = text seen only in a search-engine snippet, page itself not openable.

---

## KQ1. What does Sierra itself say about its engineering interview (format, philosophy, rounds, AI tools, Agent Engineer vs Software Engineer tracks)?

### Takeaway
Sierra published a first-party description of its loop on 22 Apr 2026 ("The AI-native interview", by Vijay Iyengar, Arya Asemanfar, Angie Wang): the coding phone screen became a system-design screen, the two coding + algorithms onsite rounds were removed and replaced by a three-phase "AI-native onsite" (Plan → 2-hour solo Build with any AI tooling → Review), and a debugging round (review/improve a colleague's draft PR on a medium codebase, with coding agents) is in pilot. Bret Taylor amplified it the same day; Sierra's careers page separately states interviews are in person at an office and assess values alignment. Sierra has not published a separate "Agent Engineer" loop; the official role is titled "Software Engineer, Agent".

### Cited Findings

**The official blog post (primary source)**
- Post: "The AI-native interview", Sierra blog, 22 Apr 2026, authors Vijay Iyengar, Arya Asemanfar, Angie Wang. [OFFICIAL] — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview); author page confirms date — [Vijay Iyengar author page](https://sierra.ai/author/vijay-iyengar)
- Old loop described in the post: "two coding interviews, plus algorithms, system design, and culture-fit interviews, followed by reference checks"; the coding phone screen was "written without AI in an online editor". Authors say the signal was "mostly about mechanics, such as typing syntax, recalling algorithms, and assembling frameworks" and that in debriefs hiring managers "leaned more on referrals and prior experience when the interview signal was unclear." — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- Design goals stated: representative of daily work, high-signal about strengths and gaps, positive candidate experience. — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- Phone screen: replaced with a **system design interview**. Rationale quote: "vibe-coding an app is easy"; "The harder, more relevant, problem is getting it into production in a scalable way." — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- Onsite: "We removed our coding and algorithms interviews and replaced them with an AI-native onsite." Three phases:
  - **Plan**: working session; candidate defines a product "in their own domain", drives ideation, interviewers probe to strengthen the idea. No duration stated.
  - **Build**: interviewer leaves; candidate builds for "2 hours, using the AI tooling and frameworks of their choice"; may pivot or cut scope freely; "OK to cut your scope as you build, and to skip boilerplate (CRUD, auth) to focus on what's unique."
  - **Review**: candidate demos; panel discusses product flows/choices, reviews code (data model, abstractions, extensibility), discusses path to production, and "We also dig into how they used AI along the way." No duration stated. — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview); corroborated by [four-leaf.ai summary](https://four-leaf.ai/blog/sierra-interview-process)
- Evaluation mechanics: evaluation criteria and advice are **shared with candidates in advance**; criteria are "agnostic to what the candidate builds"; interviews are "run in pairs" for calibration; signals named are agency (does the candidate pivot when stuck), judgment (scoping within time limits), and technical judgment in code review. Debriefs shifted from yes/no to "where would this person thrive, and how do we support them?" — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- **Debugging interview (pilot)**: "candidates get a medium-sized codebase and a colleague's draft PR that adds a cross-cutting feature"; they "review and improve it, pulling down the code, inspecting output, and iterating with coding agents"; "the level of AI used in this interview is still TBD" because new models can zero-shot many fixes. Purpose: the onsite tests 0→1 product building but not taking a feature "from 1 to N in an existing, messy codebase." — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- **Infrastructure roles**: same format applies ("infrastructure engineers increasingly build full-stack tools and agents"), interview "slightly amended" to capture infra signal; the post does not say how. — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- Example builds cited by Sierra: a trivia enthusiast built "an AI-powered game meant to keep the user in a state of flow"; a backend engineer built "a headless simulation tool and used an agent with a markdown file to walk through the demo." — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- Candidate feedback: every candidate is asked for feedback; "many said it was the most fun they'd had in an interview." Acknowledged challenge: open-ended format is harder to standardize. Lesson: "We're hiring for strengths, not just an absence of weakness." Scoping maxim attributed to Paul Buchheit: "if it's great, it doesn't have to be good." — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- The post names **no specific AI tool** (only "AI tooling and frameworks of their choice"). — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)

**Founder / author amplification on X**
- Bret Taylor, 22 Apr 2026 16:55 UTC: "As coding agents have become the standard for developing software, we've transformed Sierra's engineering interview process to be AI-native. We've documented our lessons here, and very curious how others in the industry are navigating" + link to the post. No thread; 27 quote-tweets counted. [OFFICIAL] — [X post](https://x.com/btaylor/status/2046996207898366248) (text via fxtwitter API; x.com itself returned HTTP 402/451)
- Vijay Iyengar (bio: "Engineering & Research @SierraPlatform"), 11 May 2026 18:52 UTC: "AMA! 2 weeks ago, we posted about Sierra's AI-native interview process. Many eng leaders have reached out asking questions and sharing that they're evolving their processes too. Wanted to answer some of the most common questions we've gotten to help teams evolving their interview. If you have more questions, just drop them in the 🧵". JSON shows 3 replies, 1 quote; reply bodies were not retrievable. [OFFICIAL] — [X post](https://x.com/vijayiyengar/status/2053911107254075782)

**Employee LinkedIn amplification** [SNIPPET-ONLY — LinkedIn pages not openable]
- Katharine Chow (Sierra) reposted: the team "revamped our interview from the ground up to be AI-native"; "during the onsite, we pair with candidates to plan a project, they build it from scratch, and we conclude with a product/technical review", crediting Arya Asemanfar, Angie Wang and others. — [LinkedIn profile](https://www.linkedin.com/in/katharinegchow/)
- Arya Asemanfar and Andrew Yeung (Sierra) also reposted the article. — [Asemanfar](https://www.linkedin.com/in/asemanfar/), [Yeung](https://www.linkedin.com/in/yeungandrew/)
- Outside reaction (Elliot van Huijgevoort, Alarm.com): the authors "broke down how interviewing needs to change to better assess talent across what matters more today (agency, judgement, product thinking), rather than coding ability." — [LinkedIn profile](https://www.linkedin.com/in/elliot-van-huijgevoort/)
- RecOps Collective newsletter (week of 25 May 2026) listed the post as a "guide" under industry news, with no commentary. — [RecOps Roundup](https://recops.substack.com/p/week-of-may-25th-2026)

**Hacker News**
- Submitted twice, both with zero comments: objectID 47867043 (22 Apr 2026, 4 points) and 48230970 (22 May 2026, 2 points, by mooreds). No HN comment hits for "sierra interview take-home". — [HN Algolia](https://hn.algolia.com/api/v1/search?query=sierra%20ai-native%20interview&tags=story)

**Careers page / early-career page** [OFFICIAL]
- Careers page: "our approach to hiring is grounded in the belief that excellence is about more than just functional expertise"; "we'll evaluate not only your capabilities, but also how well you align with our values"; "Since we work in person, interviews take place at one of our offices." — [sierra.ai/careers](https://sierra.ai/careers)
- Values (About page): Trust, Customer Obsession, Craftsmanship ("We get the details right, from the words on the page to the system architecture."), Intensity ("When we fail, we talk about it openly and without blame…"), Family ("We strive to be the best technology company for parents."). — [sierra.ai/about](https://sierra.ai/about)
- Early-career program page lists a 4-stage process: Apply ("Submit your resume") → Technical assessment ("Demonstrate how you think and solve problems") → Meet the team ("Meet future teammates and collaborate on real-world scenarios") → Decision ("Fast feedback and next steps"); goal "to gain an understanding of how you think, build, and collaborate." Internships are 12–16 weeks, paid, for 2028 grads; New Grad roles for 2027 grads. No AI policy or round detail stated. — [sierra.ai/early-career-program](https://sierra.ai/early-career-program)

**Role tracks** [OFFICIAL]
- Careers page job families (Nov 2026): *Agent Engineering* — "Software Engineer, Agent" (SF, NY, Atlanta, London, Madrid, Paris, Munich, Toronto, Sydney, South Korea, Tokyo) plus vertical variants (Financial Services, Healthcare, Insurance, Public Sector, Retail, TMT, Travel) and language variants (Arabic, Brazilian Portuguese, Dutch, French, German, Italian, Spanish, Mandarin), "Engineering Manager, Agent", "Healthcare Integrations Architect". *Platform Engineering* (SF) — Agent Builder, Agent Runtime, Channels and Experiences, Cloud Infrastructure, Context Engine, Horizon, Inference, Infrastructure, Insights, Payments Infrastructure, Platform, Product, Security, SRE, Admin Experience, Research Engineer (Applied Research), "Deployed Infrastructure Engineer" (SF/NY), Web Developer. *Early Career* — Software Engineer, Agent (New Grad 2027) in SF/NY/Singapore/London; APX (New Grad 2027); interns Summer 2027 SF/NY/Singapore and London 2027. — [sierra.ai/careers](https://sierra.ai/careers)
- Sierra's own definition of the Agent Engineer (Natalie Meurer, 11 Jul 2024): "Agent engineers need to be strong software engineers, but their role differs from other engineering roles in key ways"; "AI agents are nondeterministic and built on tools uncommon in modern software stacks"; skills sought: SWE fundamentals, modern AI stack (frontier LLMs, vector DBs, prompt engineering, tool-calling/Reflexion-style architectures, orchestration incl. Sierra's Agent SDK), "innate curiosity and respect for the complexity of their customers' challenges", and "non-traditional experiences are not a prerequisite for success". No interview description. — [Meet the AI agent engineer](https://sierra.ai/blog/meet-the-ai-agent-engineer)
- Aggregated JD text for "Software Engineer, Agent": partner with customers to build and ship agents handling "thousands of daily conversations"; own the Agent Development Life Cycle "from initial pilot through deployment and continuous iteration"; stack named React, TypeScript, Go, LLM/RAG tooling; 5–7+ yrs experience; AI/LLM experience "a plus"; US base ranges reported $180K–$390K. [HEARSAY — aggregator copies of the Ashby JD] — [tealhq JD](https://www.tealhq.com/job/software-engineer-agent_3c2c11c5-8336-436d-81ee-527f6faf560c), [zerogtalent](https://zerogtalent.com/blog/career-opportunities-at-sierra-ai)
- Bret Taylor on Latent Space (ep. "The AI Architect", Feb 2025): "We are growing the team and we're hiring software engineers, agent engineers… send me a note, Bret at Sierra dot AI"; "Our engineering team is exclusively in person in San Francisco, though we do have some kind of forward deployed engineers… and other offices like London." Also: "There's a lot of power in combining product and engineering into as few people as possible." No interview-format discussion. [OFFICIAL, founder statement] — [Latent Space](https://www.latent.space/p/bret)
- Bret Taylor on Cheeky Pint #27 (10 Mar 2026, host John Collison): on the "product engineer" profile, "Finding someone with good taste, that's relatively easy. Finding someone who also understands your customers extremely well, the nuances of the problem they're solving" is harder. No passage on the interview process itself in the available transcript. — [Cheeky Pint transcript](https://cheekypint.transistor.fm/27/transcript)

### Inferences
- The official loop as of Apr 2026, for a generic Software Engineer: recruiter screen (not described in the post but universally reported) → system-design phone screen → in-person onsite with Plan/Build(2h)/Review → debugging-PR round (pilot) → hiring manager/values → references. The post is explicit that AI is allowed throughout Build and is itself an evaluated dimension in Review.
- Sierra's "Agent Engineer" is not a separate interview track in official material; "Software Engineer, Agent" is the forward-deployed/customer-facing title and candidate reports (KQ2) show a take-home agent build + TS/React debugging flavor for that track, while the Apr 2026 post is written from the platform-engineering side (authors are engineering/research leads). Whether the Plan/Build/Review onsite has fully replaced the agent-track take-home is not confirmed by Sierra.
- Bret Taylor's and Vijay Iyengar's posts are amplification only; the blog post is the sole substantive official text.

### Gaps
- The replies/answers in Vijay Iyengar's 11 May 2026 AMA thread could not be retrieved (x.com returned 402/451; fxtwitter JSON contained no reply text).
- Sierra does not state durations for Plan or Review, which AI tools are permitted/provided, whether candidates use their own laptop, or the exact "slight amendment" for infrastructure roles.
- No official statement found on the recruiter screen, hiring-manager round, reference checks post-redesign, or whether the agent-track take-home still exists.
- LinkedIn post bodies could only be seen as search snippets.

---

## KQ2. What concrete coding exercises, take-homes, or "build a demo agent" tasks have candidates/employees described?

### Takeaway
Pre-redesign (2024–early 2026) accounts converge on: (a) a CoderPad screen that is a multi-part, progressively-extended practical problem (call a flaky API with retries → paginate → transform JSON → resolve fallback product IDs), with a LeetCode-style variant (detect circular references in a spreadsheet) reported for Agent Engineer; (b) a take-home "build a customer-service agent for a fictional company (one report: an outdoors retailer), pick 2 of 5 features, API key provided, no framework expected", presented and extended in a 60-min onsite; (c) a ~60-min debugging round on a 4–5-file agent codebase with ~3 planted bugs and a diagram as source of truth, or a TypeScript/React app with 5–6 bugs. Post-redesign, the only concrete format is Sierra's own Plan/Build/Review description plus the "draft PR on a medium codebase" debugging pilot.

### Cited Findings

**First-hand: gaijineer.co — "Sierra Software Engineer, Agent Interview Experience"** [FIRST-HAND; undated, process ~2–3 weeks; outcome not stated]
- Recruiter call (30 min): background, why Sierra, AI startup vs big company; "Sierra primarily works in Python and TypeScript, and they want you to interview in one of those." — [gaijineer.co](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- Technical screen on **CoderPad**, "sometimes with screen sharing"; "practical multi-part problem that builds progressively", not LeetCode. Problem: call an API endpoint that fails occasionally but eventually succeeds (retry); then the response contains a product list with fallback IDs; iterate through the list and resolve each product's eventual set of IDs into product objects; "each follow-up adds new requirements on top of your existing code." — [gaijineer.co](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- Debugging round: "surprisingly fun"; small codebase (~4–5 files) implementing an agent plus a diagram; "The diagram is your source of truth"; run the agent in the CoderPad terminal; interviewer describes a scenario per part; ~3 bugs; optimization questions if time remains. — [gaijineer.co](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- Agent building: take-home — candidate "receives an API key and a prompt to build an agent that carries out different functions"; onsite 60-min presentation with many "why" questions ("Why this architecture? Why this approach to tool calling?"). — [gaijineer.co](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- Hiring manager (60 min): behavioral on agency and collaboration; "The questions are specific and they dig into details." Advice: "If you're a Java or C++ person, you'll want to get comfortable in Python or TS before the process starts"; focus on "practical coding, class design". — [gaijineer.co](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)

**First-hand: Exponent/aced.io candidate reports** [FIRST-HAND, anonymous; dates only relative]
- Agent Engineer, US, 6-week process, rejected (listed "2 years ago", so ~2024): Recruiter screen 60 min (strongest in Python, no TypeScript). Technical screen 1 hr "LeetCode-style": "Imagine an Excel-style spreadsheet where cells can reference other cells" — detect circular references (graph cycle detection); brute force acceptable to start. **Take-home: "Build a customer service AI agent for a fake outdoors company, pick 2 of 5 possible features to implement, and be ready to justify your choices."** Candidate built a basic OpenAI-API tool-calling loop, no framework. Follow-up: "If this were running in production, what metrics would you track and what observability dashboards would you want?" Onsite round 1: "Here's some prewritten TypeScript and React code with several bugs in it. Can you debug and fix it?" ~5–6 bugs; request to use Python refused; two interviewers; "I pretty much bombed this round." Onsite round 2: walk through the agent (interviewers had already run the submitted code) + "a short 5 to 10 minute explanation of a technical topic of your choice" (candidate chose RAG). Onsite round 3: HM behavioral (resume walk, stakeholder work). Candidate attributes rejection to the debugging round. — [aced.io (ex-Exponent)](https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc)
- AI Engineer Senior/L5, US, ~2 weeks, rejected, "Difficult": recruiter screen ("Why do you want to work at Sierra?"); technical: "Implement pagination for an API to retrieve all results. Then do some computation with the JSON response." Tip: practice "API calls, error handling, retries, and pagination, plus JSON data wrangling." "the team has a very high bar and is a lot of self starters." — [aced.io](https://www.aced.io/experiences/sierra-ai-senior-ai-engineer-interview-087f4e)
- AI Engineer, US, in progress, "Difficult": recruiter screen; technical: "Implement chatbot compaction logic" (candidate ran short on time); take-home: "Build an agent chatbot." "Very friendly, they genuinely want you to succeed." — [aced.io](https://www.aced.io/experiences/sierra-ai-ai-engineer-interview-a7267d)
- Forward Deployed Engineer L4, US, 4 weeks, "Very difficult", waiting: recruiter asked "How do you use AI on a regular basis?"; **take-home (written/system-design flavored): "Metric X for our AI agent is down. How would you diagnose the issue?"** — which data sources to check, what fixes to build, how to prioritize; final round: "What are the north star success metrics for an AI agent for a healthcare financial platform?" "They really do abide by their values." — [aced.io](https://www.aced.io/experiences/sierra-ai-forward-deployed-engineer-interview-99c71f)

**First-hand: Blind thread "Sierra AI hiring and future!"** [FIRST-HAND, anonymous; Blind is a review site, included because it is the only source naming the permitted AI tool]
- Commenter NgBj65 (Amazon), 17 Dec 2025: phone screen was a multi-part coding question "connecting to an API via a client that they provide", parts 2–3 transform the response ("LC Easy and Medium, respectively"); "not really leetcode"; **"there is a take-home assignment but you are encouraged to use Cursor for it"**; onsite in SF or NY, three rounds: (1) code debugging — "they provide you with a lot of starter code and there are a few bugs they tell you about", (2) HM behavioral, (3) take-home discussion then add an extra feature. Passed all but the HM round; base "in the low 200's" plus options. — [Blind](https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v)

**Other first-hand (paywalled / not openable)**
- singdev.fyi story #10: Software Engineer, Agent, mid-level 3 YOE, interviewed Jan–Mar 2026, outcome "failed_final", est. TC >250k; only the recruiter call (30 min, motivation/why switch) is visible before the paywall. — [singdev.fyi](https://singdev.fyi/stories/10)
- Taro listed a "Software Engineer, San Francisco, October 1 2025, no offer, negative" experience; page returned 404. — [jointaro.com](https://www.jointaro.com/interviews/companies/sierra/experiences/software-engineer-san-francisco-california-october-1-2025-no-offer-negative-efd8c622)

**Secondary guides (compile the above; some add unattributed detail)** [HEARSAY/GUIDE]
- vibeengines.com (updated 22 Oct 2026): take-home is "Build an agent for a fictional client's support use case that performs several functions"; API key provided; "a feature list to prioritize"; written questions on observability and metrics; interviewers "look for a loop that calls tools directly, without relying on an agent framework"; deadline/language not stated. Also relays Sierra's Plan advice as "Bring two ideas, each with a user, a workflow, and a definition of done" (not in Sierra's post; guide's own). Key line: "do you actually understand how an agent works, or do you import one?" — [vibeengines](https://vibeengines.com/handbook/fde-interview-sierra)
- aced.io guide (2026): rounds = recruiter 30 min → technical screen 60 min (one DS problem) → take-home (fictional-client support agent, prioritize features) → onsite 3×60 min in person (TS/React debugging; agent presentation + explain a technical topic to a non-technical audience; HM behavioral). Historically "the debugging round ran without AI coding tools". Timeline 2–5 weeks; technical screen can come a month+ after recruiter call. Does **not** mention a "paid async work sample" despite search snippets attributing one to Exponent. — [aced.io guide](https://www.aced.io/guides/sierra-agent-engineer-interview)
- prachub.com (4 Sep 2026): cites an InterviewDB account of "a CoderPad technical round with no AI assistance" and an Exponent account of "a live coding round with no LLMs, but syntax lookup was allowed"; debugging-pilot reports mention "Python/TypeScript, flowcharts, command-line output, and customer-impact questions". The InterviewDB entry itself was not found. — [prachub](https://prachub.com/resources/sierra-ai-native-software-engineer-interview-guide-2026-agentic-coding-product-framing-and-build-review)
- GitHub ombharatiya/AI-Engineer-Interview-Questions (sierra.md, "Last reviewed: October 2026"): explicitly says its 13 questions are "synthesised" from public focus areas, not recalled; no real problems; describes debugging as "React/TS flavor for Agent Engineer tracks" and onsites "in person". Cites Sierra's blog, gaijineer, Exponent. — [GitHub](https://github.com/ombharatiya/AI-Engineer-Interview-Questions/blob/main/14-company-interview-questions/sierra.md)
- extern.com internship guide (Aug 2026): new-grad technical assessment question types reported as "graph traversal, dependency detection in Excel-like spreadsheets, and grid search, at LeetCode medium-to-hard"; onsite system-design example "design an agent for a streaming service"; sourced from Exponent/Glassdoor; projections of Oct–Dec 2026 onsites are the author's. — [extern.com](https://www.extern.com/post/sierra-internship-guide)
- four-leaf.ai (10 Sep 2026, updated 2 Nov 2026) cites only Sierra's post, no candidate reports. — [four-leaf.ai](https://four-leaf.ai/blog/sierra-interview-process)
- Search snippet from a Glassdoor-derived summary (not opened): a Rio de Janeiro candidate described ~7 steps with "live coding… about building ai agents without a framework only using open ai sdk." [SNIPPET-ONLY] — [search result referencing glassdoor.ca](https://www.glassdoor.ca/Interview/SIERA-AI-Interview-Questions-E1987769.htm) (note: that URL is the unrelated SIERA.AI; the Rio snippet's origin page was not confirmed)

### Inferences
- The "flaky API → paginate → transform → resolve fallback IDs" CoderPad problem is reported independently by gaijineer, Blind (NgBj65), and the L5 aced.io report ("pagination… then computation on the JSON"), so it is the best-attested pre-redesign screen; the "spreadsheet circular reference" problem is attested by one first-hand report (~2024) and may be an older Agent Engineer variant.
- The take-home is consistently a customer-service agent for a fictional company with a feature menu; the "fake outdoors company / pick 2 of 5" detail is single-source. "No framework" is a guide inference from candidates who used raw OpenAI tool-calling; Sierra does not publish such a rule.
- No candidate account yet describes going through the Apr 2026 Plan/Build/Review onsite in detail; all detailed first-hand reports predate or straddle the redesign. The Jan–Mar 2026 singdev story is the most likely to describe the transition but is paywalled.

### Gaps
- No GitHub repo/gist reconstructing a Sierra take-home or CoderPad problem was found (searches for "sierra take-home", "sierra.ai challenge" returned only prep sites).
- No YouTube/podcast segment where a Sierra engineer walks through an interview exercise was found.
- Take-home deadline, submission format, language, and whether it is paid are unconfirmed (one search snippet claims "paid take-home"; no opened page says so).
- The exact five features in the take-home menu and the three agent-codebase bugs are not described anywhere.

---

## KQ3. Are there known prep guides sent by Sierra recruiters, and what do they tell candidates to expect?

### Takeaway
No recruiter prep email or PDF has been posted publicly. The only official statement is that Sierra shares "evaluation criteria and advice" with candidates ahead of the AI-native onsite; candidates report the recruiter explains the full process upfront and sets the Python/TypeScript expectation.

### Cited Findings
- Sierra: for the AI-native onsite, "Evaluation criteria and advice are shared in advance" and candidates are told it is fine to cut scope and skip boilerplate. [OFFICIAL] — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- gaijineer: "the process was explained clearly upfront" by the recruiter; recruiter asks preferred language and wants Python or TypeScript. [FIRST-HAND] — [gaijineer.co](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- aced.io guide: recruiter screen covers "preferred languages (Python or TypeScript), and salary range"; guide advises confirming AI rules with the recruiter. [GUIDE] — [aced.io](https://www.aced.io/guides/sierra-agent-engineer-interview)
- four-leaf.ai recommends asking the recruiter "about the debugging pilot, its AI rules, and infrastructure amendments" — i.e., the guide itself has no recruiter material. [GUIDE] — [four-leaf.ai](https://four-leaf.ai/blog/sierra-interview-process)
- Blind NgBj65: recruiter said candidates are "encouraged to use Cursor" for the take-home. [FIRST-HAND] — [Blind](https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v)

### Inferences
- The advance "criteria and advice" document that Sierra says it sends is the de-facto prep guide, but nobody has leaked or reproduced it.

### Gaps
- No copy or paraphrase of Sierra's advance criteria/advice document was found on LinkedIn, X, GitHub, or blogs.

---

## KQ4. What interview tools are used (CoderPad, HackerRank, CodeSignal, own IDE, Cursor, screen-share)?

### Takeaway
CoderPad (editor + terminal) for the pre-redesign screen and debugging round; screen-share for take-home review; Cursor explicitly encouraged for the take-home (one report); AI tooling of the candidate's choice during the 2-hour Build; AI rules for the debugging pilot "still TBD". No reports of HackerRank or CodeSignal.

### Cited Findings
- CoderPad for the technical screen, "sometimes with screen sharing"; debugging round run "in the CoderPad terminal". [FIRST-HAND] — [gaijineer.co](https://gaijineer.co/sierra-software-engineer-agent-interview-experience)
- Old coding phone screen was "written without AI in an online editor". [OFFICIAL] — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- Build phase: "the AI tooling and frameworks of their choice"; Review examines "how they used AI along the way"; debugging pilot uses "coding agents" but "the level of AI used in this interview is still TBD". [OFFICIAL] — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- "you are encouraged to use Cursor" for the take-home. [FIRST-HAND] — [Blind](https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v)
- Take-home review: interviewers had already run the submitted code; discussion via screen share; debugging round required TypeScript/React, Python refused. [FIRST-HAND] — [aced.io](https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc)
- Live coding round with "no LLMs, but syntax lookup was allowed" (Exponent account relayed by prachub); "CoderPad technical round with no AI assistance" (InterviewDB account relayed by prachub). [HEARSAY] — [prachub](https://prachub.com/resources/sierra-ai-native-software-engineer-interview-guide-2026-agentic-coding-product-framing-and-build-review)
- Take-home built against an OpenAI API key with tool calling. [FIRST-HAND aced.io; GUIDE vibeengines] — [aced.io](https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc), [vibeengines](https://vibeengines.com/handbook/fde-interview-sierra)
- Interviews are in person at a Sierra office (SF or NY for US candidates). [OFFICIAL careers page; FIRST-HAND Blind] — [sierra.ai/careers](https://sierra.ai/careers), [Blind](https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v)

### Inferences
- Tooling split by era: no-AI CoderPad for the old screen/debugging; AI-permitted for take-home and the new Build; the new debugging pilot is the one round where Sierra is still deciding the AI policy.

### Gaps
- Whether candidates use their own laptop/IDE during the 2-hour Build, or a Sierra-provisioned machine, is not stated anywhere.
- No source names the system-design screen tool (whiteboard vs. Excalidraw etc.).

---

## KQ5. Any reports on Sierra's "work trial", paid project, or onsite "build day" formats?

### Takeaway
Sierra's official "build day" is the 2-hour solo Build inside the AI-native onsite; there is no evidence of a multi-day work trial. A "paid take-home / paid async work sample" is mentioned only in search snippets attributed to Exponent, and the Exponent/aced guide itself does not say the take-home is paid.

### Cited Findings
- Onsite Build is 2 hours solo, interviewer leaves, then demo + review. [OFFICIAL] — [Sierra blog](https://sierra.ai/blog/the-ai-native-interview)
- Onsite "take-home discussion, then add an extra feature" live. [FIRST-HAND] — [Blind](https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v)
- Search snippets claim "candidates receive a paid take-home assignment: build a customer service agent" and "a paid async work sample"; the aced.io guide page does not contain either phrase. [SNIPPET-ONLY, unverified] — [aced.io guide](https://www.aced.io/guides/sierra-agent-engineer-interview)
- Internships are the only paid "trial"-like arrangement Sierra advertises (12–16 weeks, paid, full-time). [OFFICIAL] — [sierra.ai/early-career-program](https://sierra.ai/early-career-program)

### Inferences
- "Work trial" at Sierra is best read as the in-onsite 2-hour build plus the pre-onsite take-home; no evidence of paid multi-day trials of the kind used by some other AI startups.

### Gaps
- Whether the take-home is compensated could not be confirmed from any opened page.
- No first-hand account of the post-April-2026 onsite (what people built, how long Plan/Review ran, whether laptops were provided) was found.

---

## Source index (date, URL, provenance)

| Date | Source | Type |
|---|---|---|
| 2026-04-22 | https://sierra.ai/blog/the-ai-native-interview | OFFICIAL (primary) |
| 2026-04-22 | https://x.com/btaylor/status/2046996207898366248 | OFFICIAL (founder) |
| 2026-05-11 | https://x.com/vijayiyengar/status/2053911107254075782 | OFFICIAL (author AMA; replies unavailable) |
| 2026-11 (checked) | https://sierra.ai/careers | OFFICIAL |
| 2026-11 (checked) | https://sierra.ai/early-career-program | OFFICIAL |
| 2026-11 (checked) | https://sierra.ai/about | OFFICIAL (values) |
| 2024-07-11 | https://sierra.ai/blog/meet-the-ai-agent-engineer | OFFICIAL (role definition) |
| 2025-02 | https://www.latent.space/p/bret | OFFICIAL (founder, hiring remarks) |
| 2026-03-10 | https://cheekypint.transistor.fm/27/transcript | OFFICIAL (founder, taste/product engineers) |
| 2026-04-22 / 05-22 | HN 47867043, 48230970 | 0 comments |
| undated (2025–26) | https://gaijineer.co/sierra-software-engineer-agent-interview-experience | FIRST-HAND |
| ~2024 | https://www.aced.io/experiences/sierra-ai-machine-learning-engineer-interview-8549fc | FIRST-HAND |
| undated | https://www.aced.io/experiences/sierra-ai-senior-ai-engineer-interview-087f4e | FIRST-HAND |
| undated | https://www.aced.io/experiences/sierra-ai-ai-engineer-interview-a7267d | FIRST-HAND |
| undated | https://www.aced.io/experiences/sierra-ai-forward-deployed-engineer-interview-99c71f | FIRST-HAND |
| 2025-12-17 | https://www.teamblind.com/post/sierra-ai-hiring-and-future-peb5ne2v | FIRST-HAND (review-site) |
| 2026 Jan–Mar | https://singdev.fyi/stories/10 | FIRST-HAND (paywalled) |
| 2026-10-22 | https://vibeengines.com/handbook/fde-interview-sierra | GUIDE |
| 2026 | https://www.aced.io/guides/sierra-agent-engineer-interview | GUIDE |
| 2026-09-04 | https://prachub.com/resources/sierra-ai-native-software-engineer-interview-guide-2026-agentic-coding-product-framing-and-build-review | GUIDE |
| 2026-09-10 | https://four-leaf.ai/blog/sierra-interview-process | GUIDE |
| 2026-10 | https://github.com/ombharatiya/AI-Engineer-Interview-Questions/blob/main/14-company-interview-questions/sierra.md | GUIDE (synthesized Qs) |
| 2026-08-03 | https://www.extern.com/post/sierra-internship-guide | GUIDE |
| 2026-05-25 | https://recops.substack.com/p/week-of-may-25th-2026 | newsletter mention |
