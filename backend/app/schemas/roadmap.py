from pydantic import BaseModel, Field


class AITaskSpec(BaseModel):
    title: str
    description: str = ""
    estimated_effort: str = ""
    importance: float = Field(ge=0, le=1, default=0.5)
    urgency: float = Field(ge=0, le=1, default=0.5)
    depends_on_titles: list[str] = Field(default_factory=list)


class AIMilestoneSpec(BaseModel):
    title: str
    description: str = ""
    target_date: str = ""
    tasks: list[AITaskSpec] = Field(default_factory=list)


class AIPhaseSpec(BaseModel):
    title: str
    objective: str = ""
    rationale: str = ""
    milestones: list[AIMilestoneSpec] = Field(default_factory=list)


class RoadmapPlan(BaseModel):
    """Structured contract returned by the Roadmap Generator AI service."""

    summary: str = ""
    phases: list[AIPhaseSpec] = Field(default_factory=list)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: float
    estimated_effort: str
    order_index: int
    depends_on: list[int] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class MilestoneResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    target_date: str
    order_index: int
    tasks: list[TaskResponse]

    model_config = {"from_attributes": True}


class PhaseResponse(BaseModel):
    id: int
    title: str
    objective: str
    order_index: int
    milestones: list[MilestoneResponse]

    model_config = {"from_attributes": True}


class RoadmapResponse(BaseModel):
    id: int
    version: int
    summary: str
    active: bool
    phases: list[PhaseResponse]
    overall_progress: float
    current_phase: str | None = None
    current_milestone: str | None = None
    next_action: str | None = None
    # When the user started working on this goal (goal creation date), so the
    # client can lay the plan out on a real timeline.
    started_at: str | None = None

    model_config = {"from_attributes": True}


class TaskUpdateRequest(BaseModel):
    status: str
