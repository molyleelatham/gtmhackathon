import { useParams, Link } from "react-router-dom";
import { useState } from "react";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { Loading, ErrorBox } from "./Dashboard";
import { WarmthBadge } from "../components/WarmthBadge";

export function PreMeet() {
  const { eventId = "" } = useParams();
  const event = useAsync(() => api.getEvent(eventId), [eventId]);
  const leads = useAsync(() => api.eventLeads(eventId), [eventId]);
  const [running, setRunning] = useState(false);

  async function runPipeline() {
    setRunning(true);
    try {
      await api.runPremeet(eventId, [
        {
          name: "Sam Rivera",
          title: "RevOps Lead",
          company: "Glide",
          interests: ["RevOps", "attribution"],
          source: "manual",
        },
      ]);
      leads.reload();
      event.reload();
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-5">
      <Link to="/events" className="text-sm text-ink-muted hover:text-flame">
        ← Events
      </Link>

      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">
            {event.data?.name ?? "Event"} — Before meet
          </h1>
          <p className="mt-1 text-sm text-ink-muted">
            Enriched, warmth-scored attendees ranked by intent for pre-event outreach.
          </p>
        </div>
        <button
          onClick={runPipeline}
          disabled={running}
          className="glass-interactive rounded-xl border border-orange/40 bg-orange/15 px-4 py-2 text-sm font-semibold text-flame disabled:opacity-50"
        >
          {running ? "Running…" : "Run pre-meet pipeline"}
        </button>
      </header>

      {(event.error || leads.error) && (
        <ErrorBox message={event.error ?? leads.error ?? ""} />
      )}
      {leads.loading && <Loading />}

      <div className="glass overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead className="text-left text-xs uppercase tracking-wider text-ink-faint">
            <tr className="border-b border-subtle">
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Company</th>
              <th className="px-4 py-3 font-medium">ICP</th>
              <th className="px-4 py-3 font-medium">Warmth</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {leads.data?.map((c) => (
              <tr
                key={c.id}
                className="border-b border-subtle transition-colors hover:bg-orange/5"
              >
                <td className="px-4 py-3">
                  <Link
                    to={`/connections/${c.id}`}
                    className="font-medium text-ink-900 hover:text-flame"
                  >
                    {c.name ?? "Unknown"}
                  </Link>
                  <div className="text-xs text-ink-faint">{c.title ?? ""}</div>
                </td>
                <td className="px-4 py-3 text-ink-800">
                  {c.company_name ?? "—"}
                  <div className="text-xs text-ink-faint">
                    {c.industry ?? ""} {c.funding_stage ? `· ${c.funding_stage}` : ""}
                  </div>
                </td>
                <td className="px-4 py-3 text-ink-800">{Math.round(c.icp_score)}</td>
                <td className="px-4 py-3">
                  <WarmthBadge score={c.predicted_warmth} />
                </td>
                <td className="px-4 py-3 text-xs text-ink-muted">
                  {c.status.replace(/_/g, " ")}
                </td>
              </tr>
            ))}
            {leads.data && leads.data.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-ink-faint">
                  No leads yet — run the pre-meet pipeline.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
