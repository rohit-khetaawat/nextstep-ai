from pydantic import BaseModel, Field, field_validator


class GoalCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = ""
    category: str = ""
    target_date: str = ""

    @field_validator("title")
    @classmethod
    def title_must_be_meaningful(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Goal must be a meaningful description of at least 3 characters.")
        return cleaned


class GoalResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    target_date: str
    status: str
    profile: dict

    model_config = {"from_attributes": True}


class AnswerSubmission(BaseModel):
    question_id: str
    question_text: str
    answer: str | list[str]


class AnswersRequest(BaseModel):
    answers: list[AnswerSubmission]
