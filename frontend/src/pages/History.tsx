import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { ErrorBanner } from "../components/ErrorBanner";
import { EmptyState } from "../components/EmptyState";
import { readUser } from "../lib/session";
import { ApiError, api } from "../services/api";
import type { HistoryGoal } from "../types";

function when(iso: string) {
  const d = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z");
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function GoalHistory({ goal }: { goal: HistoryGoal }) {
  const turns = goal.answers.length + goal.checkins.length;
  return (
    <details className="panel history-goal">
      <summary>
        <span className="history-title">{goal.title}</span>
        <span className="muted">
          {when(goal.created_at)} · {turns} {turns === 1 ? "message" : "messages"}
        </span>
      </summary>
      <div className="history-body">
        <Link
          className="btn btn-sm"
          to={goal.has_roadmap ? `/goals/${goal.id}/dashboard` : `/goals/${goal.id}/discovery`}
        >
          {goal.has_roadmap ? "Open plan" : "Continue setup"}
        </Link>

        {goal.answers.length > 0 && (
          <>
            <h3>Your interview</h3>
            <ol className="chat">
              {goal.answers.map((a, i) => (
                <li key={i}>
                  <p className="chat-q">{a.question}</p>
                  <p className="chat-a">{a.answer}</p>
                </li>
              ))}
            </ol>
          </>
        )}

        {goal.checkins.length > 0 && (
          <>
            <h3>Check-ins</h3>
            <ol className="chat">
              {goal.checkins.map((c, i) => (
                <li key={i}>
                  <p className="chat-a">{c.message}</p>
                  {c.summary && <p className="chat-q">{c.summary}</p>}
                  <p className="chat-date">{when(c.created_at)}</p>
                </li>
              ))}
            </ol>
          </>
        )}

        {turns === 0 && <p className="muted">No conversation recorded for this goal yet.</p>}
      </div>
    </details>
  );
}

export function History() {
  const user = readUser();
  const [goals, setGoals] = useState<HistoryGoal[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    if (!user) return;
    setError(null);
    api
      .getHistory(user.id)
      .then((r) => setGoals(r.goals))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Couldn't load your history."));
  }

  useEffect(load, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (!user) return <Navigate to="/signin" replace />;

  return (
    <div className="page page-narrow">
      <div className="page-head">
        <div>
          <h1>{user.username}'s history</h1>
          <p className="lede">Every goal you started, with your interview answers and check-ins.</p>
        </div>
        <Link to="/create" className="btn btn-primary">
          New goal
        </Link>
      </div>

      {error && <ErrorBanner message={error} onRetry={load} />}
      {!error && goals === null && <p className="muted">Loading…</p>}
      {goals?.length === 0 && (
        <EmptyState
          title="No goals yet"
          description="Start one and your conversation will be saved here."
          action={
            <Link to="/create" className="btn btn-primary">
              Create a goal
            </Link>
          }
        />
      )}
      {goals?.map((g) => <GoalHistory key={g.id} goal={g} />)}
    </div>
  );
}
