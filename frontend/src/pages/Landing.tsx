import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { PeriodStrip } from "../components/PeriodStrip";
import { StateMark } from "../components/StateMark";
import { readLastGoal } from "../lib/lastGoal";
import type { Roadmap, Task, TaskStatus } from "../types";

const EXAMPLE_GOALS = [
  "Become a Python backend developer",
  "Run my first half marathon",
  "Pay off my credit card debt",
  "Learn conversational Spanish",
  "Build a consistent morning routine",
];

function isoIn(days: number) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

function task(id: number, title: string, status: TaskStatus): Task {
  return { id, title, status, description: "", priority: 0, estimated_effort: "", order_index: id, depends_on: [] };
}

// Illustrative example only (labelled as such on the page).
function exampleRoadmap(): Roadmap {
  const started = new Date();
  started.setDate(started.getDate() - 24);
  return {
    id: 0,
    version: 1,
    summary: "",
    active: true,
    overall_progress: 22,
    current_phase: "Base building",
    current_milestone: "Run 5 km without stopping",
    next_action: "Easy 25-minute run",
    started_at: started.toISOString().slice(0, 10),
    phases: [
      {
        id: 1,
        title: "Get moving",
        objective: "",
        order_index: 0,
        milestones: [
          { id: 1, title: "", description: "", status: "COMPLETED", target_date: isoIn(-3), order_index: 0, tasks: [task(1, "", "COMPLETED"), task(2, "", "COMPLETED")] },
        ],
      },
      {
        id: 2,
        title: "Base building",
        objective: "",
        order_index: 1,
        milestones: [
          { id: 2, title: "", description: "", status: "IN_PROGRESS", target_date: isoIn(20), order_index: 0, tasks: [task(3, "", "COMPLETED"), task(4, "", "NOT_STARTED")] },
          { id: 3, title: "", description: "", status: "NOT_STARTED", target_date: isoIn(45), order_index: 1, tasks: [task(5, "", "NOT_STARTED"), task(6, "", "NOT_STARTED")] },
        ],
      },
      {
        id: 3,
        title: "Long runs",
        objective: "",
        order_index: 2,
        milestones: [{ id: 4, title: "", description: "", status: "NOT_STARTED", target_date: isoIn(95), order_index: 0, tasks: [task(7, "", "NOT_STARTED"), task(8, "", "NOT_STARTED"), task(9, "", "NOT_STARTED")] }],
      },
      {
        id: 4,
        title: "Taper & race",
        objective: "",
        order_index: 3,
        milestones: [{ id: 5, title: "", description: "", status: "NOT_STARTED", target_date: isoIn(125), order_index: 0, tasks: [task(10, "", "NOT_STARTED"), task(11, "", "NOT_STARTED")] }],
      },
    ],
  };
}

export function Landing() {
  const navigate = useNavigate();
  const [goal, setGoal] = useState("");
  const lastGoal = readLastGoal();

  function start(e: FormEvent) {
    e.preventDefault();
    navigate("/create", { state: { prefillTitle: goal.trim() } });
  }

  return (
    <div className="page">
      <section className="landing-hero">
        <div>
          <h1>
            You don't need to know <em>the next step.</em>
          </h1>
          <p className="lede">
            Tell NextStep AI what you want to achieve. It asks a few questions about you, builds a dated plan,
            and always shows the one thing to do next. When life gets in the way, check in and the plan adjusts.
          </p>
          <form className="goal-starter" onSubmit={start}>
            <label htmlFor="starter" className="visually-hidden">
              Your goal
            </label>
            <input
              id="starter"
              type="text"
              placeholder="e.g. Run my first half marathon"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
            />
            <button className="btn btn-primary" type="submit">
              Plan it
              <ArrowRight size={18} aria-hidden="true" />
            </button>
          </form>
          <div className="example-row" aria-label="Example goals">
            {EXAMPLE_GOALS.map((g) => (
              <button
                key={g}
                type="button"
                className="example-chip"
                onClick={() => navigate("/create", { state: { prefillTitle: g } })}
              >
                {g}
              </button>
            ))}
          </div>
        </div>

        <figure style={{ margin: 0 }}>
          <PeriodStrip roadmap={exampleRoadmap()} />
          <div className="session" style={{ marginTop: 12 }}>
            <h2 style={{ fontSize: "1.6rem" }}>Easy 25-minute run</h2>
            <p className="desc">Conversational pace, then 5 minutes of stretching. Done when you've logged it.</p>
            <ul className="tasklist" style={{ marginTop: 12 }}>
              <li className="task is-done">
                <StateMark status="COMPLETED" />
                <span className="task-main task-title">Buy proper running shoes</span>
              </li>
              <li className="task">
                <StateMark status="IN_PROGRESS" />
                <span className="task-main task-title">Run 5 km without stopping</span>
              </li>
            </ul>
          </div>
          <figcaption className="strip-note">Example plan for a half marathon, for illustration.</figcaption>
        </figure>
      </section>

      <section className="steps-band" aria-label="How it works">
        {[
          ["Say the goal", "Broad is fine: a skill, a job, a race, a habit, a debt."],
          ["Answer a few questions", "Only what changes the plan: your level, time, budget, limits."],
          ["Get a dated plan", "Phases, milestones and tasks, sized to your week."],
          ["Check in, it adapts", "Tell it what you finished or where you're stuck."],
        ].map(([title, text], i) => (
          <div key={title}>
            <span className="n">{i + 1}</span>
            <h3>{title}</h3>
            <p>{text}</p>
          </div>
        ))}
      </section>

      {lastGoal && (
        <section className="panel resume">
          <div>
            <h3>Pick up where you left off</h3>
            <p className="muted">{lastGoal.title}</p>
          </div>
          <Link
            className="btn btn-ink"
            to={lastGoal.hasRoadmap ? `/goals/${lastGoal.id}/dashboard` : `/goals/${lastGoal.id}/discovery`}
          >
            Continue
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </section>
      )}
    </div>
  );
}
