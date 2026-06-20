import { useParams, Link } from "react-router-dom";
import { useState } from "react";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { Loading, ErrorBox } from "./Dashboard";
import { WarmthBadge } from "../components/WarmthBadge";
import type { RoutingDecision } from "../types";

export function ConnectionDetail() {
  const { connectionId = "" } = useParams();
  const { data, error, loading } = useAsync(
    () => api.getConnection(connectionId),
    [connectionId],
  );
  const [decision, setDecision] = useState<RoutingDecision | null>(null);
  const [followup, setFollowup] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);

  const conn = data?.connection;
  const warmth = data?.warmth;

  async function simulateMeet() {
    if (!conn) return;
    setBusy(true);
    try {
      const result = await api.processSignal({
        connection_id: conn.id,
        name: conn.name,
        company: conn.company_name,
        interests: conn.interests,
        what_you_learned: ["Exploring a RevOps revamp", "Budget approved for Q3"],
        most_interesting: "They’re consolidating 3 tools into one",
        topic_time: [{ topic: "pipeline", seconds: 240 }],
        most_time_topic: "pipeline",
      });
      setDecision(result);
    } finally {
      setBusy(false);
    }
  }

  async function sendFollowup() {
    if (!conn) return;
    setBusy(true);
    try {
      const result = await api.sendFollowup(conn.id, {
        name: conn.name,
        company: conn.company_name,
        interests: conn.interests,
        most_interesting: "They’re consolidating 3 tools into one",
      });
      setFollowup(result);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <Link to="/connections" className="text-sm text-gray-400 hover:underline">
        ← Connections
      </Link>

      {loading && <Loading />}
      {error && <ErrorBox message={error} />}

      {conn && (
        <>
          <header className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-semibold">{conn.name ?? "Unknown"}</h1>
              <p className="text-sm text-gray-400">
                {conn.title ?? ""} {conn.company_name ? `· ${conn.company_name}` : ""}
              </p>
            </div>
            <WarmthBadge score={conn.predicted_warmth} band={warmth?.band} />
          </header>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="Firmographics">
              <Row label="Industry" value={conn.industry ?? "—"} />
              <Row label="Company size" value={conn.company_size?.toString() ?? "—"} />
              <Row label="Funding" value={conn.funding_stage ?? "—"} />
              <Row label="Source" value={conn.source} />
            </Card>

            <Card title="Scores">
              <Row label="ICP fit" value={Math.round(conn.icp_score).toString()} />
              <Row label="Intent" value={Math.round(conn.intent_score).toString()} />
              <Row label="Predicted warmth" value={Math.round(conn.predicted_warmth).toString()} />
              {warmth?.actual_score != null && (
                <Row label="Actual warmth" value={Math.round(warmth.actual_score).toString()} />
              )}
            </Card>
          </div>

          <Card title="Interests">
            <div className="flex flex-wrap gap-2">
              {conn.interests.map((i) => (
                <span
                  key={i}
                  className="rounded-full bg-ink-700 px-2.5 py-0.5 text-xs text-gray-300"
                >
                  {i}
                </span>
              ))}
            </div>
          </Card>

          {conn.draft_body && (
            <Card title="Pre-meet outreach draft">
              <div className="text-sm font-medium text-gray-200">{conn.draft_subject}</div>
              <pre className="mt-2 whitespace-pre-wrap text-sm text-gray-400">
                {conn.draft_body}
              </pre>
            </Card>
          )}

          <div className="flex gap-3">
            <button
              onClick={simulateMeet}
              disabled={busy}
              className="rounded-lg border border-ink-600 px-4 py-2 text-sm hover:bg-ink-700 disabled:opacity-50"
            >
              Simulate meet → route
            </button>
            <button
              onClick={sendFollowup}
              disabled={busy}
              className="rounded-lg bg-warmth-warm/90 px-4 py-2 text-sm font-medium text-ink-900 hover:bg-warmth-warm disabled:opacity-50"
            >
              Draft post-meet follow-up
            </button>
          </div>

          {decision && (
            <Card title="Routing decision">
              <Row
                label="Target"
                value={decision.target === "crm_and_outreach" ? "CRM + outreach" : "Founder community"}
              />
              <Row label="Reason" value={decision.reason} />
              {decision.uplift != null && (
                <Row label="Warmth uplift" value={decision.uplift.toFixed(1)} />
              )}
              {decision.matched_candidates.length > 0 && (
                <Row
                  label="Best match"
                  value={decision.matched_candidates.map((m) => m.name).join(", ")}
                />
              )}
            </Card>
          )}

          {followup && (
            <Card title="Post-meet follow-up">
              <div className="text-sm font-medium text-gray-200">
                {String(followup.subject ?? "")}
              </div>
              <pre className="mt-2 whitespace-pre-wrap text-sm text-gray-400">
                {String(followup.body ?? "")}
              </pre>
              {followup.gmail_compose_url ? (
                <a
                  href={String(followup.gmail_compose_url)}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-block rounded-lg bg-warmth-warm/90 px-3 py-1.5 text-xs font-medium text-ink-900 hover:bg-warmth-warm"
                >
                  Open in Gmail · Lightfern polishes it there
                </a>
              ) : null}
              <div className="mt-2 text-xs text-gray-500">status: {String(followup.status)}</div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-ink-600 bg-ink-800 p-5">
      <h2 className="mb-3 text-sm font-semibold text-gray-300">{title}</h2>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-ink-700 py-2 text-sm last:border-0">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-200">{value}</span>
    </div>
  );
}
