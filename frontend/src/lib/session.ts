/** The signed-in username. There is no password: the username is only a name
 * that groups a person's goals and history, so it lives in browser storage. */

const KEY = "nextstep_user";

export interface SessionUser {
  id: number;
  username: string;
}

export function readUser(): SessionUser | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const value = JSON.parse(raw) as SessionUser;
    return typeof value?.id === "number" && typeof value?.username === "string" ? value : null;
  } catch {
    return null;
  }
}

export function writeUser(user: SessionUser | null): void {
  try {
    if (user) localStorage.setItem(KEY, JSON.stringify(user));
    else localStorage.removeItem(KEY);
  } catch {
    // storage blocked: the user stays signed in for this page view only
  }
  window.dispatchEvent(new Event("nextstep:user"));
}
