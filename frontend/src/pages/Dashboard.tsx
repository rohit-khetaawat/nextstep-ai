import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowRight, Check, Sparkles } from "lucide-react";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingButton } from "../components/LoadingButton";
import { PeriodStrip } from "../components/PeriodStrip";
import { TaskList } from "../components/TaskList";
import { writeLastGoal } from "../lib/lastGoal";
import { dueLabel, parseDate, formatDate } from "../lib/timeline";
import { ApiError, api } from "../services/api";
import type { Goal, Milestone, Roadmap, Task, TaskStatus } from "../types";

function findTask(roadmap: Roadmap, title: string | null): { task: Task; milestone: Milestone } | null {
  if (!title) return null;
  for (const p of roadmap.phases)
    for (const m of p.milestones)
      for (const t of m.tasks) if (t.title === title) return { task: t, milestone: m };
  return null;
}

export function Dashboard() {
  const { goalId } = useParams();
  const numericGoalId = Number(goalId);
  const navigate = useNavigate();

  const [goal, setGoal] = useState<Goal | null>(null);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingTaskId, setUpdatingTaskId] = useState<number | null>(null);

  async function load(quiet = false) {
    if (!quiet) setLoading(true);
    setError(null);
    try {
      const [goalResult, roadmapResult] = await Promise.all([
        api.getGoal(numericGoalId),
        api.getRoadmap(numericGoalId).catch((err) => {
          if (err instanceof ApiError && err.status === 404) return null;
          throw err;
        }),
      ]);
      setGoal(goalResult);
      setRoadmap(roadmapResult);
      writeLastGoal({ id: goalResult.id, title: goalResult.title, hasRoadmap: !!roadmapResult });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load your plan.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [numericGoalId]);

  async function setStatus(task: Task, status: TaskStatus) {
    setUpdatingTaskId(task.id);
    setError(null);
    try {
      await api.updateTaskStatus(task.id, status);
      await load(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't update that task.");
    } finally {
      setUpdatingTaskId(null);
    }
  }

  if (loading) {
    return (
      <div className="page">
        <div className="panel empty" role="status">
          <span className="spinner" style={{ color: "var(--blue)", display: "inline-block" }} aria-hidden="true" />
          <p>Loading your plan…</p>
        </div>
      </div>
    );
  }

  if (!roadmap || !goal) {
    return (
      <div className="page page-narrow">
        {error && <ErrorBanner message={error} onRetry={() => load()} />}
        {!error && (
          <EmptyState
            title="No plan yet"
            description="Finish the questions and review your profile to build a plan."
            action={
              <button className="btn btn-primary" onClick={() => navigate(`/goals/${numericGoalId}/profile`)}>
                Review profile
              </button>
            }
          />
        )}
      </div>
    );
  }

  const allTasks = roadmap.phases.flatMap((p) => p.milestones.flatMap((m) => m.tasks));
  const doneCount = allTasks.filter((t) => t.status === "COMPLETED").length;
  const phaseIdx = roadmap.phases.findIndex((p) => p.title === roadmap.current_phase);
  const next = findTask(roadmap, roadmap.next_action);
  const currentMilestone =
    next?.milestone ??
    roadmap.phases.flatMap((p) => p.milestones).find((m) => m.title === roadmap.current_milestone) ??
    null;
  const target = parseDate(goal.target_date);
  const upcoming = roadmap.phases
    .flatMap((p) => p.milestones)
    .filter((m) => m.status !== "COMPLETED" && m.id !== currentMilestone?.id)
    .slice(0, 3);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{goal.title}</h1>
          <div className="meta-line">
            {goal.category && <span>{goal.category}</span>}
            {target && (
              <span>
                Target <b>{formatDate(target, true)}</b>
              </span>
            )}
            <span>
              <b className="num">{Math.round(roadmap.overall_progress)}%</b> done
            </span>
            <span>
              <b className="num">
                {doneCount} of {allTasks.length}
              </b>{" "}
              tasks
            </span>
            {phaseIdx >= 0 && (
              <span>
                Phase <b className="num">{phaseIdx + 1}</b> of {roadmap.phases.length}
              </span>
            )}
            {roadmap.version > 1 && <span>Plan v{roadmap.version}</span>}
          </div>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      <PeriodStrip roadmap={roadmap} linkBase={`/goals/${numericGoalId}/roadmap`} />

      <div className="plan-grid">
        {next ? (
          <section className="session" aria-labelledby="session-title">
            <h2 id="session-title">{next.task.title}</h2>
            {next.task.description && <p className="desc">{next.task.description}</p>}
            <div className="facts">
              {next.task.estimated_effort && (
                <div>
                  Effort <b>{next.task.estimated_effort}</b>
                </div>
              )}
              <div>
                Milestone <b>{next.milestone.title}</b>
              </div>
              {next.milestone.target_date && (
                <div>
                  Due <b>{dueLabel(next.milestone.target_date)}</b>
                </div>
              )}
            </div>
            <div className="actions">
              <LoadingButton
                variant="ink"
                loading={updatingTaskId === next.task.id}
                onClick={() => setStatus(next.task, "COMPLETED")}
              >
                <Check size={18} aria-hidden="true" />
                Mark done
              </LoadingButton>
              {next.task.status === "NOT_STARTED" && (
                <button className="btn hide-xs" disabled={updatingTaskId === next.task.id} onClick={() => setStatus(next.task, "IN_PROGRESS")}>
                  Start it
                </button>
              )}
              <Link
                className="btn btn-quiet"
                to={`/goals/${numericGoalId}/checkin`}
                state={{ prefill: `I'm stuck on "${next.task.title}" because ` }}
              >
                I'm stuck
              </Link>
            </div>
          </section>
        ) : (
          <section className="session">
            <h2>
              <Sparkles size={22} aria-hidden="true" style={{ verticalAlign: -3, marginRight: 8, color: "var(--green)" }} />
              Every open task is done or waiting on something.
            </h2>
            <p className="desc">Check in to tell the plan what's next, or review the full roadmap.</p>
            <div className="actions" style={{ marginTop: 16 }}>
              <Link className="btn btn-primary" to={`/goals/${numericGoalId}/checkin`}>
                Check in
              </Link>
            </div>
          </section>
        )}

        <div>
          {currentMilestone && (
            <section className="panel">
              <h2 className="section-title">
                {currentMilestone.title}
                {currentMilestone.target_date && <small>due {dueLabel(currentMilestone.target_date)}</small>}
              </h2>
              <TaskList tasks={currentMilestone.tasks} updatingTaskId={updatingTaskId} onSetStatus={setStatus} />
            </section>
          )}

          {upcoming.length > 0 && (
            <section className="panel">
              <h2 className="section-title">
                Coming up
                <Link to={`/goals/${numericGoalId}/roadmap`} style={{ fontSize: "0.9rem", fontFamily: "var(--font-ui)", fontWeight: 600 }}>
                  Full roadmap <ArrowRight size={14} style={{ verticalAlign: -2 }} aria-hidden="true" />
                </Link>
              </h2>
              <ul className="tasklist">
                {upcoming.map((m) => (
                  <li key={m.id} className="task">
                    <div className="task-main">
                      <div className="task-title">{m.title}</div>
                      <div className="task-sub">{m.tasks.length} tasks</div>
                    </div>
                    {m.target_date && <span className="task-effort">{dueLabel(m.target_date)}</span>}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
