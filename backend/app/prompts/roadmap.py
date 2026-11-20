"""Roadmap Generator + Roadmap Adapter prompts."""

import json

from app.prompts.context import date_context

_ROADMAP_SCHEMA = (
    '{"summary": str, "phases": [{"title": str, "objective": str, '
    '"rationale": str, "milestones": [{"title": str, "description": str, '
    '"target_date": "YYYY-MM-DD", "tasks": [{"title": str, "description": str, '
    '"estimated_effort": str, "importance": float 0-1, "urgency": float 0-1, '
    '"depends_on_titles": [str]}]}]}]}'
)

_SIZE_LIMITS = (
    "To keep the response compact and syntactically valid: use 2-4 phases, "
    "1-2 milestones per phase, and 2-3 tasks per milestone."
)

_QUALITY_RULES = (
    "Quality rules:\n"
    "- Dates: every milestone target_date is a real calendar date in "
    "YYYY-MM-DD format, after today, in ascending order, and on or before "
    "the user's target date if one is given. Space them according to the "
    "user's weekly time - do not compress the plan unrealistically.\n"
    "- Workload: the total estimated effort between milestones must fit "
    "the user's stated time per week.\n"
    "- Tasks are concrete actions with a visible result, starting with a "
    "verb (e.g. 'Build a CRUD REST API for a to-do app with FastAPI', not "
    "'Learn APIs'). The description says exactly what to do and how the "
    "user knows it is done; name a specific free resource or method when "
    "useful, respecting the user's budget.\n"
    "- The very first task must be small enough to start today.\n"
    "- Every task title is unique. depends_on_titles must copy titles of "
    "EARLIER tasks exactly, character for character.\n"
    "- importance/urgency should vary between tasks to reflect real "
    "priority; do not give every task the same values.\n"
    "- Personalize: reflect the user's level, constraints, preferences and "
    "budget from the profile, and mention them in phase rationales.\n"
    "- For health, fitness, medical, legal or financial goals, include a "
    "brief, specific safety note where relevant (e.g. warm-up and rest "
    "days, consulting a professional) without refusing to help.\n"
    "- summary: 2-3 sentences describing the overall strategy and timeline."
)


def build_roadmap_prompt(goal_title: str, goal_description: str, profile: dict, target_date: str = "") -> str:
    return (
        "Roadmap Generator.\n"
        + date_context(target_date)
        + f"Goal title: {goal_title}\nGoal description: {goal_description or '(none)'}\n"
        f"Structured profile (JSON): {json.dumps(profile)}\n"
        "Generate a staged roadmap of phases in logical order. Each phase "
        "needs an objective and a short rationale explaining why it "
        "matters for this specific user. Each phase contains milestones; "
        "each milestone contains actionable tasks with an estimated_effort "
        "string (e.g. '2 hours', '3 sessions of 45 min'), an importance "
        "(0-1) and urgency (0-1) score, and optional depends_on_titles. "
        "Avoid impossible precision - use estimates.\n"
        f"{_QUALITY_RULES}\n{_SIZE_LIMITS}\n"
        f"Respond as JSON matching this schema: {_ROADMAP_SCHEMA}"
    )


def build_adapt_prompt(
    goal_title: str,
    profile: dict,
    classification: dict,
    remaining_roadmap: dict,
    target_date: str = "",
    completed_task_titles: list[str] | None = None,
) -> str:
    completed = completed_task_titles or []
    return (
        "Roadmap Adapter.\n"
        + date_context(target_date)
        + f"Goal title: {goal_title}\nProfile (JSON): {json.dumps(profile)}\n"
        f"Latest check-in (JSON): {json.dumps(classification)}\n"
        f"Tasks the user has already completed (JSON): {json.dumps(completed)}\n"
        f"Remaining (not-yet-completed) roadmap structure (JSON): {json.dumps(remaining_roadmap)}\n"
        "Return the revised REMAINING plan only: it replaces the remaining "
        "structure above. Tasks in it with status COMPLETED must stay in "
        "their milestone with their exact title (they stay marked done); "
        "never add a new task that repeats completed work. Keep remaining "
        "tasks that are still appropriate, using their exact titles, and "
        "keep their order unless the check-in "
        "gives a reason to change it. Respond directly to the check-in: if "
        "the user is blocked, insert one or two smaller preparatory or "
        "unblocking tasks immediately before the blocked task and make the "
        "blocked task more manageable (e.g. split it); if they have less "
        "time, reduce the workload and push dates later; if they are ahead, "
        "you may pull work forward. Do not rewrite unrelated parts of the "
        "plan. The summary must explain in 1-2 sentences, addressed to the "
        "user, what changed and why.\n"
        f"{_QUALITY_RULES}\n{_SIZE_LIMITS}\n"
        f"Respond as JSON matching this schema: {_ROADMAP_SCHEMA}"
    )
