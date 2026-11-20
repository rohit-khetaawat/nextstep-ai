import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.checkin import AdaptResponse, CheckInRequest, CheckInResponse
from app.services import checkin_service, goal_service, roadmap_service
from app.services.ai_service import AIServiceError, ai_service

router = APIRouter(prefix="/api/goals/{goal_id}", tags=["checkins"])


def _get_goal_or_404(db: Session, goal_id: int):
    goal = goal_service.get_goal(db, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found.")
    return goal


@router.post("/checkins", response_model=CheckInResponse)
def submit_checkin(goal_id: int, payload: CheckInRequest, db: Session = Depends(get_db)):
    goal = _get_goal_or_404(db, goal_id)
    try:
        checkin, classification = checkin_service.create_checkin(db, goal, payload.message)
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return CheckInResponse(
        id=checkin.id,
        message=checkin.message,
        classification=classification.model_dump(),
        created_at=checkin.created_at.isoformat(),
    )


@router.post("/adapt", response_model=AdaptResponse)
def adapt_roadmap(goal_id: int, db: Session = Depends(get_db)):
    goal = _get_goal_or_404(db, goal_id)
    roadmap = roadmap_service.get_active_roadmap(db, goal_id)
    if roadmap is None:
        raise HTTPException(status_code=404, detail="No roadmap exists for this goal yet.")

    latest_checkin = goal.checkins[-1] if goal.checkins else None
    if latest_checkin is None:
        raise HTTPException(status_code=400, detail="Submit a check-in before requesting an adaptation.")

    classification_context = {
        "progress": json.loads(latest_checkin.progress_json or "{}"),
        "blockers": json.loads(latest_checkin.blockers_json or "{}"),
        "message": latest_checkin.message,
    }
    remaining = roadmap_service.remaining_roadmap_summary(roadmap)
    profile = json.loads(goal.profile_json or "{}")

    completed_titles = [
        t.title for p in roadmap.phases for m in p.milestones for t in m.tasks if t.status == "COMPLETED"
    ]

    try:
        plan = ai_service.adapt_roadmap(
            goal.title,
            profile,
            classification_context,
            remaining,
            target_date=goal.target_date,
            completed_task_titles=completed_titles,
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    new_roadmap = roadmap_service.apply_adaptation(db, goal, roadmap, plan, version=roadmap.version + 1)

    return AdaptResponse(
        adapted=True,
        new_roadmap_version=new_roadmap.version,
        explanation=plan.summary or "The roadmap was updated based on your check-in.",
    )
