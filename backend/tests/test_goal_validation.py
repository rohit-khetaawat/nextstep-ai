import pytest
from pydantic import ValidationError

from app.schemas.goal import GoalCreateRequest


def test_goal_title_cannot_be_empty():
    with pytest.raises(ValidationError):
        GoalCreateRequest(title="")


def test_goal_title_cannot_be_whitespace_only():
    with pytest.raises(ValidationError):
        GoalCreateRequest(title="   ")


def test_goal_title_too_short_rejected():
    with pytest.raises(ValidationError):
        GoalCreateRequest(title="Hi")


def test_goal_title_is_trimmed():
    goal = GoalCreateRequest(title="  Become a backend developer  ")
    assert goal.title == "Become a backend developer"


def test_valid_goal_accepted():
    goal = GoalCreateRequest(title="Become a Python backend developer", category="career")
    assert goal.category == "career"
