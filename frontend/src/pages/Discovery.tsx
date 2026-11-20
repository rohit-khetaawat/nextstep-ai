import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Check, Info } from "lucide-react";
import { AiWait } from "../components/AiWait";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingButton } from "../components/LoadingButton";
import { ApiError, api } from "../services/api";
import type { AnswerSubmission, Question } from "../types";

type AnswerMap = Record<string, string | string[]>;
type Phase = "questions" | "loading" | "profiling";

export function Discovery() {
  const { goalId } = useParams();
  const numericGoalId = Number(goalId);
  const navigate = useNavigate();

  const [questions, setQuestions] = useState<Question[] | null>(null);
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [answeredCount, setAnsweredCount] = useState(0);
  const [phase, setPhase] = useState<Phase>("loading");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<{ questions: Question[]; answers: AnswerMap }[]>([]);

  async function loadNextQuestions() {
    setPhase("loading");
    setError(null);
    try {
      const result = await api.getNextQuestions(numericGoalId);
      if (result.is_complete || result.questions.length === 0) {
        setPhase("profiling");
        await api.finalizeProfile(numericGoalId);
        navigate(`/goals/${numericGoalId}/profile`);
        return;
      }
      setQuestions(result.questions);
      setAnswers({});
      setPhase("questions");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load the next questions.");
      setPhase("questions");
    }
  }

  useEffect(() => {
    loadNextQuestions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [numericGoalId]);

  function setAnswer(questionId: string, value: string | string[]) {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  }

  function toggleMulti(questionId: string, option: string) {
    setAnswers((prev) => {
      const current = Array.isArray(prev[questionId]) ? (prev[questionId] as string[]) : [];
      const next = current.includes(option) ? current.filter((o) => o !== option) : [...current, option];
      return { ...prev, [questionId]: next };
    });
  }

  const isAnswered = (q: Question) => {
    const value = answers[q.id];
    if (Array.isArray(value)) return value.length > 0;
    return typeof value === "string" && value.trim().length > 0;
  };
  const allRequiredAnswered = questions?.every((q) => !q.required || isAnswered(q)) ?? false;

  async function handleContinue() {
    if (!questions) return;
    setSubmitting(true);
    setError(null);
    try {
      const submissions: AnswerSubmission[] = questions
        .filter((q) => answers[q.id] !== undefined)
        .map((q) => ({ question_id: q.id, question_text: q.text, answer: answers[q.id] }));
      await api.submitAnswers(numericGoalId, submissions);
      setHistory((prev) => [...prev, { questions, answers }]);
      setAnsweredCount((n) => n + submissions.length);
      await loadNextQuestions();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save your answers.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleBack() {
    const previous = history[history.length - 1];
    if (!previous) return;
    setHistory((prev) => prev.slice(0, -1));
    setQuestions(previous.questions);
    setAnswers(previous.answers);
  }

  const segments = Math.max(6, answeredCount + (questions?.length ?? 0));

  return (
    <div className="page page-narrow">
      <div className="page-head" style={{ marginBottom: 0 }}>
        <div>
          <h1>A few questions about you</h1>
          <p className="lede">Usually 5 to 8 in total. Each one changes your plan.</p>
        </div>
      </div>

      <div className="interview-progress" aria-hidden="true">
        {Array.from({ length: segments }, (_, i) => (
          <i key={i} className={i < answeredCount ? "done" : ""} />
        ))}
      </div>
      <p className="visually-hidden" aria-live="polite">
        {answeredCount} questions answered
      </p>

      {error && <ErrorBanner message={error} onRetry={loadNextQuestions} />}

      {phase === "loading" && (
        <div className="panel">
          <AiWait
            title={answeredCount ? "Choosing what to ask next" : "Reading your goal"}
            steps={
              answeredCount
                ? ["Reviewing your answers", "Finding what's still unclear", "Writing the next questions"]
                : ["Understanding the goal", "Working out what matters most", "Writing the first questions"]
            }
            typical="5-20 seconds"
          />
        </div>
      )}

      {phase === "profiling" && (
        <div className="panel">
          <AiWait
            title="Building your profile"
            steps={["Summarising your answers", "Comparing where you are to where you want to be", "Listing the gaps to close"]}
            typical="10-30 seconds"
          />
        </div>
      )}

      {phase === "questions" && questions && (
        <form
          className="panel"
          onSubmit={(e) => {
            e.preventDefault();
            if (allRequiredAnswered) handleContinue();
          }}
        >
          {questions.map((question) => (
            <QuestionField
              key={question.id}
              question={question}
              value={answers[question.id]}
              onChange={(value) => setAnswer(question.id, value)}
              onToggleMulti={(option) => toggleMulti(question.id, option)}
            />
          ))}

          <div className="form-foot">
            <button type="button" className="btn btn-quiet" onClick={handleBack} disabled={history.length === 0 || submitting}>
              <ArrowLeft size={18} aria-hidden="true" />
              Previous
            </button>
            <LoadingButton type="submit" loading={submitting} disabled={!allRequiredAnswered}>
              Continue
              <ArrowRight size={18} aria-hidden="true" />
            </LoadingButton>
          </div>
        </form>
      )}
    </div>
  );
}

interface QuestionFieldProps {
  question: Question;
  value: string | string[] | undefined;
  onChange: (value: string) => void;
  onToggleMulti: (option: string) => void;
}

function QuestionField({ question, value, onChange, onToggleMulti }: QuestionFieldProps) {
  const labelId = `${question.id}-label`;
  const isChoice = question.type === "single_choice" || question.type === "multi_choice";
  const multi = question.type === "multi_choice";

  return (
    <fieldset className="question" aria-labelledby={labelId}>
      {isChoice ? (
        <legend id={labelId} className="qtext" style={{ padding: 0 }}>
          {question.text}
          {!question.required && <span className="muted" style={{ fontSize: "1rem", fontWeight: 500 }}> (optional)</span>}
        </legend>
      ) : (
        <label id={labelId} htmlFor={question.id} className="qtext" style={{ display: "block" }}>
          {question.text}
          {!question.required && <span className="muted" style={{ fontSize: "1rem", fontWeight: 500 }}> (optional)</span>}
        </label>
      )}
      {question.reason ? (
        <p className="why">
          <Info size={15} aria-hidden="true" />
          {question.reason}
        </p>
      ) : (
        <div style={{ height: 12 }} />
      )}

      {isChoice && (
        <div className="choices" role={multi ? "group" : "radiogroup"} aria-labelledby={labelId}>
          {question.options.map((option) => {
            const selected = multi ? Array.isArray(value) && value.includes(option) : value === option;
            return (
              <label key={option} className={`choice ${multi ? "multi" : ""} ${selected ? "selected" : ""}`}>
                <input
                  type={multi ? "checkbox" : "radio"}
                  name={question.id}
                  checked={selected}
                  onChange={() => (multi ? onToggleMulti(option) : onChange(option))}
                />
                <span className="tick" aria-hidden="true">
                  {selected && <Check size={14} strokeWidth={3} />}
                </span>
                {option}
              </label>
            );
          })}
        </div>
      )}

      {question.type === "numeric" && (
        <input
          id={question.id}
          type="number"
          inputMode="decimal"
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value)}
          style={{ maxWidth: 220 }}
        />
      )}
      {question.type === "date" && (
        <input
          id={question.id}
          type="date"
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value)}
          style={{ maxWidth: 220 }}
        />
      )}
      {question.type === "short_text" && (
        <input id={question.id} type="text" value={typeof value === "string" ? value : ""} onChange={(e) => onChange(e.target.value)} />
      )}
      {question.type === "long_text" && (
        <textarea id={question.id} value={typeof value === "string" ? value : ""} onChange={(e) => onChange(e.target.value)} />
      )}
    </fieldset>
  );
}
