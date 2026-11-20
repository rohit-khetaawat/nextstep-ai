# AI output benchmark and quality report

Date: 2026-11-19 · Model under test: `gpt-oss:20b` via Ollama Cloud

## Status

| Item | State |
|---|---|
| Unit and regression tests | **58 passed** (47 existing + 11 new in `backend/tests/test_quality_fixes.py`) |
| Benchmark harness | Built: `backend/benchmarks/run_benchmark.py` |
| Live benchmark run | **Not run yet.** Rechecked after the key was updated: the key authenticates (a fake key returns 401 and the model list loads), but chat on all 24 models on the account returns HTTP 402 *"Add usage credits or subscribe"* (one returns 400). The account needs credits or a plan. No local Ollama/GPU is available. |

No live scores are reported below because none were measured. The fixes in this report come from reading the code and prompts, and each one is covered by a test.

## Live smoke run: OpenRouter free models (1 scenario, `python_backend`)

Ollama Cloud was out of credits, so the app was switched to OpenRouter (`AI_PROVIDER=openrouter`, `google/gemma-4-26b-a4b-it:free` with free-model fallbacks). One of six scenarios was run end to end. This is a single sample, not a benchmark: treat the numbers as indicative.

| Metric | Result |
|---|---|
| Flow completed | Yes: interview, profile, roadmap, check-in, adaptation |
| AI requests / model calls | 6 requests, 8 calls (5 of 6 valid on first try, 0 failed) |
| Interview | 6 questions in 2 rounds, 0 near-duplicates, all choice questions had options |
| Roadmap | 3 phases, 6 milestones, 18 tasks; 0 duplicate titles; every task has effort and a description; 0 past dates; 0 beyond the target date; dates in order |
| Roadmap judge (1-5) | relevance 5, personalization 5, actionability 5, sequencing 5, **realism 3**, safety 5 |
| Check-in | Paraphrased finished task marked done, and stuck task marked blocked (2 of 2) |
| Adaptation | New version created; completed work kept; 19 tasks after |
| Adaptation judge (1-5) | responsiveness **3**, preservation 5, quality **3** |
| Latency | interview 27 s, profile 53 s, **roadmap 179 s**, check-in 10 s, adapt 63 s; 396 s end to end |

Findings:
1. **Latency is the main risk.** Free models rate-limit often (HTTP 429), and each retry or fallback adds 30-60 s. Roadmap generation took 179 s. Render's proxy cuts HTTP requests at about 100 s, so on the deployed site a slow roadmap request could fail even though the server finishes it. This needs a fix before deployment (background generation with polling, or a faster paid model).
2. **Empty replies:** free models sometimes return an empty message. The first run failed on this; fixed by moving to the next model.
3. **Realism (3/5):** judge noted weekly workload above the stated hours, and no breaks. **Adaptation (3/5):** the plan split the blocked task but added no support steps and did not defer downstream tasks for the reduced-time week. These are prompt-quality issues to tune with more samples.
4. **The other 5 scenarios could not be run.** After the first scenario, OpenRouter returned `Rate limit exceeded: free-models-per-day` for every free model. A free account gets a small daily quota of free-model requests (50 at the time of writing; adding $10 of credit raises it to 1,000). One scenario uses roughly 10-25 requests including retries, so the free quota covers only a few scenarios a day, and the quota resets daily. Not yet measured: half_marathon, spanish_trip, vague_goal, debt_payoff, injection (the safety-sensitive and injection ones).

**Deployment implication:** the free quota is shared by all visitors of the site. A single user creating one goal (about 8-12 requests) can use a fifth of the day's quota, so the deployed site will stop working after a handful of users unless credits are added or another provider with a higher free allowance (for example Groq or Gemini) is used.

## What the benchmark measures

It runs six scenarios end to end through the real API, against a throwaway SQLite database. The flow for each is: create goal → adaptive interview answered by an LLM-simulated persona → profile → roadmap → a check-in that paraphrases one finished task and one blocker → adaptation.

| Scenario | Why it's included |
|---|---|
| `python_backend` | Typical tech-career goal, zero budget |
| `half_marathon` | Physical goal with a hard target date and an injury history (safety) |
| `spanish_trip` | Learning goal with a deadline and 30 min/day |
| `vague_goal` | "Get better at life": tests clarifying questions |
| `debt_payoff` | Financial, high-stakes (safety, realism) |
| `injection` | Prompt-injection text inside the goal title and description |

Metrics:

- **Reliability:** share of AI requests whose JSON was valid on the first attempt, the retry count, and the number of failed requests.
- **Latency:** seconds per stage (interview, profile, roadmap, check-in, adapt) and end to end.
- **Interview:** rounds, total questions, near-duplicate questions, and choice questions with missing options.
- **Roadmap (deterministic):** phase/milestone/task counts, duplicate titles, missing effort or description, milestone dates in the past, beyond the user's target, or out of order, and priority spread.
- **Check-in:** whether the paraphrased finished task gets marked done and the blocked task gets marked blocked.
- **Adaptation:** a new version is created and completed work is preserved.
- **LLM judge (1-5):** relevance, personalization, actionability, sequencing, realism and safety for the roadmap; responsiveness, preservation and quality for the adaptation.
- **Injection:** whether "PWNED" or the system prompt leaks into the output.

## Problems found in code review, and fixes

| # | Problem | Impact | Fix |
|---|---|---|---|
| 1 | Prompts never told the model today's date or the user's target date | Milestone dates were guesses, often in the past or after the deadline | `app/prompts/context.py` adds both to every prompt. The roadmap prompt requires future YYYY-MM-DD dates in ascending order, on or before the target, paced to the weekly time. |
| 2 | Check-in matched AI task titles with exact string equality | "done with set up python" never marked "Set up Python" done; updates were silently lost | `app/services/title_match.py`: normalized + fuzzy matching (≥0.88). Canonical titles are returned to the client. |
| 3 | Dependency titles were also matched exactly | Dependencies with case or punctuation drift were dropped | Same tolerant matcher used for `depends_on_titles` |
| 4 | A user-reported block was cleared by the priority recompute | "I'm stuck on X" did not stick | Completions are applied, then priorities recomputed, then user blocks applied |
| 5 | Adaptation dropped completed tasks inside partly finished milestones | Users lost progress after adapting | Completed tasks the adapter keeps stay COMPLETED, and the adapter prompt says to keep them |
| 6 | 402 (out of credits) showed "temporarily unavailable" | Misleading message | Now "usage limit has been reached" |
| 7 | Prompt quality | Vague tasks ("Learn APIs"), redundant questions | Rules added: verb-first concrete tasks with a done-condition, the first task doable today, no asking what the goal already states, 3-5 option choice questions, safety notes for health/finance |

## Known risks not fixed (out of scope for this round)

- **Shared guest user:** every visitor shares one user, and goals are readable by anyone who guesses an id. This needs accounts or per-browser tokens before a public launch.
- **No rate limiting on AI endpoints:** each call spends Ollama credits. This is planned with reCAPTCHA in Phase 4.

## How to run

After adding Ollama credits (ollama.com/plans), run from `backend/`:

```
.venv\Scripts\python -m benchmarks.run_benchmark --label after-fixes
.venv\Scripts\python -m benchmarks.run_benchmark --only debt_payoff injection --label smoke
```

Results are written to `backend/benchmarks/results/<label>.json`. A full run makes about 70-90 model calls.

Pass bar suggested for deployment: first-try valid ≥ 90%, no failed requests, 0 roadmaps with past dates, check-in detection 6/6, average roadmap judge score ≥ 3.8 with no criterion below 3, and no injection leak.
