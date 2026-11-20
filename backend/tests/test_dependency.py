import pytest

from app.services.dependency_service import (
    CycleDetectedError,
    has_cycle,
    is_blocked,
    topological_order,
    unblocked_counts,
    validate_edges,
)


def test_validate_edges_rejects_unknown_task():
    with pytest.raises(ValueError):
        validate_edges({1, 2}, [(1, 99)])


def test_validate_edges_rejects_self_dependency():
    with pytest.raises(ValueError):
        validate_edges({1}, [(1, 1)])


def test_has_cycle_detects_simple_cycle():
    assert has_cycle({1, 2, 3}, [(1, 2), (2, 3), (3, 1)]) is True


def test_has_cycle_false_for_dag():
    assert has_cycle({1, 2, 3}, [(2, 1), (3, 2)]) is False


def test_topological_order_respects_dependencies():
    # task 2 depends on 1, task 3 depends on 2
    order = topological_order({1, 2, 3}, [(2, 1), (3, 2)])
    assert order.index(1) < order.index(2) < order.index(3)


def test_topological_order_raises_on_cycle():
    with pytest.raises(CycleDetectedError):
        topological_order({1, 2}, [(1, 2), (2, 1)])


def test_unblocked_counts_counts_dependents():
    counts = unblocked_counts({1, 2, 3}, [(2, 1), (3, 1)])
    assert counts[1] == 2


def test_is_blocked_true_when_prerequisite_incomplete():
    assert is_blocked(2, [(2, 1)], completed_ids=set()) is True


def test_is_blocked_false_when_prerequisite_complete():
    assert is_blocked(2, [(2, 1)], completed_ids={1}) is False
