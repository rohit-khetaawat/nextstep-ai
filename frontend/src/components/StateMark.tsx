import { useId } from "react";
import type { TaskStatus } from "../types";

/** The one state vocabulary used everywhere: open ring, half ring (in
 * progress), filled check (done), hatched amber ring (blocked). */
export function StateMark({ status, size = 20 }: { status: TaskStatus; size?: number }) {
  const hatchId = `hatch-${useId().replace(/:/g, "")}`;
  const common = { width: size, height: size, viewBox: "0 0 20 20", className: "mark", "aria-hidden": true } as const;

  if (status === "COMPLETED") {
    return (
      <svg {...common}>
        <circle cx="10" cy="10" r="9" fill="var(--green)" />
        <path d="M6 10.4l2.6 2.6L14.2 7.4" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (status === "IN_PROGRESS") {
    return (
      <svg {...common}>
        <circle cx="10" cy="10" r="8" fill="none" stroke="var(--blue)" strokeWidth="2" />
        <path d="M10 4a6 6 0 0 1 0 12z" fill="var(--blue)" />
      </svg>
    );
  }
  if (status === "BLOCKED") {
    return (
      <svg {...common}>
        <defs>
          <pattern id={hatchId} width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="2" height="4" fill="var(--amber)" />
          </pattern>
        </defs>
        <circle cx="10" cy="10" r="8" fill={`url(#${hatchId})`} stroke="var(--amber)" strokeWidth="2" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <circle cx="10" cy="10" r="8" fill="none" stroke="var(--line-strong)" strokeWidth="2" />
    </svg>
  );
}

export const STATUS_LABEL: Record<TaskStatus, string> = {
  NOT_STARTED: "Not started",
  IN_PROGRESS: "In progress",
  BLOCKED: "Blocked",
  COMPLETED: "Done",
};
