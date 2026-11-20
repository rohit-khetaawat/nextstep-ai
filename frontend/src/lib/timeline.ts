import type { Phase, Roadmap } from "../types";

const DAY = 86_400_000;
const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

export type PhaseState = "done" | "current" | "future";

export interface StripPhase {
  phase: Phase;
  state: PhaseState;
  /** Share of the strip's width, 0-1. Proportional to real time when dated. */
  weight: number;
  start: Date | null;
  end: Date | null;
  doneTasks: number;
  totalTasks: number;
  milestones: { weight: number; state: "done" | "part" | "open" }[];
}

export interface StripModel {
  phases: StripPhase[];
  dated: boolean;
  start: Date | null;
  end: Date | null;
  /** Position of today on the strip, 0-1, or null when undated. */
  today: number | null;
  ticks: { label: string; at: number }[];
  /** Each phase's displayed share of the width (short phases floored so they stay legible). */
  shares: number[];
  /** True when some AI dates were missing or out of order and were estimated. */
  approximate: boolean;
}

export function parseDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const iso = /^(\d{4})-(\d{2})(?:-(\d{2}))?/.exec(value.trim());
  if (iso) {
    const d = new Date(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3] ?? 1));
    return Number.isNaN(d.getTime()) ? null : d;
  }
  const t = Date.parse(value);
  return Number.isNaN(t) ? null : new Date(t);
}

export function formatDate(d: Date | null, withYear = false): string {
  if (!d) return "";
  return d.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    ...(withYear ? { year: "numeric" } : {}),
  });
}

/** "Due 12 Dec" style label from an AI target_date string; falls back to the raw text. */
export function dueLabel(raw: string): string {
  const d = parseDate(raw);
  if (!d) return raw;
  return formatDate(d, d.getFullYear() !== new Date().getFullYear());
}

function taskCounts(phase: Phase) {
  const tasks = phase.milestones.flatMap((m) => m.tasks);
  return { done: tasks.filter((t) => t.status === "COMPLETED").length, total: tasks.length };
}

function startOfDay(d: Date) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

export function buildStrip(roadmap: Roadmap, now: Date = new Date()): StripModel {
  const today = startOfDay(now);
  const ordered = [...roadmap.phases].sort((a, b) => a.order_index - b.order_index);
  const currentTitle = roadmap.current_phase;

  // Phase end = latest milestone date in the phase.
  const rawEnds = ordered.map((p) => {
    const dates = p.milestones.map((m) => parseDate(m.target_date)).filter((d): d is Date => !!d);
    return dates.length ? new Date(Math.max(...dates.map((d) => d.getTime()))) : null;
  });

  const datedCount = rawEnds.filter(Boolean).length;
  const dated = ordered.length > 0 && datedCount >= Math.ceil(ordered.length / 2);
  let approximate = dated && datedCount < ordered.length;

  let reachedCurrent = currentTitle == null;
  const states: PhaseState[] = ordered.map((p) => {
    const { done, total } = taskCounts(p);
    if (total > 0 && done === total) return "done";
    if (!reachedCurrent && p.title === currentTitle) {
      reachedCurrent = true;
      return "current";
    }
    return "future";
  });
  if (!states.includes("current")) {
    const firstOpen = states.indexOf("future");
    if (firstOpen >= 0) states[firstOpen] = "current";
  }

  let start: Date | null = null;
  let end: Date | null = null;
  const spans: { start: Date | null; end: Date | null; days: number }[] = [];

  if (dated) {
    const started = parseDate(roadmap.started_at ?? null);
    const firstEnd = rawEnds.find(Boolean)!;
    start = startOfDay(started && started < firstEnd ? started : new Date(Math.min(today.getTime(), firstEnd.getTime() - 14 * DAY)));
    let cursor = start;
    for (let i = 0; i < ordered.length; i++) {
      let e = rawEnds[i];
      if (!e || e.getTime() <= cursor.getTime()) {
        // Missing or out-of-order date: give the phase a two-week stand-in span.
        e = new Date(cursor.getTime() + 14 * DAY);
        approximate = true;
      }
      spans.push({ start: cursor, end: e, days: (e.getTime() - cursor.getTime()) / DAY });
      cursor = e;
    }
    end = cursor;
  } else {
    for (const p of ordered) {
      spans.push({ start: null, end: null, days: Math.max(1, taskCounts(p).total) });
    }
  }

  const totalDays = spans.reduce((s, x) => s + x.days, 0) || 1;

  const phases: StripPhase[] = ordered.map((phase, i) => {
    const { done, total } = taskCounts(phase);
    const ms = [...phase.milestones].sort((a, b) => a.order_index - b.order_index);
    const msTotal = ms.reduce((s, m) => s + Math.max(1, m.tasks.length), 0) || 1;
    return {
      phase,
      state: states[i],
      weight: spans[i].days / totalDays,
      start: spans[i].start,
      end: spans[i].end,
      doneTasks: done,
      totalTasks: total,
      milestones: ms.map((m) => {
        const d = m.tasks.filter((t) => t.status === "COMPLETED").length;
        return {
          weight: Math.max(1, m.tasks.length) / msTotal,
          state: m.tasks.length && d === m.tasks.length ? "done" : d > 0 ? "part" : "open",
        };
      }),
    };
  });

  // Displayed widths: floor short phases at 10%, then renormalise. Dates are
  // mapped onto these displayed blocks piecewise, so TODAY and the month
  // labels always line up with the block they fall in.
  const floored = phases.map((p) => Math.max(p.weight, 0.14));
  const flooredTotal = floored.reduce((s, x) => s + x, 0) || 1;
  const shares = floored.map((x) => x / flooredTotal);
  const toDisplay = (t: number): number => {
    let cum = 0;
    for (let i = 0; i < phases.length; i++) {
      const s = phases[i].start?.getTime();
      const e = phases[i].end?.getTime();
      if (s !== undefined && e !== undefined && t <= e) {
        return cum + shares[i] * Math.max(0, Math.min(1, (t - s) / (e - s || 1)));
      }
      cum += shares[i];
    }
    return 1;
  };

  let todayPos: number | null = null;
  const ticks: { label: string; at: number }[] = [];
  if (dated && start && end) {
    todayPos = toDisplay(today.getTime());

    // Month ticks, thinned so at most ~7 labels show.
    const months: Date[] = [];
    const m = new Date(start.getFullYear(), start.getMonth() + 1, 1);
    while (m <= end) {
      months.push(new Date(m));
      m.setMonth(m.getMonth() + 1);
    }
    const step = Math.max(1, Math.ceil(months.length / 6));
    ticks.push({ label: `${MONTHS[start.getMonth()]} ${start.getFullYear()}`, at: 0 });
    months.forEach((d, idx) => {
      if (idx % step !== step - 1) return;
      const at = toDisplay(d.getTime());
      // Leave room for the start label and the right-aligned end label.
      if (at < 0.1 || at > 0.86) return;
      if (ticks.length && at - ticks[ticks.length - 1].at < 0.08) return;
      // The end label already names the final month.
      if (d.getFullYear() === end!.getFullYear() && d.getMonth() === end!.getMonth()) return;
      ticks.push({ label: d.getMonth() === 0 ? `JAN ${d.getFullYear()}` : MONTHS[d.getMonth()], at });
    });
  }

  return { phases, dated, start, end, today: todayPos, ticks, approximate, shares };
}
