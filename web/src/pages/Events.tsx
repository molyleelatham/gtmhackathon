import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { Loading, ErrorBox } from "./Dashboard";

export function Events() {
  const { data, error, loading } = useAsync(() => api.listEvents(), []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Events</h1>
        <p className="text-sm text-gray-400">
          Conferences detected from your calendar. Open one to run the before-meet pipeline.
        </p>
      </header>

      {loading && <Loading />}
      {error && <ErrorBox message={error} />}

      <div className="grid gap-4 md:grid-cols-2">
        {data?.map((e) => (
          <Link
            key={e.id}
            to={`/events/${e.id}`}
            className="rounded-xl border border-ink-600 bg-ink-800 p-5 transition hover:border-warmth-warm/50"
          >
            <div className="flex items-start justify-between">
              <h2 className="text-lg font-medium">{e.name}</h2>
              <span className="rounded-full bg-ink-700 px-2 py-0.5 text-xs text-gray-300">
                {Math.round(e.confidence * 100)}% match
              </span>
            </div>
            <div className="mt-1 text-sm text-gray-400">{e.location ?? "—"}</div>
            <div className="mt-4 flex items-center gap-4 text-xs text-gray-500">
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
        <p className="text-sm text-gray-500">
          No events yet — click “Connect calendar” on the dashboard.
        </p>
      )}
    </div>
  );
}
