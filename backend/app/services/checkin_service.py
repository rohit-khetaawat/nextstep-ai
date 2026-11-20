import json

from sqlalchemy.orm import Session

from app.models.checkin import CheckIn
from app.models.goal import Goal
from app.models.roadmap import Task
from app.schemas.checkin import CheckInClassification
from app.services import roadmap_service
from app.services.ai_service import ai_service
from app.services.title_match import match_title


def create_checkin(db: Session, goal: Goal, message: str) -> tuple[CheckIn, CheckInClassification]:
    roadmap = roadmap_service.get_active_roadmap(db, goal.id)
    open_tasks: list[Task] = []
    if roadmap:
        open_tasks = [
            t
            for p in roadmap.phases
            for m in p.milestones
            for t in m.tasks
            if t.status in ("NOT_STARTED", "IN_PROGRESS", "BLOCKED")
        ]
    open_titles = [t.title for t in open_tasks]

    classification = ai_service.classify_checkin(message, open_titles)

    # Resolve the model's titles to real ones (tolerating case/punctuation
    # drift) and report the canonical titles back to the client.
    completed_titles = _resolve_titles(classification.completed_task_titles, open_titles)
    blocked_titles = [t for t in _resolve_titles(classification.blocked_task_titles, open_titles)
                      if t not in completed_titles]
    classification.completed_task_titles = completed_titles
    classification.blocked_task_titles = blocked_titles

    completed_count = 0
    for task in open_tasks:
        if task.title in completed_titles:
            task.status = "COMPLETED"
            completed_count += 1

    # Recompute dependency-driven priorities/blocks first, then apply the
    # user-reported blocks - recompute_priorities would otherwise clear a
    # BLOCKED status that has no unfinished dependency behind it.
    if roadmap and completed_count:
        db.commit()
        roadmap_service.recompute_priorities(db, roadmap.id)
    for task in open_tasks:
        if task.title in blocked_titles:
            task.status = "BLOCKED"

    checkin = CheckIn(
        goal_id=goal.id,
        message=message,
        progress_json=json.dumps({"completed_task_titles": classification.completed_task_titles}),
        blockers_json=json.dumps(
            {
                "blocked_task_titles": classification.blocked_task_titles,
                "blocker_description": classification.blocker_description,
            }
        ),
    )
    db.add(checkin)
    db.commit()

    db.refresh(checkin)
    return checkin, classification


def _resolve_titles(candidates: list[str], open_titles: list[str]) -> list[str]:
    resolved: list[str] = []
    for candidate in candidates:
        match = match_title(candidate, open_titles)
        if match and match not in resolved:
            resolved.append(match)
    return resolved
