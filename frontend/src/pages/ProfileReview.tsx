import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { AiWait } from "../components/AiWait";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingButton } from "../components/LoadingButton";
import { PeriodStripSkeleton } from "../components/PeriodStrip";
import { writeLastGoal } from "../lib/lastGoal";
import { ApiError, api } from "../services/api";
import type { Goal } from "../types";

const FIELD_LABELS: [string, string][] = [
  ["desired_outcome", "What success looks like"],
  ["current_level", "Where you are now"],
  ["time_per_week", "Time per week"],
  ["budget_resources", "Budget and resources"],
  ["available_tools", "Tools you have"],
  ["previous_experience", "Previous experience"],
];

const LIST_FIELDS: [string, string][] = [
  ["constraints", "Constraints"],
  ["preferences", "Preferences"],
  ["known_strengths", "Strengths"],
  ["known_weaknesses", "To work on"],
];

interface Gap {
  area?: string;
  description?: string;
  importance?: number;
}

const isBlank = (v: unknown) => !v || (typeof v === "string" && /^not specified\.?$/i.test(v.trim()));

export function ProfileReview() {
  const { goalId } = useParams();
  const numericGoalId = Number(goalId);
  const navigate = useNavigate();

  const [goal, setGoal] = useState<Goal | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setGoal(await api.getGoal(numericGoalId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load your profile.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [numericGoalId]);

  async function handleGenerateRoadmap() {
    setGenerating(true);
    setError(null);
    try {
      await api.generateRoadmap(numericGoalId);
      if (goal) writeLastGoal({ id: goal.id, title: goal.title, hasRoadmap: true });
      navigate(`/goals/${numericGoalId}/dashboard`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't build your plan. Please try again.");
      setGenerating(false);
    }
  }

  if (generating) {
    return (
      <div className="page page-narrow">
        <div className="panel">
          <AiWait
            title="Building your plan"
            steps={["Splitting the goal into phases", "Setting milestones and dates", "Writing concrete tasks", "Checking it fits your week"]}
            typical="20-60 seconds"
          >
            <PeriodStripSkeleton />
          </AiWait>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="page page-narrow">
        <div className="panel empty" role="status">
          <span className="spinner" style={{ color: "var(--blue)", display: "inline-block" }} aria-hidden="true" />
          <p>Loading your profile…</p>
        </div>
      </div>
    );
  }

  if (!goal) {
    return (
      <div className="page page-narrow">
        {error && <ErrorBanner message={error} onRetry={load} />}
        <EmptyState title="Goal not found" description="This goal may have been removed." />
      </div>
    );
  }

  const profile = goal.profile as Record<string, unknown>;
  const gaps = (Array.isArray(profile.gaps) ? profile.gaps : []) as Gap[];
  const hasProfile = Object.keys(profile).length > 0;

  return (
    <div className="page page-narrow">
      <div className="page-head">
        <div>
          <h1>Here's what we understood</h1>
          <p className="lede">Check it before we build your plan. If something's off, answer a few more questions.</p>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      <section className="panel">
        <h2 className="section-title">
          {goal.title}
          {goal.category && <small>{goal.category}</small>}
        </h2>
        {hasProfile ? (
          <dl className="profile-grid" style={{ margin: 0 }}>
            {FIELD_LABELS.filter(([key]) => !isBlank(profile[key])).map(([key, label]) => (
              <div key={key}>
                <dt>{label}</dt>
                <dd>{String(profile[key])}</dd>
              </div>
            ))}
            {LIST_FIELDS.map(([key, label]) => {
              const items = Array.isArray(profile[key]) ? (profile[key] as string[]) : [];
              if (!items.length) return null;
              return (
                <div key={key}>
                  <dt>{label}</dt>
                  <dd className="tags">
                    {items.map((item) => (
                      <span key={item} className="tag">
                        {item}
                      </span>
                    ))}
                  </dd>
                </div>
              );
            })}
          </dl>
        ) : (
          <p className="muted">No profile yet. Answer the questions first.</p>
        )}
      </section>

      {gaps.length > 0 && (
        <section className="panel">
          <h2 className="section-title">
            Gaps to close <small>most important first</small>
          </h2>
          {gaps.map((gap, idx) => (
            <div className="gap-row" key={idx}>
              <div>
                <strong>{gap.area ?? "Gap"}</strong>
                <p className="muted" style={{ fontSize: "0.95rem" }}>
                  {gap.description}
                </p>
              </div>
              <div>
                <div className="gap-meter" role="img" aria-label={`Importance ${Math.round((gap.importance ?? 0.5) * 100)}%`}>
                  <i style={{ width: `${Math.round((gap.importance ?? 0.5) * 100)}%` }} />
                </div>
              </div>
            </div>
          ))}
        </section>
      )}

      <div className="form-foot">
        <button type="button" className="btn btn-quiet" onClick={() => navigate(`/goals/${numericGoalId}/discovery`)}>
          <ArrowLeft size={18} aria-hidden="true" />
          Answer more questions
        </button>
        <LoadingButton onClick={handleGenerateRoadmap} disabled={!hasProfile}>
          Build my plan
          <ArrowRight size={18} aria-hidden="true" />
        </LoadingButton>
      </div>
    </div>
  );
}
