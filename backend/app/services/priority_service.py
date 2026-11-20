"""Deterministic task priority scoring.

priority_score = importance * gap * urgency * dependency_weight

All factors are normalized to [0, 1] so the final score is also in [0, 1]
and comparable across tasks. dependency_weight rewards tasks that unblock
more future work (more outgoing dependents) and are not themselves blocked.
"""

MIN_FACTOR = 0.05  # avoid a single zero factor collapsing the whole score to 0


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def dependency_weight(unblocked_count: int, is_blocked: bool, max_unblocked: int) -> float:
    """Higher when a task unlocks more future work; near-zero while blocked."""

    if is_blocked:
        return MIN_FACTOR
    if max_unblocked <= 0:
        return 0.5
    return _clamp(0.5 + 0.5 * (unblocked_count / max_unblocked))


def priority_score(importance: float, gap: float, urgency: float, dep_weight: float) -> float:
    importance = max(MIN_FACTOR, _clamp(importance))
    gap = max(MIN_FACTOR, _clamp(gap))
    urgency = max(MIN_FACTOR, _clamp(urgency))
    dep_weight = max(MIN_FACTOR, _clamp(dep_weight))
    raw = importance * gap * urgency * dep_weight
    # Normalize against the maximum possible product (1.0) - already in range,
    # but re-clamp defensively against floating point drift.
    return round(_clamp(raw), 4)
