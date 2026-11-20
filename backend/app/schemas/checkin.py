from typing import Literal

from pydantic import BaseModel, Field


class CheckInRequest(BaseModel):
    message: str = Field(min_length=1)


class CheckInClassification(BaseModel):
    """Structured contract returned by the Check-in Analyzer AI service."""

    category: Literal["progress", "blocker", "changed_constraint", "new_information", "other"]
    summary: str = ""
    completed_task_titles: list[str] = Field(default_factory=list)
    blocked_task_titles: list[str] = Field(default_factory=list)
    blocker_description: str = ""
    should_adapt_roadmap: bool = False


class CheckInResponse(BaseModel):
    id: int
    message: str
    classification: dict
    created_at: str

    model_config = {"from_attributes": True}


class AdaptResponse(BaseModel):
    adapted: bool
    new_roadmap_version: int | None = None
    explanation: str
