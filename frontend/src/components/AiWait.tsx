import { useEffect, useState, type ReactNode } from "react";
import { Check } from "lucide-react";

interface AiWaitProps {
  title: string;
  /** What is happening, in order. The highlighted step advances on a timer:
   * it describes the work honestly, it does not track the server. */
  steps: string[];
  /** Typical duration shown to the user, e.g. "20-40 seconds". */
  typical: string;
  children?: ReactNode;
}

const STEP_MS = 6000;

export function AiWait({ title, steps, typical, children }: AiWaitProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const id = window.setInterval(() => setElapsed(Date.now() - started), 1000);
    return () => window.clearInterval(id);
  }, []);

  const active = Math.min(steps.length - 1, Math.floor(elapsed / STEP_MS));
  const seconds = Math.floor(elapsed / 1000);

  return (
    <div className="aiwait" role="status" aria-live="polite">
      {children}
      <h2 style={{ marginTop: children ? 24 : 0 }}>{title}</h2>
      <ol className="aiwait-steps">
        {steps.map((step, i) => (
          <li key={step} className={i < active ? "past" : i === active ? "now" : ""}>
            {i < active ? (
              <Check size={18} aria-hidden="true" />
            ) : i === active ? (
              <span className="spinner" style={{ color: "var(--red)" }} aria-hidden="true" />
            ) : (
              <span style={{ width: 18, display: "inline-block" }} aria-hidden="true" />
            )}
            {step}
          </li>
        ))}
      </ol>
      <p className="aiwait-time">
        <span className="num">{seconds}s</span> · usually {typical}
        {seconds > 45 && ". The server may be waking up; hang on."}
      </p>
    </div>
  );
}
