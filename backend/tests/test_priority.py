from app.services.priority_service import dependency_weight, priority_score


def test_priority_increases_with_importance_gap_urgency():
    low = priority_score(0.2, 0.2, 0.2, 0.5)
    high = priority_score(0.9, 0.9, 0.9, 0.5)
    assert high > low


def test_priority_is_bounded_between_zero_and_one():
    score = priority_score(1.0, 1.0, 1.0, 1.0)
    assert 0.0 <= score <= 1.0


def test_blocked_task_gets_minimal_dependency_weight():
    weight = dependency_weight(unblocked_count=5, is_blocked=True, max_unblocked=5)
    assert weight < 0.5


def test_unblocking_more_tasks_increases_weight():
    low = dependency_weight(unblocked_count=0, is_blocked=False, max_unblocked=5)
    high = dependency_weight(unblocked_count=5, is_blocked=False, max_unblocked=5)
    assert high > low
