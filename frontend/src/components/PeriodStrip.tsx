import { Link } from "react-router-dom";
import { buildStrip, formatDate } from "../lib/timeline";
import type { Roadmap } from "../types";

interface PeriodStripProps {
  roadmap: Roadmap;
  /** When set, each phase block links to its section on the roadmap page. */
  linkBase?: string;
}

/** The signature: the plan as a training block. Each phase is as wide as its
 * real time span, and a red line marks today. */
export function PeriodStrip({ roadmap, linkBase }: PeriodStripProps) {
  const model = buildStrip(roadmap);
  const shares = model.shares;
  // Blocks are separated by a 4px gap, so share-of-width must be taken from
  // the width left after the gaps, and a position inside block i is shifted
  // by i gaps. One coordinate for blocks, ticks, month labels and TODAY.
  const GAP = 4;
  const gaps = GAP * Math.max(0, shares.length - 1);
  const widthOf = (share: number) => `calc((100% - ${gaps}px) * ${share.toFixed(5)})`;
  const pct = (at: number) => {
    let cum = 0;
    let index = 0;
    for (let i = 0; i < shares.length; i++) {
      index = i;
      if (at <= cum + shares[i]) break;
      cum += shares[i];
    }
    return `calc((100% - ${gaps}px) * ${at.toFixed(5)} + ${index * GAP}px)`;
  };

  const description = model.phases
    .map((p) => {
      const range = p.start && p.end ? `${formatDate(p.start)} to ${formatDate(p.end)}` : "";
      return `${p.phase.title}: ${p.state === "done" ? "done" : p.state === "current" ? "in progress" : "upcoming"}, ${p.doneTasks} of ${p.totalTasks} tasks ${range}`;
    })
    .join("; ");

  return (
    <section className="strip" aria-label="Plan timeline">
      <p className="visually-hidden">{description}</p>
      {model.dated && (
        <div className="strip-scale" aria-hidden="true">
          {model.ticks.map((t) => (
            <span key={`${t.label}-${t.at}`} style={{ left: pct(t.at) }}>
              {t.label}
            </span>
          ))}
          {model.end && (
            <span style={{ left: "auto", right: 0, transform: "none" }}>
              {model.end.toLocaleDateString(undefined, { month: "short", year: "numeric" }).toUpperCase()}
            </span>
          )}
        </div>
      )}

      <div className={`strip-track ${model.today !== null ? "has-today" : ""}`} aria-hidden="true">
        {model.today !== null && (
          <>
            <div className="today-label" style={{ left: pct(model.today) }}>
              TODAY
            </div>
            <div className="today-line" style={{ left: pct(model.today) }} />
          </>
        )}
        <div className="strip-blocks">
          {model.phases.map((p, i) => {
            const body = (
              <>
                <span className="t">{p.phase.title}</span>
                <span className="s">{p.state === "done" ? "Done" : `${p.doneTasks}/${p.totalTasks} tasks`}</span>
              </>
            );
            const style = { flex: `0 0 ${widthOf(shares[i])}`, ["--i" as string]: i };
            return linkBase ? (
              <Link
                key={p.phase.id}
                to={`${linkBase}#phase-${p.phase.id}`}
                className={`strip-block ${p.state}`}
                style={style}
                tabIndex={-1}
              >
                {body}
              </Link>
            ) : (
              <div key={p.phase.id} className={`strip-block ${p.state}`} style={style}>
                {body}
              </div>
            );
          })}
        </div>
        <div className="strip-ticks">
          {model.phases.map((p, i) => (
            <div key={p.phase.id} style={{ flex: `0 0 ${widthOf(shares[i])}` }}>
              {p.milestones.map((m, j) => (
                <i key={j} className={m.state === "open" ? "" : m.state} style={{ flex: `${m.weight} 1 0` }} />
              ))}
            </div>
          ))}
        </div>
      </div>

      {!model.dated && <p className="strip-note">Block widths follow the number of tasks; the plan has no dates yet.</p>}
      {model.dated && model.approximate && (
        <p className="strip-note">Some phase dates were missing, so their length is estimated.</p>
      )}
    </section>
  );
}

export function PeriodStripSkeleton() {
  return (
    <div className="strip is-loading" aria-hidden="true">
      <div className="strip-blocks">
        {[3, 5, 4, 3].map((f, i) => (
          <div key={i} className="strip-block" style={{ flex: `${f} 1 0`, padding: 0 }} />
        ))}
      </div>
    </div>
  );
}
