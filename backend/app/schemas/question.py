from typing import Literal

from pydantic import BaseModel, Field


class Question(BaseModel):
    id: str
    text: str
    type: Literal["single_choice", "multi_choice", "numeric", "date", "short_text", "long_text"]
    options: list[str] = Field(default_factory=list)
    required: bool = True
    reason: str = ""


class QuestionSetResponse(BaseModel):
    """Structured contract returned by the Question Generator AI service."""

    questions: list[Question]
    is_complete: bool = False
    inferred_category: str = ""
