import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingButton } from "../components/LoadingButton";
import { writeUser } from "../lib/session";
import { ApiError, api } from "../services/api";

type Mode = "signin" | "create";

export function SignIn() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>("signin");
  const [username, setUsername] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  const trimmed = username.trim();
  const valid = trimmed.length >= 2;

  async function submit(forceMode?: Mode) {
    const active = forceMode ?? mode;
    if (!valid) return;
    setBusy(true);
    setError(null);
    setNotFound(false);
    try {
      const user = active === "create" ? await api.createUser(trimmed) : await api.signIn(trimmed);
      writeUser(user);
      navigate("/history");
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) setNotFound(true);
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  function switchMode(next: Mode) {
    setMode(next);
    setError(null);
    setNotFound(false);
  }

  return (
    <div className="page page-narrow">
      <div className="page-head">
        <div>
          <h1>{mode === "signin" ? "Welcome back" : "Create your username"}</h1>
          <p className="lede">
            {mode === "signin"
              ? "Enter your username to see your goals and past conversations."
              : "Pick a username. Your goals and history will be saved under it."}
          </p>
        </div>
      </div>

      <div className="seg" role="tablist" aria-label="Account">
        <button type="button" role="tab" aria-selected={mode === "signin"} onClick={() => switchMode("signin")}>
          I have a username
        </button>
        <button type="button" role="tab" aria-selected={mode === "create"} onClick={() => switchMode("create")}>
          Create one
        </button>
      </div>

      {error && <ErrorBanner message={error} />}

      <form
        className="panel"
        noValidate
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          void submit();
        }}
      >
        <div className="field">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            autoComplete="username"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            placeholder="e.g. rohit"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            maxLength={40}
            aria-describedby="username-hint"
            autoFocus
          />
          <span className="hint" id="username-hint">
            2 to 40 characters: letters, numbers, spaces, dots, dashes, underscores. There is no password, so
            don't use a name you want kept private.
          </span>
        </div>
        <LoadingButton type="submit" loading={busy} disabled={!valid} block>
          {mode === "signin" ? "See my history" : "Create username"}
          <ArrowRight size={18} aria-hidden="true" />
        </LoadingButton>
        {notFound && mode === "signin" && (
          <p style={{ marginTop: 16 }} className="muted">
            Never used it before?{" "}
            <button
              type="button"
              className="linklike"
              onClick={() => {
                setMode("create");
                void submit("create");
              }}
            >
              Create “{trimmed}”
            </button>
          </p>
        )}
      </form>
    </div>
  );
}
