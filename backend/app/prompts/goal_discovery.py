"""Goal Analyzer + Adaptive Question Generator prompt."""

import json

from app.prompts.context import date_context


def build_questions_prompt(
    goal_title: str,
    goal_description: str,
    known_profile: dict,
    previous_answers: list[dict],
    questions_remaining: int,
    target_date: str = "",
) -> str:
    already_asked = [a.get("question_text", "") for a in previous_answers]
    already_asked_list = "\n".join(f"- {q}" for q in already_asked) or "(none yet)"
    is_first_round = not previous_answers

    return (
        "Goal Analyzer + Question Generator.\n"
        + date_context(target_date)
        + f"Goal title: {goal_title}\nGoal description: {goal_description or '(none)'}\n"
        f"Known profile fields so far (JSON): {json.dumps(known_profile)}\n"
        f"Questions already asked and answered - do NOT ask any of these "
        f"again, and do NOT ask a different phrasing of the same underlying "
        f"topic or metric:\n"
        f"{already_asked_list}\n"
        f"Full previous answers (JSON): {json.dumps(previous_answers)}\n"
        "Generate the next 1-3 highest-value adaptive questions that would "
        "materially change the roadmap for this goal. Only ask about topics "
        "not already covered above, and never ask for something the goal "
        "title, description or target date already states. "
        + (
            "This is the first round: cover the user's current level/experience "
            "and how much time they can realistically commit per week (and the "
            "deadline only if no target date is given). "
            if is_first_round
            else ""
        )
        + "If the goal is vague, first ask what concrete outcome would mean "
        "success for them. You have a hard budget of at most "
        f"{questions_remaining} more questions in total for this entire "
        "interview, so prioritize the few things that would change the plan "
        "the most and set is_complete to true as soon as you have enough to "
        "build a solid roadmap - most goals only need 5-8 questions total. "
        "Once current level, time available, timeframe, constraints and "
        "resources/budget are known, stop - prefer stopping early over "
        "asking one more question. Question style: short, plain language, "
        "one topic per question. Prefer single_choice/multi_choice with 3-5 "
        "distinct, mutually exclusive options (include an 'Other / not sure' "
        "style option where sensible) so answering is fast; use short_text "
        "or long_text only when options cannot capture the answer. "
        "choice questions must always include options; other types must have "
        "an empty options list. 'reason' is one short sentence telling the "
        "user why the answer matters for their plan. Use unique ids like "
        "'q_level'. Infer a goal category if one is not yet known "
        "(e.g. Learning, Career, Fitness, Health, Finance, Business, Creative, "
        "Personal development).\n"
        "Respond as JSON matching this schema: "
        '{"questions": [{"id": str, "text": str, "type": '
        '"single_choice|multi_choice|numeric|date|short_text|long_text", '
        '"options": [str], "required": bool, "reason": str}], '
        '"is_complete": bool, "inferred_category": str}'
    )
