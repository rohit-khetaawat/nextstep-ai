import re

from pydantic import BaseModel, field_validator

_ALLOWED = re.compile(r"^[A-Za-z0-9 _.\-]+$")


class UsernameRequest(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def valid_username(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2 or len(cleaned) > 40:
            raise ValueError("Username must be between 2 and 40 characters.")
        if not _ALLOWED.match(cleaned):
            raise ValueError("Use letters, numbers, spaces, dots, dashes or underscores only.")
        return cleaned


class UserResponse(BaseModel):
    id: int
    username: str


class HistoryAnswer(BaseModel):
    question: str
    answer: str
    created_at: str


class HistoryCheckIn(BaseModel):
    message: str
    summary: str
    created_at: str


class HistoryGoal(BaseModel):
    id: int
    title: str
    status: str
    has_roadmap: bool
    created_at: str
    answers: list[HistoryAnswer]
    checkins: list[HistoryCheckIn]


class HistoryResponse(BaseModel):
    user: UserResponse
    goals: list[HistoryGoal]
