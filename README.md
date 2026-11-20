# NextStep AI

A goal-to-action planning platform. You enter a broad goal ("become a Python
backend developer"), the app interviews you with adaptive questions, builds a
structured profile, identifies gaps, generates a personalized roadmap of
phases/milestones/tasks, tracks your progress, and adapts the plan as you
check in with progress or blockers.

Full product/engineering specification: [docs/project-specification.md](docs/project-specification.md).

## Architecture

- **Backend**: Python + FastAPI + SQLAlchemy + SQLite. All AI calls go through
  a single `app/services/ai_service.py` module (system instruction, prompt
  templates in `app/prompts/`, structured JSON output validated with Pydantic,
  one retry on an invalid response). Deterministic logic - validation,
  persistence, progress calculation, priority scoring, dependency-cycle
  detection/topological ordering - lives in Python, never in the LLM.
- **Frontend**: React + Vite + TypeScript. Talks to the backend over REST/JSON.
- **AI provider**: [Ollama](https://ollama.com) via the official `ollama`
  Python client - either a local Ollama install or Ollama Cloud. The API key
  (Cloud only) and endpoint live server-side only and are never sent to the
  frontend.

```
nextAI/
├── backend/        FastAPI app, services, tests
├── frontend/        React + Vite + TS app
├── docs/            Product specification
└── .env.example
```

## Prerequisites

- Python 3.11+
- Node.js 18+ / npm
- Ollama access - either:
  - a local Ollama install ([ollama.com/download](https://ollama.com/download)) with a model pulled (e.g. `ollama pull gpt-oss:20b`), or
  - an [Ollama Cloud](https://ollama.com) account and API key (requires internet access)

## Setup

1. Copy the environment file and add your Ollama configuration:

   ```bash
   cp .env.example backend/.env
   ```

   Edit `backend/.env`:
   - **Local Ollama**: set `OLLAMA_BASE_URL=http://localhost:11434` and leave
     `OLLAMA_API_KEY` blank.
   - **Ollama Cloud**: set `OLLAMA_BASE_URL=https://ollama.com` and
     `OLLAMA_API_KEY=<your key>`.
   - Set `OLLAMA_MODEL` to a model available on your endpoint (e.g. `gpt-oss:20b`).

   Never commit this file - it's already covered by `.gitignore`.

2. Backend:

   ```bash
   cd backend
   python -m venv .venv
   .venv/Scripts/activate   # Windows; use `source .venv/bin/activate` on macOS/Linux
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

   The database schema (SQLite, `backend/nextstep.db`) is created
   automatically on startup - no separate migration step for the MVP.

3. Frontend (in a second terminal):

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   Open http://localhost:5173. The frontend expects the API at
   `http://localhost:8000` by default; override with a `VITE_API_URL` env var
   if needed.

If Ollama isn't configured or reachable, the backend still starts (so you can
inspect the API and DB), but any endpoint that calls the AI service returns a
friendly 503 instead of a raw error.

### Troubleshooting

| Symptom | Likely cause |
|---|---|
| `The AI service credentials are not configured correctly.` | Missing/invalid `OLLAMA_API_KEY` for Ollama Cloud, or `OLLAMA_BASE_URL` unset. |
| `The configured AI model is unavailable.` | `OLLAMA_MODEL` isn't pulled locally (`ollama pull <model>`) or isn't available on your Cloud account. |
| `We couldn't connect to the AI service.` | Local Ollama isn't running (`ollama serve`), or `OLLAMA_BASE_URL` is wrong. |
| Backend log: `OLLAMA_BASE_URL is not set` | `backend/.env` is missing or wasn't loaded - confirm the file exists at `backend/.env`, not the repo root. |

## Running tests

```bash
cd backend
.venv/Scripts/activate
python -m pytest
```

Tests mock all AI calls - none of them require a live Ollama endpoint or
network access. They cover goal validation, AI response schema
validation/retry, Ollama error mapping (auth/model/connection failures),
progress calculation, priority scoring, dependency cycle detection, task
status transitions, roadmap persistence, and API error handling.

## Sample goal for demonstration

> "I want to become a Python backend developer."
>
> Beginner Python, ~7 hours/week, 6-month timeframe, limited project
> experience.

Walk through: create the goal → answer the adaptive questions → review the
generated profile → generate the roadmap → open the dashboard (phases,
milestones, next action, progress) → mark a task complete and watch progress
recalculate → submit a check-in like "I'm struggling to understand REST
APIs" → adapt the roadmap and see the future phases revise without losing
completed work.

## API summary

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/goals` | Create a goal |
| GET | `/api/goals/{id}` | Read a goal + its profile |
| POST | `/api/goals/{id}/questions` | Get the next adaptive question(s) |
| POST | `/api/goals/{id}/answers` | Submit answers to the current questions |
| POST | `/api/goals/{id}/profile` | Interpret answers into a structured profile |
| POST | `/api/goals/{id}/roadmap` | Generate a roadmap from the profile |
| GET | `/api/goals/{id}/roadmap` | Read the active roadmap (with computed progress) |
| PATCH | `/api/tasks/{id}` | Update a task's status |
| POST | `/api/goals/{id}/checkins` | Submit a check-in; AI classifies it |
| POST | `/api/goals/{id}/adapt` | Adapt the future roadmap from the latest check-in |

## Notable design decisions

- **Priority scoring** (`app/services/priority_service.py`):
  `priority = importance × gap × urgency × dependency_weight`, each factor in
  `[0, 1]`. `dependency_weight` is near-zero while a task is blocked and rises
  with how many other tasks it unblocks once available, so priorities update
  automatically as dependencies clear.
- **Dependencies** (`app/services/dependency_service.py`): stored as directed
  edges `(task_id → depends_on_task_id)`. Cycle detection runs before a
  roadmap is persisted; the API also rejects starting/completing a task whose
  prerequisites aren't done (`409 Conflict`).
- **Adaptation**: `POST /api/goals/{id}/adapt` copies fully-completed phases
  into a new roadmap version untouched, sends only the remaining structure to
  the Roadmap Adapter, and appends its revised phases - so completed work is
  never regenerated, and roadmap history stays traceable via `version`.
- **AI provider abstraction**: the rest of the codebase calls
  `ai_service.generate_questions()`, `.interpret_profile()`,
  `.generate_roadmap()`, `.classify_checkin()`, `.adapt_roadmap()` and never
  imports the Ollama client directly - swapping providers means changing
  `app/services/ai_service.py` alone.
