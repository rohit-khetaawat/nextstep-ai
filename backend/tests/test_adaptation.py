from app.schemas.roadmap import AIMilestoneSpec, AIPhaseSpec, AITaskSpec, RoadmapPlan
from app.services import goal_service, roadmap_service
from app.services.goal_service import get_or_create_default_user
from app.models.goal import Goal


def _make_goal(db_session):
    user = get_or_create_default_user(db_session)
    goal = Goal(user_id=user.id, title="Become a backend developer", profile_json='{"gaps": []}')
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    return goal


def _initial_plan():
    return RoadmapPlan(
        summary="initial",
        phases=[
            AIPhaseSpec(
                title="Foundations",
                objective="Learn basics",
                milestones=[
                    AIMilestoneSpec(
                        title="FastAPI Deep Dive",
                        tasks=[
                            AITaskSpec(title="Build a Basic FastAPI App", importance=0.8, urgency=0.8),
                            AITaskSpec(title="Add JWT Authentication", importance=0.7, urgency=0.6),
                        ],
                    )
                ],
            )
        ],
    )


def test_adaptation_preserves_completed_milestone_even_in_partial_phase(db_session):
    """A milestone that is fully complete must survive adaptation even though
    its phase is not fully complete - regression test for the bug where only
    whole completed *phases* were preserved, silently dropping completed work
    that happened to share a phase with still-open milestones."""

    goal = _make_goal(db_session)
    roadmap = roadmap_service.build_roadmap_from_plan(db_session, goal, _initial_plan(), version=1)

    # Complete every task in the first milestone; leave a second, brand-new
    # not-yet-complete milestone in the same phase.
    first_milestone = roadmap.phases[0].milestones[0]
    for task in first_milestone.tasks:
        task.status = "COMPLETED"
    db_session.commit()

    from app.models.roadmap import Milestone, Task

    open_milestone = Milestone(phase_id=roadmap.phases[0].id, title="Testing", order_index=1)
    db_session.add(open_milestone)
    db_session.commit()
    db_session.refresh(open_milestone)
    db_session.add(Task(milestone_id=open_milestone.id, title="Write tests", status="NOT_STARTED"))
    db_session.commit()
    db_session.refresh(roadmap)

    adapt_plan = RoadmapPlan(
        summary="adapted",
        phases=[
            AIPhaseSpec(
                title="Foundations",
                objective="Learn basics",
                milestones=[AIMilestoneSpec(title="Testing", tasks=[AITaskSpec(title="Write more tests")])],
            )
        ],
    )

    new_roadmap = roadmap_service.apply_adaptation(db_session, goal, roadmap, adapt_plan, version=2)

    all_task_titles = {t.title: t.status for p in new_roadmap.phases for m in p.milestones for t in m.tasks}
    assert all_task_titles.get("Build a Basic FastAPI App") == "COMPLETED"
    assert all_task_titles.get("Add JWT Authentication") == "COMPLETED"
    assert "Write more tests" in all_task_titles


def test_remaining_roadmap_summary_omits_completed_milestones_only(db_session):
    goal = _make_goal(db_session)
    roadmap = roadmap_service.build_roadmap_from_plan(db_session, goal, _initial_plan(), version=1)

    milestone = roadmap.phases[0].milestones[0]
    milestone.tasks[0].status = "COMPLETED"  # partially done, not fully
    db_session.commit()
    db_session.refresh(roadmap)

    summary = roadmap_service.remaining_roadmap_summary(roadmap)

    assert len(summary["phases"]) == 1
    assert summary["phases"][0]["milestones"][0]["title"] == "FastAPI Deep Dive"
