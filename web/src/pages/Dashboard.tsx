import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { StatCard } from "../components/StatCard";
import { WarmthBadge } from "../components/WarmthBadge";

export function Dashboard() {
  const { data, error, loading, reload } = useAsync(() => api.dashboard(), []);

  async function connect() {
    await api.connect();
    reload();
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-gray-400">
            Your personal CRM across the conference lifecycle.
          </p>
        </div>
        <button
          onClick={connect}
          className="rounded-lg bg-warmth-warm/90 px-4 py-2 text-sm font-medium text-ink-900 hover:bg-warmth-warm"
        >
          Connect calendar
        </button>
      </header>

      {loading && <Loading />}
      {error && <ErrorBox message={error} />}

      {data && (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Events" value={data.events} hint="Detected conferences" />
            <StatCard label="Connections" value={data.connections} hint="Across all events" />
            <StatCard label="Hot leads" value={data.hot_leads} hint="Warmth ≥ 70" />
            <StatCard label="In CRM" value={data.leads_in_crm} hint="Pushed to Zero" />
          </div>

          <section className="grid gap-6 lg:grid-cols-2">
            <Panel title="Upcoming events">
              <ul className="divide-y divide-ink-700">
                {data.upcoming_events.map((e) => (
                  <li key={e.id} className="flex items-center justify-between py-3">
                    <div>
                      <Link to={`/events/${e.id}`} className="font-medium hover:underline">
                        {e.name}
                      </Link>
                      <div className="text-xs text-gray-500">
                        {e.location ?? "—"} · {e.attendee_count} attendees
                      </div>
                    </div>
                    <span className="rounded-full bg-ink-700 px-2 py-0.5 text-xs text-gray-300">
                      {e.stage.replace("_", " ")}
                    </span>
                  </li>
                ))}
                {data.upcoming_events.length === 0 && <Empty />}
              </ul>
            </Panel>

            <Panel title="Top leads by warmth">
              <ul className="divide-y divide-ink-700">
                {data.top_leads.map((c) => (
                  <li key={c.id} className="flex items-center justify-between py-3">
                    <div>
                      <Link
                        to={`/connections/${c.id}`}
                        className="font-medium hover:underline"
                      >
                        {c.name ?? "Unknown"}
                      </Link>
                      <div className="text-xs text-gray-500">
                        {c.title ?? ""} {c.company_name ? `· ${c.company_name}` : ""}
                      </div>
                    </div>
                    <WarmthBadge score={c.predicted_warmth} />
                  </li>
                ))}
                {data.top_leads.length === 0 && <Empty />}
              </ul>
            </Panel>
          </section>
        </>
      )}
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-ink-600 bg-ink-800 p-5">
      <h2 className="mb-2 text-sm font-semibold text-gray-300">{title}</h2>
      {children}
    </div>
  );
}

export function Loading() {
  return <div className="text-sm text-gray-500">Loading…</div>;
}

export function Empty() {
  return <li className="py-3 text-sm text-gray-500">Nothing here yet.</li>;
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-warmth-hot/40 bg-warmth-hot/10 p-4 text-sm text-warmth-hot">
      Couldn’t reach the API ({message}). Is the backend running on{" "}
      <code>VITE_API_BASE_URL</code>?
    </div>
  );
}
