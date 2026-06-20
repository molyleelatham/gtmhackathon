import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useAsync } from "../lib/useAsync";
import { Loading, ErrorBox } from "./Dashboard";

export function Events() {
  const { user } = useAuth();
  const { data, error, loading, reload } = useAsync(() => api.listEvents(), []);
  const [connecting, setConnecting] = useState(false);
  const [connectMsg, setConnectMsg] = useState<string | null>(null);

  async function connectCalendar() {
    setConnecting(true);
    setConnectMsg(null);
    try {
      const result = await api.connect(user?.uid ?? "demo-user");
      const detected = result.events_detected ?? 0;
      setConnectMsg(
        detected > 0
          ? `Connected — ${detected} event(s) discovered from calendar.`
          : "Connected — no new events detected (demo store may already be seeded).",
      );
      reload();
    } catch (e) {
      setConnectMsg(e instanceof Error ? e.message : "Connect failed");
    } finally {
      setConnecting(false);
    }
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">Events</h1>
          <p className="mt-1 text-sm text-ink-muted">
            Conferences detected from your calendar. Connect Google, then run pre-meet or the full
            conference pipeline.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={connecting}
            onClick={connectCalendar}
            className="glass-interactive rounded-xl border border-orange/40 bg-orange/15 px-4 py-2 text-sm font-semibold text-flame disabled:opacity-50"
          >
            {connecting ? "Connecting…" : "Connect calendar"}
          </button>
          <Link to="/pipeline" className="btn-secondary">
            Conference pipeline
          </Link>
        </div>
      </header>

      {connectMsg && (
        <p className="text-sm text-ink-muted">{connectMsg}</p>
      )}

      {loading && <Loading />}
      {error && <ErrorBox message={error} />}

      <div className="grid gap-4 md:grid-cols-2">
        {data?.map((e) => (
          <Link key={e.id} to={`/events/${e.id}`} className="glass glass-interactive p-5">
            <div className="flex items-start justify-between">
              <h2 className="text-lg font-medium text-ink-900">{e.name}</h2>
              <span className="glass-pill border-orange/25 bg-orange/10 text-flame">
                {Math.round(e.confidence * 100)}% match
              </span>
            </div>
            <div className="mt-1 text-sm text-ink-muted">{e.location ?? "—"}</div>
            <div className="mt-4 flex items-center gap-3 text-xs text-ink-faint">
              <span>{e.attendee_count} attendees</span>
              <span>·</span>
              <span>{e.stage.replace("_", " ")}</span>
              <span>·</span>
              <span>{e.premeet_completed ? "pre-meet done" : "pre-meet pending"}</span>
            </div>
          </Link>
        ))}
      </div>
      {data && data.length === 0 && (
        <p className="text-sm text-ink-faint">
          No events yet — click Connect calendar to run onboarding discovery.
        </p>
      )}
    </div>
  );
}
