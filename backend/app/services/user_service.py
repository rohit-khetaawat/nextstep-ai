import json

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import HistoryAnswer, HistoryCheckIn, HistoryGoal
from app.services import roadmap_service


def find_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(func.lower(User.name) == username.lower()).first()


def create_user(db: Session, username: str) -> User | None:
    """Returns None when the username is already taken (case-insensitive)."""
    if find_by_username(db, username) is not None:
        return None
    user = User(name=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _answer_text(raw: str) -> str:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    return ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)


def build_history(db: Session, user: User) -> list[HistoryGoal]:
    goals = sorted(user.goals, key=lambda g: g.created_at, reverse=True)
    result = []
    for goal in goals:
        result.append(
            HistoryGoal(
                id=goal.id,
                title=goal.title,
                status=goal.status,
                has_roadmap=roadmap_service.get_active_roadmap(db, goal.id) is not None,
                created_at=goal.created_at.isoformat(),
                answers=[
                    HistoryAnswer(
                        question=a.question_text,
                        answer=_answer_text(a.answer_json),
                        created_at=a.created_at.isoformat(),
                    )
                    for a in sorted(goal.answers, key=lambda a: a.id)
                ],
                checkins=[
                    HistoryCheckIn(
                        message=c.message,
                        summary=_checkin_summary(c),
                        created_at=c.created_at.isoformat(),
                    )
                    for c in sorted(goal.checkins, key=lambda c: c.id)
                ],
            )
        )
    return result


def _checkin_summary(checkin) -> str:
    try:
        progress = json.loads(checkin.progress_json or "{}")
        blockers = json.loads(checkin.blockers_json or "{}")
    except json.JSONDecodeError:
        return ""
    parts = []
    if progress.get("completed_task_titles"):
        parts.append("Marked done: " + ", ".join(progress["completed_task_titles"]))
    if blockers.get("blocked_task_titles"):
        parts.append("Blocked: " + ", ".join(blockers["blocked_task_titles"]))
    if blockers.get("blocker_description"):
        parts.append(blockers["blocker_description"])
    return " · ".join(parts)
