from pydantic import BaseModel, Field


class GapItem(BaseModel):
    area: str
    description: str
    importance: float = Field(ge=0, le=1, default=0.5)
    current_level: float | None = Field(default=None, ge=0, le=1)
    required_level: float | None = Field(default=None, ge=0, le=1)


class ProfileFields(BaseModel):
    """Structured contract returned by the Profile Interpreter AI service."""

    goal_category: str = ""
    current_level: str = ""
    desired_outcome: str = ""
    time_per_week: str = ""
    budget_resources: str = ""
    available_tools: str = ""
    constraints: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    known_strengths: list[str] = Field(default_factory=list)
    known_weaknesses: list[str] = Field(default_factory=list)
    previous_experience: str = ""
    gaps: list[GapItem] = Field(default_factory=list)
