import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { Loading, ErrorBox } from "./Dashboard";

export function Events() {
  const { data, error, loading } = useAsync(() => api.listEvents(), []);

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">Events</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Conferences detected from your calendar. Open one to run the before-meet pipeline.
        </p>
      </header>

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
          No events yet — connect your calendar from the dashboard.
        </p>
      )}
    </div>
  );
}
