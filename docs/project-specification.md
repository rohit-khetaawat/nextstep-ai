# NextStep AI - Master Prompt, Engineering Instructions & Build Specification

> Source: `NextStep_AI_Master_Prompt_and_Development_Instructions.docx`, placed
> here as the authoritative reference for this repository.
>
> **Note:** this original specification names Google Gemini as the AI
> provider. The project has since migrated to [Ollama](https://ollama.com)
> (see the "Migrate Gemini to Ollama" instructions and the current
> [README](../README.md)); every other requirement below - product workflow,
> UI, deterministic logic, data model, structured AI contracts - is unchanged.

## 1. Purpose

This document is the single source of truth for building NextStep AI: product
requirements, architecture, UI requirements, AI behavior, data model,
engineering rules and testing requirements.

## 2. Product Definition

NextStep AI is a goal-to-action planning platform. A user enters a broad
objective - starting a business, beginning a fitness journey, learning a
skill, changing careers, completing a project. The application interviews the
user with adaptive questions, builds a structured profile, identifies gaps and
dependencies, generates a personalized roadmap, and continuously adapts that
roadmap as the user makes progress or reports blockers.

**Core product promise:** The user does not need to know the next step.
NextStep AI helps determine the next sensible step.

## 3. Non-Negotiable Requirements

- Proper interactive web UI - not a terminal-only application.
- Python backend.
- Cloud AI API (Google Gemini via Google AI Studio / the official GenAI Python
  SDK) - no local model execution.
- API keys stay server-side, loaded from environment variables.
- SQLite for the initial persistent database.
- Structured JSON outputs from AI wherever the app needs to parse/act on a
  response.
- Not a generic chatbot - a structured goal-planning workflow.
- Deterministic Python logic for validation, persistence, progress
  calculation, prioritization and dependency handling.
- Polished, responsive, modern UI, usable on desktop and mobile.
- No paid services required for the MVP.

## 4. Technology Stack

Frontend React + Vite + TS · Backend Python + FastAPI · DB SQLite +
SQLAlchemy · AI Google Gemini / GenAI SDK · Validation Pydantic · Config
python-dotenv · Testing pytest · API REST/JSON.

## 5. Product Workflow

Landing → Create Goal → Goal Analysis → Adaptive AI Discovery → Profile
Review → Gap Analysis → Roadmap Generation → Roadmap Dashboard →
Tasks/Milestones/Progress → Check-in → Adaptive Roadmap Update (loop).

## 6. Detailed Functional Requirements

### 6.1 Goal Intake
Prominent goal input, optional target date/timeframe, optional category
(AI can infer), example goals across categories, validation that the goal is
meaningful.

### 6.2 Adaptive Discovery Interview
No fixed giant questionnaire. Generate next question(s) from the goal, known
profile fields and previous answers. Ask only what materially affects the
roadmap. Multiple-choice/numeric/date/short/long text. One question or a
small group at a time. Neutral progress indicator (count is dynamic). Allow
going back to edit an earlier answer. Stop when the profile is sufficiently
complete.

### 6.3 Profile Model
Goal title/description/category, current skill/experience level, desired
outcome, target date/timeframe, time available per week, budget/resources,
available tools/environment, constraints, preferences, known
strengths/weaknesses, previous experience.

### 6.4 Gap Analysis
Compare current vs. desired state; identify missing skills, prerequisites,
resources, habits, actions or milestones. Not every goal has a measurable
skill gap - keep the model flexible. Where numeric levels are meaningful,
`gap = required_level - current_level`; otherwise categorical/qualitative.

### 6.5 Roadmap Generation
Phases in logical order, each with an objective; milestones per phase;
actionable tasks per milestone with estimated effort where reasonable;
dependencies/prerequisites; rationale for important phases; a clear "next
best action"; timelines as estimates, not false precision.

### 6.6 Progress Tracking
Task states: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`. Milestone
state derived from child tasks (or manually adjusted). Overall progress
calculated by Python, never by the AI. Dashboard highlights current milestone
and next recommended action.

### 6.7 Check-ins and Adaptation
User reports what they completed, where they're struggling, or what changed.
AI classifies the check-in (progress / blocker / changed constraint / new
information / other). Python updates deterministic state. AI can propose a
revised future plan. Completed work is not unnecessarily regenerated. Roadmap
versions are stored so changes are traceable.

## 7. UI/UX Requirements

First-class, responsive, desktop-first with good mobile behavior. Clean
hierarchy, generous spacing, readable typography, consistent cards. Restrained
modern color system - avoid excessive gradients/animation. Progress bars,
timeline/phase indicators, milestone badges, clear primary actions. Loading
states for AI calls. Understandable, actionable error states. Disable
duplicate submissions while a request is processing. Confirmation states
after saving/completing. Never expose raw JSON, prompts or internal AI errors.

## 8. Required Screens

Landing · Create Goal · AI Discovery · Profile Review · Roadmap · Dashboard ·
Check-in · Settings.

## 9. Dashboard UX (reference sketch)

```
NextStep AI                                Profile
Goal: Become a Python Backend Developer
Overall Progress                         62%
████████████████████░░░░░░░░
CURRENT PHASE            REST API Fundamentals
NEXT BEST ACTION         Build your first GET endpoint      [ Continue → ]
ROADMAP
✓ Python Fundamentals
✓ OOP & Advanced Python
● REST APIs
○ FastAPI
○ Database Integration
○ Backend Projects
```

## 10. AI Architecture

Specialized responsibilities rather than one giant prompt: Goal Analyzer,
Question Generator, Profile Interpreter, Roadmap Generator, Check-in Analyzer,
Roadmap Adapter.

## 11. Structured AI Contracts

Every AI operation that feeds application logic returns validated structured
JSON (Pydantic). Invalid response → retry once with a correction instruction
→ if still invalid, show a safe error and preserve existing data.

## 12. Master Prompt for Claude Code

See the full master prompt text in the original `.docx` (section 12). Summary
of authoritative requirements, AI behavior, deterministic logic ownership,
priority/dependency logic, UI quality bar, database schema, API surface, AI
service centralization, security rules, MVP definition, testing requirements,
developer experience deliverables, implementation style and the demo
scenario are all reflected in sections 3-19 of this document and in this
repository's implementation.

## 13. Suggested Repository Structure

```
nextstep-ai/
├── backend/
│   ├── app/
│   │   ├── main.py, config.py, database.py
│   │   ├── models/ schemas/ api/
│   │   ├── services/ (gemini_service, goal_service, roadmap_service, progress_service, ...)
│   │   └── core/
│   └── tests/
├── frontend/
│   └── src/ (components/ pages/ services/ hooks/ types/ App.tsx)
├── .env.example
├── .gitignore
├── README.md
└── docs/project-specification.md
```

## 14. Database Schema

`users`, `goals`, `goal_answers`, `roadmaps`, `phases`, `milestones`, `tasks`,
`task_dependencies`, `checkins` (plus `importance`/`urgency`/`gap` columns on
`tasks` added in this implementation to support deterministic priority
recomputation).

## 15. Error Handling Requirements

Gemini timeout → friendly retry, preserve answers. Rate limit → retry-later
message, preserve state. Invalid structured response → validate, retry once,
fail safely. Database failure → log server-side, generic user message.
Network failure → keep page state, allow retry. Missing API key → clear
startup/runtime configuration error, never a raw stack trace.

## 16. Security & Git Rules

`.env.example` with placeholders; `.env` and local DBs gitignored; never
commit a real key; never send the key to the frontend; never log secrets or
raw Authorization headers.

## 17. Demo Script

1. Landing page - explain the problem.
2. Enter "I want to become a Python backend developer."
3. Answer the adaptive questions.
4. Profile review.
5. Generate the roadmap.
6. Dashboard - phases, milestones, next action, progress.
7. Complete a task - watch Python-calculated progress change.
8. Check-in: "I am struggling to understand REST APIs."
9. Roadmap adapts instead of restarting.
10. Explain Gemini, gap/priority logic, dependency ordering, SQLite, API
    architecture.

## 18. Future Enhancements

Calendar integration/scheduling, resource recommendations with web search,
multiple concurrent goals + conflict detection, PDF/Markdown export,
authentication/multi-user, voice input, analytics/trends, goal templates,
richer dependency graphs.

## 19. Final Guidance

Build the simplest complete product that satisfies this specification. Do not
over-engineer the MVP. Success criterion: a smooth end-to-end experience -
vague goal → smart questions → personalized understanding → structured
roadmap → actionable next step → progress → adaptation.
