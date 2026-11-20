from app.models.roadmap import Milestone, Phase, Task
from app.services import progress_service


def make_task(status, order_index=0, priority=0.0):
    return Task(status=status, order_index=order_index, priority=priority, title=f"t{order_index}")


def test_overall_progress_with_no_tasks_is_zero():
    phase = Phase(title="P1", milestones=[Milestone(title="M1", tasks=[])])
    assert progress_service.overall_progress([phase]) == 0.0


def test_overall_progress_counts_completed_tasks():
    milestone = Milestone(
        title="M1",
        tasks=[make_task("COMPLETED", 0), make_task("NOT_STARTED", 1), make_task("COMPLETED", 2), make_task("NOT_STARTED", 3)],
    )
    phase = Phase(title="P1", milestones=[milestone])
    assert progress_service.overall_progress([phase]) == 50.0


def test_milestone_status_all_completed():
    tasks = [make_task("COMPLETED", 0), make_task("COMPLETED", 1)]
    assert progress_service.milestone_status_from_tasks(tasks) == "COMPLETED"


def test_milestone_status_in_progress_when_mixed():
    tasks = [make_task("COMPLETED", 0), make_task("NOT_STARTED", 1)]
    assert progress_service.milestone_status_from_tasks(tasks) == "IN_PROGRESS"


def test_milestone_status_not_started_when_empty():
    assert progress_service.milestone_status_from_tasks([]) == "NOT_STARTED"


def test_find_current_phase_skips_completed_phases():
    completed_milestone = Milestone(title="M1", order_index=0, tasks=[make_task("COMPLETED", 0)])
    active_milestone = Milestone(title="M2", order_index=1, tasks=[make_task("NOT_STARTED", 0)])
    phase1 = Phase(title="P1", order_index=0, milestones=[completed_milestone])
    phase2 = Phase(title="P2", order_index=1, milestones=[active_milestone])

    phase, milestone = progress_service.find_current_phase_and_milestone([phase1, phase2])
    assert phase.title == "P2"
    assert milestone.title == "M2"


def test_find_next_action_respects_priority():
    low = Task(id=1, status="NOT_STARTED", order_index=0, priority=0.2, title="low")
    high = Task(id=2, status="NOT_STARTED", order_index=1, priority=0.8, title="high")
    milestone = Milestone(title="M1", tasks=[low, high])

    next_task = progress_service.find_next_action(milestone, dependencies=[])
    assert next_task.title == "high"


def test_find_next_action_none_when_all_blocked_by_dependency():
    from app.models.roadmap import TaskDependency

    task = Task(id=1, status="NOT_STARTED", order_index=0, priority=0.5, title="blocked")
    milestone = Milestone(title="M1", tasks=[task])
    dep = TaskDependency(task_id=1, depends_on_task_id=999)

    next_task = progress_service.find_next_action(milestone, dependencies=[dep])
    assert next_task is None
