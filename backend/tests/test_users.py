from app.models.goal import GoalAnswer
from app.models.checkin import CheckIn


def test_create_then_login_case_insensitive(client):
    r = client.post("/api/users", json={"username": "Rohit  K"})
    assert r.status_code == 201
    assert r.json()["username"] == "Rohit K"
    login = client.post("/api/users/login", json={"username": "rohit k"})
    assert login.status_code == 200
    assert login.json()["id"] == r.json()["id"]


def test_duplicate_username_conflicts(client):
    client.post("/api/users", json={"username": "sam"})
    assert client.post("/api/users", json={"username": "SAM"}).status_code == 409


def test_login_unknown_user_404(client):
    assert client.post("/api/users/login", json={"username": "nobody"}).status_code == 404


def test_invalid_usernames_rejected(client):
    assert client.post("/api/users", json={"username": "a"}).status_code == 422
    assert client.post("/api/users", json={"username": "bad<script>"}).status_code == 422


def test_history_is_scoped_to_user(client, db_session):
    a = client.post("/api/users", json={"username": "alice"}).json()
    b = client.post("/api/users", json={"username": "bob"}).json()
    goal = client.post("/api/goals", json={"title": "Learn cooking", "user_id": a["id"]}).json()
    client.post("/api/goals", json={"title": "Run a marathon", "user_id": b["id"]})
    db_session.add(GoalAnswer(goal_id=goal["id"], question_id="q1", question_text="Level?", answer_json='"Beginner"'))
    db_session.add(CheckIn(goal_id=goal["id"], message="Did day one", progress_json='{"completed_task_titles": ["Buy pan"]}'))
    db_session.commit()

    h = client.get(f"/api/users/{a['id']}/history").json()
    assert [g["title"] for g in h["goals"]] == ["Learn cooking"]
    g = h["goals"][0]
    assert g["answers"][0] == {**g["answers"][0], "question": "Level?", "answer": "Beginner"}
    assert g["checkins"][0]["summary"] == "Marked done: Buy pan"


def test_anonymous_goal_does_not_join_a_real_user(client):
    a = client.post("/api/users", json={"username": "alice"}).json()
    client.post("/api/goals", json={"title": "Anonymous goal"})
    assert client.get(f"/api/users/{a['id']}/history").json()["goals"] == []
