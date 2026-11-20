import { StateMark, STATUS_LABEL } from "./StateMark";
import type { Task, TaskStatus } from "../types";

interface TaskListProps {
  tasks: Task[];
  updatingTaskId: number | null;
  onSetStatus: (task: Task, status: TaskStatus) => void;
  /** Show descriptions and explicit status controls (roadmap page). */
  detailed?: boolean;
  titleById?: (id: number) => string | undefined;
}

export function TaskList({ tasks, updatingTaskId, onSetStatus, detailed, titleById }: TaskListProps) {
  const sorted = [...tasks].sort((a, b) => a.order_index - b.order_index);

  return (
    <ul className="tasklist">
      {sorted.map((task) => {
        const done = task.status === "COMPLETED";
        const busy = updatingTaskId === task.id;
        const deps = titleById ? task.depends_on.map(titleById).filter(Boolean) : [];
        return (
          <li key={task.id} className={`task ${done ? "is-done" : ""}`}>
            <button
              type="button"
              className="task-toggle"
              disabled={busy}
              onClick={() => onSetStatus(task, done ? "NOT_STARTED" : "COMPLETED")}
              aria-label={done ? `Mark "${task.title}" as not done` : `Mark "${task.title}" as done`}
              title={STATUS_LABEL[task.status]}
            >
              {busy ? <span className="spinner" style={{ color: "var(--blue)", margin: 2 }} /> : <StateMark status={task.status} />}
            </button>
            <div className="task-main">
              <div className="task-title">{task.title}</div>
              {task.status === "BLOCKED" && (
                <div className="task-sub" style={{ color: "var(--amber-text)" }}>
                  Blocked{deps.length ? `: waiting on ${deps.join(", ")}` : ""}
                </div>
              )}
              {detailed && task.description && <p className="task-desc">{task.description}</p>}
              {detailed && task.status !== "BLOCKED" && deps.length > 0 && (
                <div className="task-sub">After: {deps.join(", ")}</div>
              )}
              {detailed && !done && task.status !== "BLOCKED" && (
                <div className="task-controls">
                  {task.status === "NOT_STARTED" ? (
                    <button type="button" className="btn btn-sm" disabled={busy} onClick={() => onSetStatus(task, "IN_PROGRESS")}>
                      Start
                    </button>
                  ) : (
                    <button type="button" className="btn btn-sm btn-quiet" disabled={busy} onClick={() => onSetStatus(task, "NOT_STARTED")}>
                      Not started
                    </button>
                  )}
                </div>
              )}
            </div>
            {task.estimated_effort && <span className="task-effort">{task.estimated_effort}</span>}
          </li>
        );
      })}
    </ul>
  );
}
