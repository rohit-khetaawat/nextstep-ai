"""Profile Interpreter + Gap Analysis prompt."""

import json

from app.prompts.context import date_context


def build_profile_prompt(goal_title: str, goal_description: str, answers: list[dict], target_date: str = "") -> str:
    return (
        "Profile Interpreter + Gap Analysis.\n"
        + date_context(target_date)
        + f"Goal title: {goal_title}\nGoal description: {goal_description or '(none)'}\n"
        f"Collected answers (JSON): {json.dumps(answers)}\n"
        "Convert these answers into a structured planning profile and "
        "perform a gap analysis comparing the user's current state to "
        "the desired outcome. Use only what the user actually said - do not "
        "invent facts; write 'Not specified' for unknown text fields. "
        "desired_outcome must be concrete and checkable (what success looks "
        "like and by when). time_per_week should be a short normalized "
        "phrase such as '10 hours/week'. List 2-5 gaps, most important first. "
        "Gaps do not need to be numeric; use current_level/required_level "
        "(0-1) only when a meaningful scale applies, otherwise leave them "
        "null and rely on the description.\n"
        "Respond as JSON matching this schema: "
        '{"goal_category": str, "current_level": str, "desired_outcome": str, '
        '"time_per_week": str, "budget_resources": str, "available_tools": str, '
        '"constraints": [str], "preferences": [str], "known_strengths": [str], '
        '"known_weaknesses": [str], "previous_experience": str, '
        '"gaps": [{"area": str, "description": str, "importance": float 0-1, '
        '"current_level": float|null 0-1, "required_level": float|null 0-1}]}'
    )
