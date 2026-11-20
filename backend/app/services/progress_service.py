"""Deterministic progress calculation. The AI never computes progress."""

from app.models.roadmap import Milestone, Phase, Task, TaskDependency

TASK_STATES = ("NOT_STARTED", "IN_PROGRESS", "BLOCKED", "COMPLETED")
MILESTONE_STATES = ("NOT_STARTED", "IN_PROGRESS", "BLOCKED", "COMPLETED")


def task_progress_fraction(status: str) -> float:
    return 1.0 if status == "COMPLETED" else 0.0


def milestone_status_from_tasks(tasks: list[Task]) -> str:
    if not tasks:
        return "NOT_STARTED"
    statuses = {t.status for t in tasks}
    if statuses == {"COMPLETED"}:
        return "COMPLETED"
    if "BLOCKED" in statuses and "IN_PROGRESS" not in statuses and "COMPLETED" not in statuses:
        return "BLOCKED"
    if any(s in ("IN_PROGRESS", "COMPLETED", "BLOCKED") for s in statuses):
        return "IN_PROGRESS"
    return "NOT_STARTED"


def milestone_progress_fraction(tasks: list[Task]) -> float:
    if not tasks:
        return 0.0
    completed = sum(1 for t in tasks if t.status == "COMPLETED")
    return completed / len(tasks)


def phase_progress_fraction(milestones: list[Milestone]) -> float:
    all_tasks = [t for m in milestones for t in m.tasks]
    if not all_tasks:
        return 0.0
    completed = sum(1 for t in all_tasks if t.status == "COMPLETED")
    return completed / len(all_tasks)


def overall_progress(phases: list[Phase]) -> float:
    all_tasks = [t for p in phases for m in p.milestones for t in m.tasks]
    if not all_tasks:
        return 0.0
    completed = sum(1 for t in all_tasks if t.status == "COMPLETED")
    return round(100 * completed / len(all_tasks), 1)


def find_current_phase_and_milestone(phases: list[Phase]) -> tuple[Phase | None, Milestone | None]:
    """The current phase/milestone is the first one that is not fully complete."""

    for phase in sorted(phases, key=lambda p: p.order_index):
        if phase_progress_fraction(phase.milestones) >= 1.0 and phase.milestones:
            continue
        for milestone in sorted(phase.milestones, key=lambda m: m.order_index):
            if milestone_progress_fraction(milestone.tasks) < 1.0 or not milestone.tasks:
                return phase, milestone
        return phase, None
    return None, None


def find_next_action(
    milestone: Milestone | None, dependencies: list[TaskDependency]
) -> Task | None:
    """The next best action: the highest-priority unblocked, not-started/in-progress task."""

    if milestone is None:
        return None
    completed_ids = {t.id for t in milestone.tasks if t.status == "COMPLETED"}
    edges = [(d.task_id, d.depends_on_task_id) for d in dependencies]

    candidates = [t for t in milestone.tasks if t.status in ("NOT_STARTED", "IN_PROGRESS")]
    unblocked = []
    for task in candidates:
        prereqs = [dep for tid, dep in edges if tid == task.id]
        if all(p in completed_ids for p in prereqs):
            unblocked.append(task)

    if not unblocked:
        return None
    return max(unblocked, key=lambda t: (t.priority, -t.order_index))
