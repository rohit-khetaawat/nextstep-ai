"""Tolerant matching of AI-returned task titles against real task titles.

The model is told to copy titles verbatim, but in practice it changes case,
punctuation or a word here and there. An exact-string comparison then
silently drops check-in updates and dependency edges, so match on a
normalized form first and fall back to a strict similarity threshold.
"""

import re
from difflib import SequenceMatcher

_FUZZY_THRESHOLD = 0.88


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def match_title(candidate: str, titles: list[str]) -> str | None:
    """Return the title from `titles` that `candidate` refers to, or None."""

    if not candidate or not titles:
        return None
    if candidate in titles:
        return candidate

    norm = normalize_title(candidate)
    if not norm:
        return None
    by_norm = {normalize_title(t): t for t in titles}
    if norm in by_norm:
        return by_norm[norm]

    best_title, best_score = None, 0.0
    for t_norm, title in by_norm.items():
        score = SequenceMatcher(None, norm, t_norm).ratio()
        if score > best_score:
            best_title, best_score = title, score
    return best_title if best_score >= _FUZZY_THRESHOLD else None
