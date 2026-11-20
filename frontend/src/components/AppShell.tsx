import { useEffect, useState, type ReactNode } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { CalendarRange, Flag, MessageSquareText, Plus, Settings as SettingsIcon } from "lucide-react";
import { readLastGoal, type LastGoal } from "../lib/lastGoal";
import { ThemeToggle } from "./ThemeToggle";

function useLastGoal(): LastGoal | null {
  const [goal, setGoal] = useState<LastGoal | null>(() => readLastGoal());
  useEffect(() => {
    const update = () => setGoal(readLastGoal());
    window.addEventListener("nextstep:lastgoal", update);
    window.addEventListener("storage", update);
    return () => {
      window.removeEventListener("nextstep:lastgoal", update);
      window.removeEventListener("storage", update);
    };
  }, []);
  return goal;
}

function BrandMark() {
  // Three rising blocks with a marker line: a training block in miniature.
  return (
    <svg className="brand-mark" viewBox="0 0 22 22" aria-hidden="true">
      <rect x="1" y="12" width="5" height="9" rx="1.5" fill="#3a9e69" />
      <rect x="8.5" y="7" width="5" height="14" rx="1.5" fill="#5b86e5" />
      <rect x="16" y="2" width="5" height="19" rx="1.5" fill="#cdd6e8" />
      <rect x="10" y="1" width="2" height="21" rx="1" fill="#f0735f" />
    </svg>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const lastGoal = useLastGoal();
  const location = useLocation();
  const base = lastGoal ? `/goals/${lastGoal.id}` : null;
  const ready = !!(base && lastGoal?.hasRoadmap);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [location.pathname]);

  const links = ready
    ? [
        { to: `${base}/dashboard`, label: "Plan", icon: Flag },
        { to: `${base}/roadmap`, label: "Roadmap", icon: CalendarRange },
        { to: `${base}/checkin`, label: "Check-in", icon: MessageSquareText },
      ]
    : [];

  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="topbar">
        <div className="topbar-inner">
          <Link to={ready ? `${base}/dashboard` : "/"} className="brand" aria-label="NextStep AI home">
            <BrandMark />
            <span>
              NEXTSTEP <em>AI</em>
            </span>
          </Link>
          {links.length > 0 && (
            <nav className="mainnav" aria-label="Goal">
              {links.map((l) => (
                <NavLink key={l.to} to={l.to} className={({ isActive }) => (isActive ? "active" : "")}>
                  {l.label}
                </NavLink>
              ))}
            </nav>
          )}
          <div className="topbar-actions">
            <Link to="/create" className="btn btn-onshell btn-sm hide-sm">
              <Plus size={16} aria-hidden="true" />
              New goal
            </Link>
            <ThemeToggle />
            <NavLink to="/settings" className="btn btn-onshell btn-sm" aria-label="Settings">
              <SettingsIcon size={16} aria-hidden="true" />
            </NavLink>
            {ready && (
              <Link to={`${base}/checkin`} className="btn btn-primary btn-sm hide-sm">
                Check in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main id="main">{children}</main>

      {links.length > 0 && (
        <nav className="bottomnav" aria-label="Goal">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => (isActive ? "active" : "")}>
              <Icon size={20} aria-hidden="true" />
              {label}
            </NavLink>
          ))}
          <NavLink to="/create" className={({ isActive }) => (isActive ? "active" : "")}>
            <Plus size={20} aria-hidden="true" />
            New goal
          </NavLink>
        </nav>
      )}
    </>
  );
}
