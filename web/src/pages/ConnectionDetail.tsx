import { useParams, Link } from "react-router-dom";
import { useState } from "react";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { Loading, ErrorBox } from "./Dashboard";
import { WarmthBadge } from "../components/WarmthBadge";
import { GlassCard } from "../components/Glass";
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
    <div className="space-y-5">
      <Link to="/connections" className="text-sm text-ink-muted hover:text-flame">
        ← Connections
      </Link>

      {loading && <Loading />}
      {error && <ErrorBox message={error} />}

      {conn && (
        <>
          <header className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-ink-900">
                {conn.name ?? "Unknown"}
              </h1>
              <p className="mt-1 text-sm text-ink-muted">
                {conn.title ?? ""} {conn.company_name ? `· ${conn.company_name}` : ""}
              </p>
            </div>
            <WarmthBadge score={conn.predicted_warmth} band={warmth?.band} />
          </header>

          <div className="grid gap-4 lg:grid-cols-2">
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
                <span key={i} className="glass-pill border-orange/25 bg-orange/10 text-flame">
                  {i}
                </span>
              ))}
            </div>
          </Card>

          {conn.draft_body && (
            <Card title="Pre-meet outreach draft">
              <div className="text-sm font-medium text-ink-900">{conn.draft_subject}</div>
              <pre className="mt-2 whitespace-pre-wrap text-sm text-ink-muted">{conn.draft_body}</pre>
            </Card>
          )}

          <div className="flex flex-wrap gap-3">
            <button
              onClick={simulateMeet}
              disabled={busy}
              className="glass-interactive rounded-xl border border-black/10 bg-white px-4 py-2 text-sm text-ink-800 disabled:opacity-50"
            >
              Simulate meet → route
            </button>
            <button
              onClick={sendFollowup}
              disabled={busy}
              className="glass-interactive rounded-xl border border-orange/40 bg-orange/15 px-4 py-2 text-sm font-semibold text-flame disabled:opacity-50"
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
              <div className="text-sm font-medium text-ink-900">{String(followup.subject ?? "")}</div>
              <pre className="mt-2 whitespace-pre-wrap text-sm text-ink-muted">
                {String(followup.body ?? "")}
              </pre>
              <div className="mt-2 text-xs text-ink-faint">status: {String(followup.status)}</div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <GlassCard className="p-5">
      <h2 className="mb-3 text-sm font-semibold text-ink-muted">{title}</h2>
      {children}
    </GlassCard>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-black/[0.06] py-2 text-sm last:border-0">
      <span className="text-ink-faint">{label}</span>
      <span className="text-ink-900">{value}</span>
    </div>
  );
}
