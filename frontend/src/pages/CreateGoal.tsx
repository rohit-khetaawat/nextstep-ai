import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { LoadingButton } from "../components/LoadingButton";
import { ErrorBanner } from "../components/ErrorBanner";
import { writeLastGoal } from "../lib/lastGoal";
import { ApiError, api } from "../services/api";

const CATEGORIES = ["", "Learning", "Career", "Fitness", "Health", "Finance", "Business", "Creative", "Personal development"];

export function CreateGoal() {
  const navigate = useNavigate();
  const location = useLocation();
  const prefill = (location.state as { prefillTitle?: string } | null)?.prefillTitle ?? "";

  const [title, setTitle] = useState(prefill);
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmedTitle = title.trim();
  const canSubmit = trimmedTitle.length >= 3 && !submitting;
  const today = new Date().toISOString().slice(0, 10);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      const goal = await api.createGoal({
        title: trimmedTitle,
        description: description.trim(),
        category,
        target_date: targetDate,
      });
      writeLastGoal({ id: goal.id, title: goal.title, hasRoadmap: false });
      navigate(`/goals/${goal.id}/discovery`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save your goal. Check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page page-narrow">
      <div className="page-head">
        <div>
          <h1>What do you want to achieve?</h1>
          <p className="lede">Say it in your own words. Broad is fine: we'll ask what we need to know next.</p>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      <form className="panel" onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="goal-title">Your goal</label>
          <textarea
            id="goal-title"
            placeholder="e.g. Become a Python backend developer"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            minLength={3}
            maxLength={500}
            aria-describedby="goal-title-hint"
            style={{ minHeight: 80 }}
            autoFocus
          />
          <span className="hint" id="goal-title-hint">
            At least 3 characters.
          </span>
        </div>

        <div className="field">
          <label htmlFor="goal-description">Anything else? (optional)</label>
          <textarea
            id="goal-description"
            placeholder="Why it matters, what you've tried, what success would look like."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={2000}
          />
        </div>

        <div className="field-row">
          <div className="field">
            <label htmlFor="goal-category">Category (optional)</label>
            <select id="goal-category" value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORIES.map((c) => (
                <option key={c || "auto"} value={c}>
                  {c || "Let the AI decide"}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="goal-target-date">Target date (optional)</label>
            <input
              id="goal-target-date"
              type="date"
              min={today}
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
            />
          </div>
        </div>

        <LoadingButton type="submit" loading={submitting} disabled={!canSubmit} block>
          Start the questions
          <ArrowRight size={18} aria-hidden="true" />
        </LoadingButton>
      </form>
    </div>
  );
}
