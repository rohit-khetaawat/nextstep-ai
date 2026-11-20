from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"))
    version: Mapped[int] = mapped_column(default=1)
    summary: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    goal: Mapped["Goal"] = relationship(back_populates="roadmaps")
    phases: Mapped[list["Phase"]] = relationship(back_populates="roadmap", cascade="all, delete-orphan", order_by="Phase.order_index")


class Phase(Base):
    __tablename__ = "phases"

    id: Mapped[int] = mapped_column(primary_key=True)
    roadmap_id: Mapped[int] = mapped_column(ForeignKey("roadmaps.id"))
    title: Mapped[str] = mapped_column(String(300))
    objective: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    roadmap: Mapped["Roadmap"] = relationship(back_populates="phases")
    milestones: Mapped[list["Milestone"]] = relationship(back_populates="phase", cascade="all, delete-orphan", order_by="Milestone.order_index")


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(primary_key=True)
    phase_id: Mapped[int] = mapped_column(ForeignKey("phases.id"))
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="NOT_STARTED")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    target_date: Mapped[str] = mapped_column(String(40), default="")

    phase: Mapped["Phase"] = relationship(back_populates="milestones")
    tasks: Mapped[list["Task"]] = relationship(back_populates="milestone", cascade="all, delete-orphan", order_by="Task.order_index")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    milestone_id: Mapped[int] = mapped_column(ForeignKey("milestones.id"))
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="NOT_STARTED")
    priority: Mapped[float] = mapped_column(default=0.0)
    importance: Mapped[float] = mapped_column(default=0.5)
    urgency: Mapped[float] = mapped_column(default=0.5)
    gap: Mapped[float] = mapped_column(default=0.6)
    estimated_effort: Mapped[str] = mapped_column(String(80), default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    milestone: Mapped["Milestone"] = relationship(back_populates="tasks")


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    depends_on_task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
