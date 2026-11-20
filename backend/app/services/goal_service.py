import json

from sqlalchemy.orm import Session

from app.models.goal import Goal, GoalAnswer
from app.models.user import User
from app.schemas.goal import AnswerSubmission, GoalCreateRequest
from app.schemas.question import QuestionSetResponse
from app.services.ai_service import ai_service

# Deterministic ceiling on the adaptive interview. The AI's own is_complete
# flag is a recommendation, not a guarantee - without a hard cap enforced in
# Python, a model that never converges could interview the user forever.
MAX_DISCOVERY_QUESTIONS = 12


def get_or_create_default_user(db: Session) -> User:
    user = db.query(User).first()
    if user is None:
        user = User(name="Guest")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def create_goal(db: Session, payload: GoalCreateRequest) -> Goal:
    user = get_or_create_default_user(db)
    goal = Goal(
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        target_date=payload.target_date,
        status="discovery",
        profile_json="{}",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_goal(db: Session, goal_id: int) -> Goal | None:
    return db.query(Goal).filter(Goal.id == goal_id).first()


def _known_profile(goal: Goal) -> dict:
    try:
        return json.loads(goal.profile_json or "{}")
    except json.JSONDecodeError:
        return {}


def get_next_questions(db: Session, goal: Goal) -> QuestionSetResponse:
    previous_answers = [
        {"question_id": a.question_id, "question_text": a.question_text, "answer": json.loads(a.answer_json)}
        for a in goal.answers
    ]

    if len(previous_answers) >= MAX_DISCOVERY_QUESTIONS:
        # Deterministic stop: never let the interview run longer than this,
        # regardless of what the AI would otherwise ask next.
        return QuestionSetResponse(questions=[], is_complete=True, inferred_category=goal.category)

    result = ai_service.generate_questions(
        goal_title=goal.title,
        goal_description=goal.description,
        known_profile=_known_profile(goal),
        previous_answers=previous_answers,
        questions_remaining=MAX_DISCOVERY_QUESTIONS - len(previous_answers),
        target_date=goal.target_date,
    )
    if result.inferred_category and not goal.category:
        goal.category = result.inferred_category
        db.commit()
    return result


def submit_answers(db: Session, goal: Goal, answers: list[AnswerSubmission]) -> Goal:
    for answer in answers:
        record = GoalAnswer(
            goal_id=goal.id,
            question_id=answer.question_id,
            question_text=answer.question_text,
            answer_json=json.dumps(answer.answer),
        )
        db.add(record)
    db.commit()
    db.refresh(goal)
    return goal


def interpret_and_store_profile(db: Session, goal: Goal) -> Goal:
    answers = [
        {"question_id": a.question_id, "question_text": a.question_text, "answer": json.loads(a.answer_json)}
        for a in goal.answers
    ]
    profile = ai_service.interpret_profile(goal.title, goal.description, answers, target_date=goal.target_date)
    goal.profile_json = profile.model_dump_json()
    if profile.goal_category and not goal.category:
        goal.category = profile.goal_category
    goal.status = "profile_ready"
    db.commit()
    db.refresh(goal)
    return goal
