import json

from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.models.roadmap import Milestone, Phase, Roadmap, Task, TaskDependency
from app.schemas.roadmap import RoadmapPlan
from app.services import dependency_service, progress_service
from app.services.ai_service import ai_service
from app.services.priority_service import dependency_weight, priority_score
from app.services.title_match import match_title


def _profile_gap_factor(profile: dict) -> float:
    gaps = profile.get("gaps") or []
    values = []
    for gap in gaps:
        required = gap.get("required_level")
        current = gap.get("current_level")
        if required is not None and current is not None:
            values.append(max(0.05, min(1.0, required - current)) if required > current else 0.3)
        else:
            values.append(gap.get("importance", 0.5))
    return sum(values) / len(values) if values else 0.6


def deactivate_existing_roadmaps(db: Session, goal_id: int) -> int:
    existing = db.query(Roadmap).filter(Roadmap.goal_id == goal_id).all()
    for r in existing:
        r.active = False
    db.commit()
    return len(existing)


def _insert_phase_specs(
    db: Session,
    roadmap: Roadmap,
    phase_specs: list,
    start_order_index: int,
    gap_factor: float,
    title_to_task_id: dict[str, int],
    completed_titles: list[str] | None = None,
) -> None:
    """Insert phases/milestones/tasks from AI phase specs, resolving dependency
    edges against title_to_task_id (which may already contain carried-over
    tasks from a previous roadmap version so cross-version references work).

    Tasks whose title matches one of completed_titles (work the user already
    finished inside a milestone that is being revised) keep COMPLETED status.
    """

    completed_titles = completed_titles or []
    pending_edges: list[tuple[str, list[str]]] = []

    for offset, phase_spec in enumerate(phase_specs):
        objective = phase_spec.objective
        if phase_spec.rationale:
            objective = f"{objective}\n\nWhy this phase matters: {phase_spec.rationale}".strip()
        phase = Phase(
            roadmap_id=roadmap.id,
            title=phase_spec.title,
            objective=objective,
            order_index=start_order_index + offset,
        )
        db.add(phase)
        db.flush()

        for milestone_idx, milestone_spec in enumerate(phase_spec.milestones):
            milestone = Milestone(
                phase_id=phase.id,
                title=milestone_spec.title,
                description=milestone_spec.description,
                target_date=milestone_spec.target_date,
                status="NOT_STARTED",
                order_index=milestone_idx,
            )
            db.add(milestone)
            db.flush()

            for task_idx, task_spec in enumerate(milestone_spec.tasks):
                task = Task(
                    milestone_id=milestone.id,
                    title=task_spec.title,
                    description=task_spec.description,
                    status="COMPLETED" if match_title(task_spec.title, completed_titles) else "NOT_STARTED",
                    importance=task_spec.importance,
                    urgency=task_spec.urgency,
                    gap=gap_factor,
                    estimated_effort=task_spec.estimated_effort,
                    order_index=task_idx,
                )
                db.add(task)
                db.flush()
                title_to_task_id[task_spec.title] = task.id
                pending_edges.append((task_spec.title, task_spec.depends_on_titles))

    edges: list[tuple[int, int]] = []
    known_titles = list(title_to_task_id.keys())
    for task_title, depends_on_titles in pending_edges:
        task_id = title_to_task_id[task_title]
        for dep_title in depends_on_titles:
            matched = match_title(dep_title, known_titles)
            dep_id = title_to_task_id.get(matched) if matched else None
            if dep_id is not None and dep_id != task_id:
                edges.append((task_id, dep_id))

    all_task_ids = set(title_to_task_id.values())
    dependency_service.validate_edges(all_task_ids, edges)
    if dependency_service.has_cycle(all_task_ids, edges):
        # Drop dependency edges rather than fail roadmap creation on an AI mistake.
        edges = []

    for task_id, dep_id in edges:
        db.add(TaskDependency(task_id=task_id, depends_on_task_id=dep_id))
    db.commit()


def build_roadmap_from_plan(db: Session, goal: Goal, plan: RoadmapPlan, version: int) -> Roadmap:
    gap_factor = _profile_gap_factor(json.loads(goal.profile_json or "{}"))

    roadmap = Roadmap(goal_id=goal.id, version=version, summary=plan.summary, active=True)
    db.add(roadmap)
    db.flush()

    _insert_phase_specs(db, roadmap, plan.phases, start_order_index=0, gap_factor=gap_factor, title_to_task_id={})

    recompute_priorities(db, roadmap.id)
    db.refresh(roadmap)
    return roadmap


def apply_adaptation(db: Session, goal: Goal, previous_roadmap: Roadmap, plan: RoadmapPlan, version: int) -> Roadmap:
    """Create a new roadmap version that preserves every fully-completed
    milestone from previous_roadmap unchanged (even ones sitting inside a
    phase that is only partially done) and replaces the not-yet-complete
    milestones with the adapter's revised plan. Preserving at milestone
    granularity - rather than only whole completed phases - avoids losing a
    finished milestone that happens to share a phase with still-open work.
    """

    gap_factor = _profile_gap_factor(json.loads(goal.profile_json or "{}"))
    roadmap = Roadmap(goal_id=goal.id, version=version, summary=plan.summary, active=True)
    db.add(roadmap)
    db.flush()

    title_to_task_id: dict[str, int] = {}
    old_to_new_task_id: dict[int, int] = {}
    preserved_phase_count = 0

    for old_phase in sorted(previous_roadmap.phases, key=lambda x: x.order_index):
        completed_milestones = [
            m
            for m in sorted(old_phase.milestones, key=lambda x: x.order_index)
            if m.tasks and progress_service.milestone_progress_fraction(m.tasks) >= 1.0
        ]
        if not completed_milestones:
            continue

        new_phase = Phase(
            roadmap_id=roadmap.id,
            title=old_phase.title,
            objective=old_phase.objective,
            order_index=preserved_phase_count,
        )
        db.add(new_phase)
        db.flush()
        preserved_phase_count += 1

        for old_milestone in completed_milestones:
            new_milestone = Milestone(
                phase_id=new_phase.id,
                title=old_milestone.title,
                description=old_milestone.description,
                target_date=old_milestone.target_date,
                status="COMPLETED",
                order_index=old_milestone.order_index,
            )
            db.add(new_milestone)
            db.flush()
            for old_task in sorted(old_milestone.tasks, key=lambda x: x.order_index):
                new_task = Task(
                    milestone_id=new_milestone.id,
                    title=old_task.title,
                    description=old_task.description,
                    status="COMPLETED",
                    importance=old_task.importance,
                    urgency=old_task.urgency,
                    gap=old_task.gap,
                    estimated_effort=old_task.estimated_effort,
                    order_index=old_task.order_index,
                )
                db.add(new_task)
                db.flush()
                old_to_new_task_id[old_task.id] = new_task.id
                title_to_task_id[old_task.title] = new_task.id
    db.commit()

    old_deps = (
        db.query(TaskDependency).filter(TaskDependency.task_id.in_(old_to_new_task_id.keys())).all()
        if old_to_new_task_id
        else []
    )
    for dep in old_deps:
        new_task_id = old_to_new_task_id.get(dep.task_id)
        new_dep_id = old_to_new_task_id.get(dep.depends_on_task_id)
        if new_task_id and new_dep_id:
            db.add(TaskDependency(task_id=new_task_id, depends_on_task_id=new_dep_id))
    db.commit()

    # Completed tasks that sit in milestones being revised (not preserved
    # above) - keep them marked complete if the adapter keeps them.
    revised_completed_titles = [
        t.title
        for p in previous_roadmap.phases
        for m in p.milestones
        for t in m.tasks
        if t.status == "COMPLETED" and t.id not in old_to_new_task_id
    ]

    _insert_phase_specs(
        db,
        roadmap,
        plan.phases,
        start_order_index=preserved_phase_count,
        gap_factor=gap_factor,
        title_to_task_id=title_to_task_id,
        completed_titles=revised_completed_titles,
    )

    previous_roadmap.active = False
    db.commit()

    recompute_priorities(db, roadmap.id)
    db.refresh(roadmap)
    return roadmap


def remaining_roadmap_summary(roadmap: Roadmap) -> dict:
    """A compact JSON-able summary of not-yet-complete milestones, for the
    Roadmap Adapter prompt. Fully-completed milestones are omitted entirely
    since apply_adaptation preserves them untouched regardless of their
    phase's overall completion."""

    phases = []
    for phase in sorted(roadmap.phases, key=lambda p: p.order_index):
        remaining_milestones = [
            m
            for m in sorted(phase.milestones, key=lambda x: x.order_index)
            if not (m.tasks and progress_service.milestone_progress_fraction(m.tasks) >= 1.0)
        ]
        if not remaining_milestones:
            continue
        phases.append(
            {
                "title": phase.title,
                "objective": phase.objective,
                "milestones": [
                    {
                        "title": m.title,
                        "description": m.description,
                        "tasks": [{"title": t.title, "status": t.status} for t in m.tasks],
                    }
                    for m in remaining_milestones
                ],
            }
        )
    return {"phases": phases}


def recompute_priorities(db: Session, roadmap_id: int) -> None:
    roadmap = db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
    if roadmap is None:
        return
    all_tasks = [t for p in roadmap.phases for m in p.milestones for t in m.tasks]
    task_ids = {t.id for t in all_tasks}
    deps = db.query(TaskDependency).filter(TaskDependency.task_id.in_(task_ids)).all()
    edges = [(d.task_id, d.depends_on_task_id) for d in deps]
    completed_ids = {t.id for t in all_tasks if t.status == "COMPLETED"}
    unblocked = dependency_service.unblocked_counts(task_ids, edges)
    max_unblocked = max(unblocked.values(), default=0)

    for task in all_tasks:
        blocked = dependency_service.is_blocked(task.id, edges, completed_ids)
        weight = dependency_weight(unblocked.get(task.id, 0), blocked, max_unblocked)
        task.priority = priority_score(task.importance, task.gap, task.urgency, weight)
        task.status = "BLOCKED" if blocked and task.status == "NOT_STARTED" else task.status
        if not blocked and task.status == "BLOCKED":
            task.status = "NOT_STARTED"
    db.commit()


def get_active_roadmap(db: Session, goal_id: int) -> Roadmap | None:
    return (
        db.query(Roadmap)
        .filter(Roadmap.goal_id == goal_id, Roadmap.active.is_(True))
        .order_by(Roadmap.version.desc())
        .first()
    )


def build_roadmap_response(db: Session, roadmap: Roadmap) -> dict:
    all_tasks = [t for p in roadmap.phases for m in p.milestones for t in m.tasks]
    task_ids = {t.id for t in all_tasks}
    deps = db.query(TaskDependency).filter(TaskDependency.task_id.in_(task_ids)).all() if task_ids else []
    dep_map: dict[int, list[int]] = {}
    for d in deps:
        dep_map.setdefault(d.task_id, []).append(d.depends_on_task_id)

    phase, milestone = progress_service.find_current_phase_and_milestone(roadmap.phases)
    next_action = progress_service.find_next_action(milestone, deps)

    phases_payload = []
    for p in sorted(roadmap.phases, key=lambda x: x.order_index):
        milestones_payload = []
        for m in sorted(p.milestones, key=lambda x: x.order_index):
            tasks_payload = [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "priority": t.priority,
                    "estimated_effort": t.estimated_effort,
                    "order_index": t.order_index,
                    "depends_on": dep_map.get(t.id, []),
                }
                for t in sorted(m.tasks, key=lambda x: x.order_index)
            ]
            milestones_payload.append(
                {
                    "id": m.id,
                    "title": m.title,
                    "description": m.description,
                    "status": progress_service.milestone_status_from_tasks(m.tasks),
                    "target_date": m.target_date,
                    "order_index": m.order_index,
                    "tasks": tasks_payload,
                }
            )
        phases_payload.append(
            {
                "id": p.id,
                "title": p.title,
                "objective": p.objective,
                "order_index": p.order_index,
                "milestones": milestones_payload,
            }
        )

    return {
        "id": roadmap.id,
        "version": roadmap.version,
        "summary": roadmap.summary,
        "active": roadmap.active,
        "phases": phases_payload,
        "overall_progress": progress_service.overall_progress(roadmap.phases),
        "current_phase": phase.title if phase else None,
        "current_milestone": milestone.title if milestone else None,
        "next_action": next_action.title if next_action else None,
        "started_at": roadmap.goal.created_at.date().isoformat() if roadmap.goal and roadmap.goal.created_at else None,
    }
