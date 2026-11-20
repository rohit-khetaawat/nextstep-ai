# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Anyone with a goal they don't yet know how to break down: learning a skill, a career move, fitness, personal finance, a habit, a project. They arrive with a broad intention ("become a Python backend developer", "pay off my credit card") and no plan. They come back repeatedly, often briefly, to tick off tasks and report how it's going.

## Product Purpose

NextStep AI turns a broad goal into a personalized, staged roadmap and keeps it current. Success is the user always knowing the single next action, and the plan staying realistic as their situation changes.

## Positioning

The plan is built from a short adaptive interview about this specific person (level, time, budget, constraints) rather than a generic template, and it re-plans itself from plain-language check-ins ("finished X, stuck on Y, less time this week"). Deterministic logic (dependencies, priorities, progress) sits under the AI so the plan stays consistent.

## Operating Context

Core flow: create goal → adaptive interview (1-3 questions per round, up to 12 total) → profile and gap review → roadmap generation (phases → milestones → tasks with effort estimates, dependencies, dates) → dashboard with next best action → task completion and free-text check-ins → roadmap adaptation into a new version.

AI steps take several seconds to tens of seconds each, so waiting states are a normal part of the experience.

## Capabilities and Constraints

- React + Vite + TypeScript frontend, FastAPI backend, Ollama-hosted LLM. Deployed on Netlify (frontend) and Render free tier (backend, may cold-start).
- No accounts: a single shared guest user; goals are addressed by id in the URL.
- Feedback goes to a Google Form (rating 1-5 plus free text); reCAPTCHA protection is planned.
- Undecided: user accounts and a "my goals" list.

## Brand Commitments

- Product name "NextStep AI" is fixed. Everything else (tagline, colors, type) is open.

## Evidence on Hand

No testimonials, user counts, logos or press exist. Do not fabricate any.

## Product Principles

1. The next action is always one glance away.
2. Ask little, plan specifically: every question must change the plan.
3. Honest about the AI: show what it understood and why the plan looks the way it does; make waiting legible.
4. The plan bends, it doesn't break: setbacks are inputs, never failures.

## Accessibility & Inclusion

Target WCAG 2.2 AA. Works on phones (check-ins happen on the go). Respect reduced motion.
