/** Remembers the goal the visitor last worked on, so the nav can link to its
 * plan, roadmap and check-in. Browser storage can be unavailable (private
 * mode, blocked site data), so every access is guarded. */

const KEY = "nextstep_last_goal";

export interface LastGoal {
  id: number;
  title: string;
  hasRoadmap: boolean;
}

export function readLastGoal(): LastGoal | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const value = JSON.parse(raw) as LastGoal;
    return typeof value?.id === "number" ? value : null;
  } catch {
    return null;
  }
}

export function writeLastGoal(goal: LastGoal): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(goal));
    window.dispatchEvent(new Event("nextstep:lastgoal"));
  } catch {
    // storage unavailable; navigation just won't remember the goal
  }
}
