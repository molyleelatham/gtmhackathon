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
      // Seed a couple of manual attendees to demonstrate the pipeline.
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
    <div className="space-y-6">
      <Link to="/events" className="text-sm text-gray-400 hover:underline">
        ← Events
      </Link>

      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">
            {event.data?.name ?? "Event"} — Before meet
          </h1>
          <p className="text-sm text-gray-400">
            Enriched, warmth-scored attendees ranked by intent for pre-conference outreach.
          </p>
        </div>
        <button
          onClick={runPipeline}
          disabled={running}
          className="rounded-lg bg-warmth-warm/90 px-4 py-2 text-sm font-medium text-ink-900 hover:bg-warmth-warm disabled:opacity-50"
        >
          {running ? "Running…" : "Run pre-meet pipeline"}
        </button>
      </header>

      {(event.error || leads.error) && (
        <ErrorBox message={event.error ?? leads.error ?? ""} />
      )}
      {leads.loading && <Loading />}

      <div className="overflow-hidden rounded-xl border border-ink-600">
        <table className="w-full text-sm">
          <thead className="bg-ink-800 text-left text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Company</th>
              <th className="px-4 py-3">ICP</th>
              <th className="px-4 py-3">Warmth</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-700 bg-ink-900/40">
            {leads.data?.map((c) => (
              <tr key={c.id} className="hover:bg-ink-800/60">
                <td className="px-4 py-3">
                  <Link to={`/connections/${c.id}`} className="font-medium hover:underline">
                    {c.name ?? "Unknown"}
                  </Link>
                  <div className="text-xs text-gray-500">{c.title ?? ""}</div>
                </td>
                <td className="px-4 py-3 text-gray-300">
                  {c.company_name ?? "—"}
                  <div className="text-xs text-gray-500">
                    {c.industry ?? ""} {c.funding_stage ? `· ${c.funding_stage}` : ""}
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-300">{Math.round(c.icp_score)}</td>
                <td className="px-4 py-3">
                  <WarmthBadge score={c.predicted_warmth} />
                </td>
                <td className="px-4 py-3 text-xs text-gray-400">
                  {c.status.replace(/_/g, " ")}
                </td>
              </tr>
            ))}
            {leads.data && leads.data.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-gray-500">
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
