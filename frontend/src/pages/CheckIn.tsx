import { useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { ArrowRight, CheckCircle2, RefreshCw } from "lucide-react";
import { AiWait } from "../components/AiWait";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingButton } from "../components/LoadingButton";
import { PeriodStripSkeleton } from "../components/PeriodStrip";
import { ApiError, api } from "../services/api";
import type { CheckInResponse } from "../types";

const QUICK_STARTS = [
  "I finished ",
  "I'm stuck on ",
  "I have less time this week because ",
  "Something changed: ",
];

const CATEGORY_LABEL: Record<string, string> = {
  progress: "Progress",
  blocker: "A blocker",
  changed_constraint: "A change in your situation",
  new_information: "New information",
  other: "General update",
};

export function CheckIn() {
  const { goalId } = useParams();
  const numericGoalId = Number(goalId);
  const location = useLocation();
  const prefill = (location.state as { prefill?: string } | null)?.prefill ?? "";

  const [message, setMessage] = useState(prefill);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CheckInResponse | null>(null);
  const [adapting, setAdapting] = useState(false);
  const [adaptExplanation, setAdaptExplanation] = useState<string | null>(null);

  async function handleSubmit() {
    if (!message.trim()) return;
    setSubmitting(true);
    setError(null);
    setResult(null);
    setAdaptExplanation(null);
    try {
      setResult(await api.submitCheckin(numericGoalId, message.trim()));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't send your check-in.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAdapt() {
    setAdapting(true);
    setError(null);
    try {
      const response = await api.adaptRoadmap(numericGoalId);
      setAdaptExplanation(response.explanation);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't adjust your plan.");
    } finally {
      setAdapting(false);
    }
  }

  if (submitting || adapting) {
    return (
      <div className="page page-narrow">
        <div className="panel">
          {submitting ? (
            <AiWait
              title="Reading your check-in"
              steps={["Matching it to your tasks", "Spotting progress and blockers"]}
              typical="5-15 seconds"
            />
          ) : (
            <AiWait
              title="Adjusting your plan"
              steps={["Keeping finished work", "Reworking what's left", "Re-checking dates and workload"]}
              typical="20-60 seconds"
            >
              <PeriodStripSkeleton />
            </AiWait>
          )}
        </div>
      </div>
    );
  }

  const cls = result?.classification;

  return (
    <div className="page page-narrow">
      <div className="page-head">
        <div>
          <h1>How's it going?</h1>
          <p className="lede">
            Say what you finished, where you're stuck, or what changed. Plain words are fine.
          </p>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {!adaptExplanation && (
        <form
          className="panel"
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
        >
          <div className="quick-prompts" aria-label="Quick starts">
            {QUICK_STARTS.map((q) => (
              <button key={q} type="button" className="example-chip" onClick={() => setMessage(q)}>
                {q.replace(/[: ]+$/, "").replace(/ because$/, "")}…
              </button>
            ))}
          </div>
          <div className="field">
            <label htmlFor="checkin-message" className="visually-hidden">
              Your check-in
            </label>
            <textarea
              id="checkin-message"
              placeholder="e.g. Finished the FastAPI tutorial, but I'm stuck on JWT auth and only had 4 hours this week."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              maxLength={2000}
              style={{ minHeight: 140 }}
            />
          </div>
          <LoadingButton type="submit" disabled={!message.trim()} block>
            Send check-in
          </LoadingButton>
        </form>
      )}

      {cls && !adaptExplanation && (
        <section className="panel understood" aria-live="polite">
          <h2 className="section-title">What we understood</h2>
          {cls.summary && <p>{cls.summary}</p>}
          <dl>
            <div>
              <dt>Type</dt>
              <dd>{CATEGORY_LABEL[cls.category] ?? cls.category}</dd>
            </div>
            {cls.completed_task_titles.length > 0 && (
              <div>
                <dt>Marked done</dt>
                <dd>{cls.completed_task_titles.join(", ")}</dd>
              </div>
            )}
            {cls.blocked_task_titles.length > 0 && (
              <div>
                <dt>Marked blocked</dt>
                <dd>{cls.blocked_task_titles.join(", ")}</dd>
              </div>
            )}
            {cls.blocker_description && (
              <div>
                <dt>The blocker</dt>
                <dd>{cls.blocker_description}</dd>
              </div>
            )}
          </dl>
          <div className="actions" style={{ marginTop: 20 }}>
            {cls.should_adapt_roadmap ? (
              <>
                <LoadingButton onClick={handleAdapt}>
                  <RefreshCw size={18} aria-hidden="true" />
                  Adjust my plan
                </LoadingButton>
                <Link to={`/goals/${numericGoalId}/dashboard`} className="btn btn-quiet">
                  Keep the plan as is
                </Link>
              </>
            ) : (
              <Link to={`/goals/${numericGoalId}/dashboard`} className="btn btn-ink">
                Back to my plan
                <ArrowRight size={18} aria-hidden="true" />
              </Link>
            )}
          </div>
        </section>
      )}

      {adaptExplanation && (
        <section className="panel">
          <div className="banner banner-success" style={{ marginBottom: 16 }}>
            <CheckCircle2 size={18} aria-hidden="true" />
            <div className="banner-body">
              <strong>Your plan is updated.</strong> {adaptExplanation}
            </div>
          </div>
          <Link to={`/goals/${numericGoalId}/dashboard`} className="btn btn-primary">
            See the new plan
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </section>
      )}
    </div>
  );
}
