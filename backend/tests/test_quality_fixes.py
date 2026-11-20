"""Regression tests for the AI-output robustness fixes: tolerant title
matching, user-reported blocks surviving a check-in, completed work surviving
adaptation, date grounding in prompts, and the 402 error message."""

from datetime import date

import ollama
import pytest

from app.models.goal import Goal
from app.prompts import build_adapt_prompt, build_questions_prompt, build_roadmap_prompt
from app.schemas.checkin import CheckInClassification
from app.schemas.roadmap import AIMilestoneSpec, AIPhaseSpec, AITaskSpec, RoadmapPlan
from app.services import checkin_service, roadmap_service
from app.services.ai_service import AIService, AIServiceError
from app.services.goal_service import get_or_create_default_user
from app.services.title_match import match_title

TITLES = ["Set up Python and VS Code", "Build a CRUD REST API with FastAPI", "Write unit tests with pytest"]


@pytest.mark.parametrize(
    "candidate,expected",
    [
        ("Build a CRUD REST API with FastAPI", "Build a CRUD REST API with FastAPI"),
        ("build a crud rest api with fastapi", "Build a CRUD REST API with FastAPI"),
        ("Set up Python & VS Code.", "Set up Python and VS Code"),
        ("Write unit test with pytest", "Write unit tests with pytest"),
        ("Deploy to production", None),
        ("", None),
    ],
)
def test_match_title(candidate, expected):
    assert match_title(candidate, TITLES) == expected


def _goal_with_roadmap(db_session, plan: RoadmapPlan):
    user = get_or_create_default_user(db_session)
    goal = Goal(user_id=user.id, title="Become a backend developer", profile_json='{"gaps": []}')
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    roadmap = roadmap_service.build_roadmap_from_plan(db_session, goal, plan, version=1)
    return goal, roadmap


def _plan(dep_title: str = "Set up Python and VS Code") -> RoadmapPlan:
    return RoadmapPlan(
        summary="plan",
        phases=[
            AIPhaseSpec(
                title="Foundations",
                milestones=[
                    AIMilestoneSpec(
                        title="First API",
                        tasks=[
                            AITaskSpec(title=TITLES[0], importance=0.9, urgency=0.9),
                            AITaskSpec(title=TITLES[1], importance=0.8, urgency=0.6, depends_on_titles=[dep_title]),
                            AITaskSpec(title=TITLES[2], importance=0.6, urgency=0.4),
                        ],
                    )
                ],
            )
        ],
    )


def _statuses(roadmap):
    return {t.title: t.status for p in roadmap.phases for m in p.milestones for t in m.tasks}


def test_dependency_with_case_drift_is_still_linked(db_session):
    _, roadmap = _goal_with_roadmap(db_session, _plan(dep_title="set up python and vs code"))
    tasks = {t.title: t for p in roadmap.phases for m in p.milestones for t in m.tasks}
    # The dependent task is blocked because its (fuzzily matched) prerequisite is open.
    assert tasks[TITLES[1]].status == "BLOCKED"


def test_checkin_matches_paraphrased_titles_and_keeps_user_block(db_session, monkeypatch):
    goal, roadmap = _goal_with_roadmap(db_session, _plan())
    monkeypatch.setattr(
        checkin_service.ai_service,
        "classify_checkin",
        lambda message, titles: CheckInClassification(
            category="blocker",
            completed_task_titles=["set up python and vs code"],
            blocked_task_titles=["Write unit test with pytest"],
            should_adapt_roadmap=True,
        ),
    )

    _, classification = checkin_service.create_checkin(db_session, goal, "done with setup, stuck on tests")
    db_session.refresh(roadmap)
    statuses = _statuses(roadmap)

    assert statuses[TITLES[0]] == "COMPLETED"
    # Unblocked by the completed prerequisite.
    assert statuses[TITLES[1]] == "NOT_STARTED"
    # User-reported block survives the priority recomputation.
    assert statuses[TITLES[2]] == "BLOCKED"
    assert classification.completed_task_titles == [TITLES[0]]
    assert classification.blocked_task_titles == [TITLES[2]]


def test_adaptation_keeps_completed_task_inside_revised_milestone(db_session):
    goal, roadmap = _goal_with_roadmap(db_session, _plan())
    for p in roadmap.phases:
        for m in p.milestones:
            for t in m.tasks:
                if t.title == TITLES[0]:
                    t.status = "COMPLETED"
    db_session.commit()
    db_session.refresh(roadmap)

    adapt_plan = RoadmapPlan(
        summary="Added a smaller step before the API.",
        phases=[
            AIPhaseSpec(
                title="Foundations",
                milestones=[
                    AIMilestoneSpec(
                        title="First API",
                        tasks=[
                            AITaskSpec(title="set up python and VS Code"),
                            AITaskSpec(title="Follow the FastAPI tutorial's first 3 chapters"),
                            AITaskSpec(title=TITLES[1]),
                        ],
                    )
                ],
            )
        ],
    )
    new_roadmap = roadmap_service.apply_adaptation(db_session, goal, roadmap, adapt_plan, version=2)
    statuses = _statuses(new_roadmap)

    assert statuses["set up python and VS Code"] == "COMPLETED"
    assert statuses["Follow the FastAPI tutorial's first 3 chapters"] == "NOT_STARTED"


def test_prompts_include_today_and_target_date():
    today = date.today().isoformat()
    prompts = [
        build_questions_prompt("Run a half marathon", "", {}, [], 12, target_date="2027-04-15"),
        build_roadmap_prompt("Run a half marathon", "", {}, target_date="2027-04-15"),
        build_adapt_prompt("Run a half marathon", {}, {}, {"phases": []}, target_date="2027-04-15"),
    ]
    for prompt in prompts:
        assert today in prompt
        assert "2027-04-15" in prompt


def test_payment_required_error_has_clear_message(monkeypatch):
    service = AIService()

    class FakeClient:
        def chat(self, **kwargs):
            raise ollama.ResponseError("Add usage credits", 402)

    monkeypatch.setattr(service, "_get_client", lambda: FakeClient())
    with pytest.raises(AIServiceError, match="usage limit"):
        service._call_model("prompt")


@pytest.mark.parametrize(
    "given,expected",
    [
        ("postgres://u:p@h/db", "postgresql+psycopg2://u:p@h/db"),
        ("postgresql://u:p@h/db?sslmode=require", "postgresql+psycopg2://u:p@h/db?sslmode=require"),
        ("postgresql+psycopg2://u:p@h/db", "postgresql+psycopg2://u:p@h/db"),
        ("sqlite:///x.db", "sqlite:///x.db"),
    ],
)
def test_database_url_is_normalised_for_hosted_postgres(given, expected):
    from app.config import Settings

    assert Settings(database_url=given).sqlalchemy_database_url == expected
