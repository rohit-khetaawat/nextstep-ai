import { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { PeriodStrip } from "../components/PeriodStrip";
import { StateMark } from "../components/StateMark";
import { TaskList } from "../components/TaskList";
import { buildStrip, dueLabel, formatDate } from "../lib/timeline";
import { ApiError, api } from "../services/api";
import type { Roadmap, Task, TaskStatus } from "../types";

export function RoadmapPage() {
  const { goalId } = useParams();
  const numericGoalId = Number(goalId);
  const location = useLocation();

  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingTaskId, setUpdatingTaskId] = useState<number | null>(null);

  async function load(quiet = false) {
    if (!quiet) setLoading(true);
    setError(null);
    try {
      setRoadmap(await api.getRoadmap(numericGoalId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load the roadmap.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [numericGoalId]);

  // Jump to a phase when arriving from a strip block link.
  useEffect(() => {
    if (!roadmap || !location.hash) return;
    document.getElementById(location.hash.slice(1))?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [roadmap, location.hash]);

  const titleById = (id: number) => {
    for (const p of roadmap?.phases ?? [])
      for (const m of p.milestones) {
        const t = m.tasks.find((x) => x.id === id);
        if (t) return t.title;
      }
    return undefined;
  };

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
          <p>Loading the roadmap…</p>
        </div>
      </div>
    );
  }

  if (!roadmap) {
    return (
      <div className="page page-narrow">
        {error && <ErrorBanner message={error} onRetry={() => load()} />}
        {!error && <EmptyState title="No roadmap yet" description="Build your plan from the profile review first." />}
      </div>
    );
  }

  const strip = buildStrip(roadmap);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Roadmap</h1>
          {roadmap.summary && <p className="lede">{roadmap.summary}</p>}
        </div>
        <div className="meta-line" style={{ marginTop: 0 }}>
          <span>
            <b className="num">{Math.round(roadmap.overall_progress)}%</b> done
          </span>
          {roadmap.version > 1 && <span>Adapted · v{roadmap.version}</span>}
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      <PeriodStrip roadmap={roadmap} />

      {strip.phases.map(({ phase, state, start, end, doneTasks, totalTasks }, i) => {
        const [objective, why] = phase.objective.split(/\n\nWhy this phase matters:\s*/);
        return (
          <section key={phase.id} id={`phase-${phase.id}`} className={`phase ${state}`} aria-labelledby={`ph-${phase.id}`}>
            <div className="phase-head">
              <span className="phase-index">{String(i + 1).padStart(2, "0")}</span>
              <h2 id={`ph-${phase.id}`}>{phase.title}</h2>
              <span className={`status-chip ${state === "done" ? "done" : state === "current" ? "active" : ""}`}>
                <StateMark status={state === "done" ? "COMPLETED" : state === "current" ? "IN_PROGRESS" : "NOT_STARTED"} size={16} />
                <span className="num">
                  {doneTasks}/{totalTasks}
                </span>
                {start && end && (
                  <span className="hide-xs">
                    · {formatDate(start)} to {formatDate(end)}
                  </span>
                )}
              </span>
            </div>
            {objective && <p className="phase-why">{objective}</p>}
            {why && <p className="phase-why" style={{ marginTop: 6 }}>Why now: {why}</p>}

            <div className="milestones">
              {[...phase.milestones]
                .sort((a, b) => a.order_index - b.order_index)
                .map((m) => (
                  <article key={m.id} className="milestone">
                    <div className="milestone-head">
                      <h3 style={{ fontSize: "1.2rem" }}>{m.title}</h3>
                      {m.target_date && <span className="milestone-date">{dueLabel(m.target_date)}</span>}
                    </div>
                    {m.description && <p>{m.description}</p>}
                    <TaskList
                      tasks={m.tasks}
                      updatingTaskId={updatingTaskId}
                      onSetStatus={setStatus}
                      titleById={titleById}
                      detailed
                    />
                  </article>
                ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
