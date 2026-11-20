import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.goal import AnswersRequest, GoalCreateRequest, GoalResponse
from app.schemas.question import QuestionSetResponse
from app.schemas.roadmap import RoadmapResponse
from app.services import goal_service, roadmap_service
from app.services.ai_service import AIServiceError, ai_service

router = APIRouter(prefix="/api/goals", tags=["goals"])


def _goal_response(goal) -> GoalResponse:
    return GoalResponse(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        category=goal.category,
        target_date=goal.target_date,
        status=goal.status,
        profile=json.loads(goal.profile_json or "{}"),
    )


def _get_goal_or_404(db: Session, goal_id: int):
    goal = goal_service.get_goal(db, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found.")
    return goal


@router.post("", response_model=GoalResponse)
def create_goal(payload: GoalCreateRequest, db: Session = Depends(get_db)):
    goal = goal_service.create_goal(db, payload)
    return _goal_response(goal)


@router.get("/{goal_id}", response_model=GoalResponse)
def read_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = _get_goal_or_404(db, goal_id)
    return _goal_response(goal)


@router.post("/{goal_id}/questions", response_model=QuestionSetResponse)
def next_questions(goal_id: int, db: Session = Depends(get_db)):
    goal = _get_goal_or_404(db, goal_id)
    try:
        return goal_service.get_next_questions(db, goal)
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{goal_id}/answers", response_model=GoalResponse)
def submit_answers(goal_id: int, payload: AnswersRequest, db: Session = Depends(get_db)):
    goal = _get_goal_or_404(db, goal_id)
    goal = goal_service.submit_answers(db, goal, payload.answers)
    return _goal_response(goal)


@router.post("/{goal_id}/profile", response_model=GoalResponse)
def finalize_profile(goal_id: int, db: Session = Depends(get_db)):
    goal = _get_goal_or_404(db, goal_id)
    try:
        goal = goal_service.interpret_and_store_profile(db, goal)
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _goal_response(goal)


@router.post("/{goal_id}/roadmap", response_model=RoadmapResponse)
def generate_roadmap(goal_id: int, db: Session = Depends(get_db)):
    goal = _get_goal_or_404(db, goal_id)
    profile = json.loads(goal.profile_json or "{}")
    if not profile:
        raise HTTPException(status_code=400, detail="Build the profile before generating a roadmap.")

    try:
        plan = ai_service.generate_roadmap(goal.title, goal.description, profile, target_date=goal.target_date)
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    existing_count = roadmap_service.deactivate_existing_roadmaps(db, goal.id)
    roadmap = roadmap_service.build_roadmap_from_plan(db, goal, plan, version=existing_count + 1)
    goal.status = "active"
    db.commit()
    return roadmap_service.build_roadmap_response(db, roadmap)


@router.get("/{goal_id}/roadmap", response_model=RoadmapResponse)
def read_roadmap(goal_id: int, db: Session = Depends(get_db)):
    _get_goal_or_404(db, goal_id)
    roadmap = roadmap_service.get_active_roadmap(db, goal_id)
    if roadmap is None:
        raise HTTPException(status_code=404, detail="No roadmap has been generated yet.")
    return roadmap_service.build_roadmap_response(db, roadmap)
