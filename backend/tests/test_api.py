from app.schemas.checkin import CheckInClassification
from app.schemas.profile import ProfileFields
from app.schemas.question import Question, QuestionSetResponse
from app.schemas.roadmap import AIPhaseSpec, AIMilestoneSpec, AITaskSpec, RoadmapPlan
from app.services import checkin_service, goal_service


def _sample_plan() -> RoadmapPlan:
    return RoadmapPlan(
        summary="A staged plan to become a backend developer.",
        phases=[
            AIPhaseSpec(
                title="Python Fundamentals",
                objective="Learn core Python",
                rationale="Everything else depends on this.",
                milestones=[
                    AIMilestoneSpec(
                        title="Syntax and data structures",
                        description="Cover the basics",
                        tasks=[
                            AITaskSpec(title="Learn variables and control flow", importance=0.9, urgency=0.8),
                            AITaskSpec(
                                title="Build a small CLI tool",
                                importance=0.7,
                                urgency=0.5,
                                depends_on_titles=["Learn variables and control flow"],
                            ),
                        ],
                    )
                ],
            )
        ],
    )


def test_create_goal_rejects_empty_title(client):
    response = client.post("/api/goals", json={"title": ""})
    assert response.status_code == 422


def test_create_goal_success(client):
    response = client.post("/api/goals", json={"title": "Become a Python backend developer"})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Become a Python backend developer"
    assert body["status"] == "discovery"


def test_get_missing_goal_returns_404(client):
    response = client.get("/api/goals/999")
    assert response.status_code == 404


def test_full_roadmap_and_task_flow(client, db_session, monkeypatch):
    create_resp = client.post("/api/goals", json={"title": "Become a Python backend developer"})
    goal_id = create_resp.json()["id"]

    monkeypatch.setattr(
        goal_service.ai_service,
        "interpret_profile",
        lambda *a, **k: ProfileFields(goal_category="career", current_level="beginner"),
    )
    profile_resp = client.post(f"/api/goals/{goal_id}/profile")
    assert profile_resp.status_code == 200
    assert profile_resp.json()["profile"]["goal_category"] == "career"

    from app.api import goals as goals_api

    monkeypatch.setattr(goals_api.ai_service, "generate_roadmap", lambda *a, **k: _sample_plan())
    roadmap_resp = client.post(f"/api/goals/{goal_id}/roadmap")
    assert roadmap_resp.status_code == 200
    roadmap_body = roadmap_resp.json()
    assert roadmap_body["overall_progress"] == 0.0
    first_task_id = roadmap_body["phases"][0]["milestones"][0]["tasks"][0]["id"]
    second_task_id = roadmap_body["phases"][0]["milestones"][0]["tasks"][1]["id"]

    # Second task depends on the first, so it cannot be completed yet.
    blocked_resp = client.patch(f"/api/tasks/{second_task_id}", json={"status": "COMPLETED"})
    assert blocked_resp.status_code == 409

    complete_resp = client.patch(f"/api/tasks/{first_task_id}", json={"status": "COMPLETED"})
    assert complete_resp.status_code == 200

    now_unblocked = client.patch(f"/api/tasks/{second_task_id}", json={"status": "COMPLETED"})
    assert now_unblocked.status_code == 200

    final_roadmap = client.get(f"/api/goals/{goal_id}/roadmap")
    assert final_roadmap.json()["overall_progress"] == 100.0


def test_task_update_rejects_invalid_status(client, monkeypatch):
    create_resp = client.post("/api/goals", json={"title": "Become a Python backend developer"})
    goal_id = create_resp.json()["id"]
    monkeypatch.setattr(
        goal_service.ai_service, "interpret_profile", lambda *a, **k: ProfileFields(goal_category="career")
    )
    client.post(f"/api/goals/{goal_id}/profile")

    from app.api import goals as goals_api

    monkeypatch.setattr(goals_api.ai_service, "generate_roadmap", lambda *a, **k: _sample_plan())
    roadmap_body = client.post(f"/api/goals/{goal_id}/roadmap").json()
    task_id = roadmap_body["phases"][0]["milestones"][0]["tasks"][0]["id"]

    response = client.patch(f"/api/tasks/{task_id}", json={"status": "NOT_A_REAL_STATUS"})
    assert response.status_code == 422


def test_questions_endpoint_returns_ai_service_error_as_503(client, monkeypatch):
    create_resp = client.post("/api/goals", json={"title": "Become a Python backend developer"})
    goal_id = create_resp.json()["id"]

    from app.services.ai_service import AIServiceError

    def raise_error(*args, **kwargs):
        raise AIServiceError("boom")

    monkeypatch.setattr(goal_service.ai_service, "generate_questions", raise_error)

    response = client.post(f"/api/goals/{goal_id}/questions")
    assert response.status_code == 503


def test_checkin_flow_marks_completed_task(client, monkeypatch):
    create_resp = client.post("/api/goals", json={"title": "Become a Python backend developer"})
    goal_id = create_resp.json()["id"]
    monkeypatch.setattr(
        goal_service.ai_service, "interpret_profile", lambda *a, **k: ProfileFields(goal_category="career")
    )
    client.post(f"/api/goals/{goal_id}/profile")

    from app.api import goals as goals_api

    monkeypatch.setattr(goals_api.ai_service, "generate_roadmap", lambda *a, **k: _sample_plan())
    client.post(f"/api/goals/{goal_id}/roadmap")

    monkeypatch.setattr(
        checkin_service.ai_service,
        "classify_checkin",
        lambda message, titles: CheckInClassification(
            category="progress",
            summary="Learned the basics",
            completed_task_titles=["Learn variables and control flow"],
        ),
    )
    response = client.post(f"/api/goals/{goal_id}/checkins", json={"message": "I finished the basics."})
    assert response.status_code == 200
    assert response.json()["classification"]["category"] == "progress"


def test_health_check_allows_get_and_head(client):
    assert client.get("/api/health").status_code == 200
    assert client.head("/api/health").status_code == 200
