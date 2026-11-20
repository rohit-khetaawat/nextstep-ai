"""Shared date context for prompts.

Models have no reliable notion of "today", so without this every generated
milestone date is a guess (often in the past). Every prompt that produces or
reasons about dates gets today's date and the user's target date.
"""

from datetime import date


def date_context(target_date: str = "", today: date | None = None) -> str:
    today = today or date.today()
    lines = [f"Today's date: {today.isoformat()}."]
    if target_date:
        lines.append(f"The user's target date for this goal: {target_date}.")
    else:
        lines.append("The user has not set a fixed target date.")
    return " ".join(lines) + "\n"
