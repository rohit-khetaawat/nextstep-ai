from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import HistoryResponse, UserResponse, UsernameRequest
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["users"])


def _response(user: User) -> UserResponse:
    return UserResponse(id=user.id, username=user.name)


@router.post("", response_model=UserResponse, status_code=201)
def create_user(payload: UsernameRequest, db: Session = Depends(get_db)):
    user = user_service.create_user(db, payload.username)
    if user is None:
        raise HTTPException(status_code=409, detail="That username is taken. Pick another, or sign in with it.")
    return _response(user)


@router.post("/login", response_model=UserResponse)
def login(payload: UsernameRequest, db: Session = Depends(get_db)):
    user = user_service.find_by_username(db, payload.username)
    if user is None:
        raise HTTPException(status_code=404, detail="No account with that username. Create it below.")
    return _response(user)


@router.get("/{user_id}/history", response_model=HistoryResponse)
def history(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return HistoryResponse(user=_response(user), goals=user_service.build_history(db, user))
