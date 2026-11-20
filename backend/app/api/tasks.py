from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.roadmap import Task, TaskDependency
from app.schemas.roadmap import TaskResponse, TaskUpdateRequest
from app.services import progress_service, roadmap_service
from app.services.dependency_service import is_blocked

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

VALID_STATUSES = set(progress_service.TASK_STATES)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdateRequest, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {sorted(VALID_STATUSES)}")

    roadmap_id = task.milestone.phase.roadmap_id
    all_tasks = [t for p in task.milestone.phase.roadmap.phases for m in p.milestones for t in m.tasks]
    task_ids = {t.id for t in all_tasks}
    deps = db.query(TaskDependency).filter(TaskDependency.task_id.in_(task_ids)).all()
    edges = [(d.task_id, d.depends_on_task_id) for d in deps]
    completed_ids = {t.id for t in all_tasks if t.status == "COMPLETED"}

    if payload.status in ("IN_PROGRESS", "COMPLETED") and is_blocked(task.id, edges, completed_ids):
        raise HTTPException(
            status_code=409,
            detail="This task is blocked by an incomplete dependency and cannot be started or completed yet.",
        )

    task.status = payload.status
    db.commit()

    roadmap_service.recompute_priorities(db, roadmap_id)
    db.refresh(task)

    dep_ids = [d.depends_on_task_id for d in deps if d.task_id == task.id]
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        estimated_effort=task.estimated_effort,
        order_index=task.order_index,
        depends_on=dep_ids,
    )
