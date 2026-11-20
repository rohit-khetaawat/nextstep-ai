from app.models.goal import GoalAnswer
from app.schemas.goal import GoalCreateRequest
from app.schemas.question import QuestionSetResponse
from app.services import goal_service


def _create_goal(db_session):
    return goal_service.create_goal(db_session, GoalCreateRequest(title="I want to learn cycling"))


def test_discovery_stops_at_cap_without_calling_ai(db_session, monkeypatch):
    """Regression test: the AI's is_complete flag alone must not be trusted -
    once MAX_DISCOVERY_QUESTIONS answers exist, the interview must end
    deterministically without another AI call, no matter what the AI would
    have said. This is what actually broke in production: a goal reached 49
    answers across 17 rounds because nothing capped it."""

    goal = _create_goal(db_session)
    for i in range(goal_service.MAX_DISCOVERY_QUESTIONS):
        db_session.add(
            GoalAnswer(goal_id=goal.id, question_id=f"q{i}", question_text=f"Question {i}", answer_json="\"x\"")
        )
    db_session.commit()
    db_session.refresh(goal)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("AI should not be called once the discovery cap is reached")

    monkeypatch.setattr(goal_service.ai_service, "generate_questions", fail_if_called)

    result = goal_service.get_next_questions(db_session, goal)

    assert result.is_complete is True
    assert result.questions == []


def test_discovery_continues_below_cap_and_passes_remaining_budget(db_session, monkeypatch):
    goal = _create_goal(db_session)
    db_session.add(GoalAnswer(goal_id=goal.id, question_id="q0", question_text="Q0", answer_json="\"x\""))
    db_session.commit()
    db_session.refresh(goal)

    captured = {}

    def fake_generate_questions(**kwargs):
        captured.update(kwargs)
        return QuestionSetResponse(questions=[], is_complete=False)

    monkeypatch.setattr(goal_service.ai_service, "generate_questions", fake_generate_questions)

    goal_service.get_next_questions(db_session, goal)

    assert captured["questions_remaining"] == goal_service.MAX_DISCOVERY_QUESTIONS - 1
