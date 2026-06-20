import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { safeGmailComposeUrl } from "../lib/safeUrl";
import { useAsync } from "../lib/useAsync";
import { Loading, ErrorBox } from "./Dashboard";
import { WarmthBadge } from "../components/WarmthBadge";
import { KnowledgeGraphView } from "../components/KnowledgeGraphView";
import { GlassCard } from "../components/Glass";
import type { MeetProcessResponse, RoutingDecision } from "../types";

function sampleTurns(conn: { name?: string | null; company_name?: string | null; title?: string | null }) {
  return [
    { speaker: 0, text: "Great to meet you — what brought you to the event?" },
    {
      speaker: 1,
      text: `We're scaling GTM at ${conn.company_name ?? "our company"}. Biggest pain is follow-up after back-to-back meetings.`,
    },
    {
      speaker: 0,
      text: "We built Warmth to score conversations and draft follow-ups in real time.",
    },
    {
      speaker: 1,
      text: "That's exactly what I need. We have budget approved for Q3 and are consolidating three tools.",
    },
  ];
}

export function ConnectionDetail() {
  const { connectionId = "" } = useParams();
  const { data, error, loading, reload } = useAsync(
    () => api.getConnection(connectionId),
    [connectionId],
  );
  const [decision, setDecision] = useState<RoutingDecision | MeetProcessResponse | null>(null);
  const [encodeResult, setEncodeResult] = useState<Record<string, unknown> | null>(null);
  const [meetDraft, setMeetDraft] = useState<Record<string, unknown> | null>(null);
  const [followup, setFollowup] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const conn = data?.connection;
  const warmth = data?.warmth;
  const persistedMeet = data?.meet_result;

  useEffect(() => {
    if (persistedMeet?.gmail_draft) {
      setMeetDraft(persistedMeet.gmail_draft as Record<string, unknown>);
    }
  }, [persistedMeet]);

  function meetPayload() {
    if (!conn) return null;
    return {
      turns: sampleTurns(conn),
      self_speaker_id: 0,
      speaker_attrs: {
        1: { name: conn.name ?? undefined, company: conn.company_name ?? undefined, role: conn.title ?? undefined },
      },
      event_id: conn.event_id,
      connection_id: conn.id,
    };
  }

  function signalPayload(): import("../types").MeetingSignalInput | null {
    if (!conn) return null;
    return {
      connection_id: conn.id,
      event_id: conn.event_id,
      name: conn.name ?? undefined,
      company: conn.company_name ?? undefined,
      role: conn.title ?? undefined,
      interests: conn.interests,
      what_you_learned: conn.research_notes?.length
        ? conn.research_notes
        : ["Exploring a RevOps revamp", "Budget approved for Q3"],
      most_interesting: "They're consolidating 3 tools into one",
      topic_time: [{ topic: "pipeline", seconds: 240 }],
      most_time_topic: "pipeline",
      transcript_excerpt: "We have budget approved for Q3 and need faster event follow-up.",
    };
  }

  async function runEncode() {
    const body = meetPayload();
    if (!body) return;
    setBusy("encode");
    try {
      const result = await api.encodeMeet(body);
      setEncodeResult(result as unknown as Record<string, unknown>);
    } finally {
      setBusy(null);
    }
  }

  async function runProcessMeet() {
    const body = meetPayload();
    if (!body) return;
    setBusy("process");
    try {
      const result = await api.processMeet(body);
      setDecision(result);
      setMeetDraft((result.gmail_draft as Record<string, unknown>) ?? null);
      reload();
    } finally {
      setBusy(null);
    }
  }

  async function simulateMeet() {
    const body = signalPayload();
    if (!body) return;
    setBusy("signal");
    try {
      const result = await api.processSignal(body);
      setDecision(result);
      setMeetDraft((result.gmail_draft as Record<string, unknown>) ?? null);
      reload();
    } finally {
      setBusy(null);
    }
  }

  async function sendFollowupAction() {
    if (!conn) return;
    setBusy("followup");
    try {
      const result = await api.sendFollowup(conn.id, {
        name: conn.name,
        company: conn.company_name,
        interests: conn.interests,
        most_interesting: "They're consolidating 3 tools into one",
        what_you_learned: conn.research_notes ?? [],
      });
      setFollowup(result);
    } finally {
      setBusy(null);
    }
  }

  const routing: RoutingDecision | null =
    decision && "target" in decision && typeof decision.target === "string"
      ? (decision as RoutingDecision)
      : null;

  return (
    <div className="space-y-5">
      <Link to="/app/connections" className="text-sm text-ink-muted hover:text-flame">
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
              <Row label="Status" value={conn.status.replace(/_/g, " ")} />
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
              {conn.interests.length === 0 && (
                <span className="text-sm text-ink-faint">No interests yet — capture from iOS or run meet pipeline.</span>
              )}
            </div>
          </Card>

          {(persistedMeet?.knowledge_graph?.length ?? 0) > 0 || conn.interests.length > 0 ? (
            <Card title="Knowledge graph">
              {persistedMeet?.knowledge_graph && persistedMeet.knowledge_graph.length > 0 ? (
                persistedMeet.knowledge_graph.map((person, idx) => (
                  <div key={idx} className="space-y-3 border-b border-subtle pb-4 last:border-0 last:pb-0">
                    <KnowledgeGraphView
                      personName={person.name ?? conn.name ?? "Contact"}
                      interests={conn.interests}
                      topicWeights={person.topic_weights}
                      values={person.values}
                      communicationStyle={person.communication_style}
                      painPoints={person.pain_points}
                      warmthScore={warmth?.warmth_score ?? conn.predicted_warmth}
                      icpScore={warmth?.icp_score ?? conn.icp_score}
                      band={warmth?.band}
                      height={300}
                    />
                    {person.learnings && person.learnings.length > 0 && (
                      <ul className="space-y-1 text-sm text-ink-muted">
                        {person.learnings.map((l) => (
                          <li key={l}>• {l}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))
              ) : (
                <KnowledgeGraphView
                  personName={conn.name ?? "Contact"}
                  interests={conn.interests}
                  warmthScore={warmth?.warmth_score ?? conn.predicted_warmth}
                  icpScore={warmth?.icp_score ?? conn.icp_score}
                  band={warmth?.band}
                  height={280}
                />
              )}
            </Card>
          ) : null}

          {persistedMeet?.relations && persistedMeet.relations.length > 0 && (
            <Card title="Relations (from iOS)">
              <ul className="space-y-2 text-sm text-ink-muted">
                {persistedMeet.relations.map((r, i) => (
                  <li key={i}>
                    <span className="font-medium text-ink-900">{r.subject}</span>{" "}
                    {r.predicate.replace(/_/g, " ")}{" "}
                    <span className="font-medium text-ink-900">{r.object}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {conn.draft_body && (
            <Card title="Pre-meet outreach draft">
              <div className="text-sm font-medium text-ink-900">{conn.draft_subject}</div>
              <pre className="mt-2 whitespace-pre-wrap text-sm text-ink-muted">{conn.draft_body}</pre>
            </Card>
          )}

          {persistedMeet && (
            <Card title="Last meet result">
              <Row label="Routed to" value={persistedMeet.routed_to ?? "—"} />
              {persistedMeet.narrative && (
                <p className="mt-2 text-sm text-ink-muted">{persistedMeet.narrative}</p>
              )}
              {persistedMeet.recorded_at && (
                <p className="mt-2 text-xs text-ink-faint">{persistedMeet.recorded_at}</p>
              )}
            </Card>
          )}

          <Card title="Meet pipeline">
            <p className="mb-3 text-xs text-ink-muted">
              Encode → process (full agent) → signal (structured) → post-meet follow-up
            </p>
            <div className="flex flex-wrap gap-2">
              <ActionButton label="Encode transcript" busy={busy === "encode"} onClick={runEncode} />
              <ActionButton label="Process meet" busy={busy === "process"} onClick={runProcessMeet} />
              <ActionButton label="Route signal" busy={busy === "signal"} onClick={simulateMeet} />
              <ActionButton
                label="Post-meet follow-up"
                busy={busy === "followup"}
                onClick={sendFollowupAction}
                primary
              />
            </div>
          </Card>

          {encodeResult && (
            <Card title="Encode output">
              <pre className="max-h-48 overflow-auto whitespace-pre-wrap text-xs text-ink-muted">
                {JSON.stringify(encodeResult, null, 2)}
              </pre>
            </Card>
          )}

          {routing && (
            <Card title="Routing decision">
              <Row
                label="Target"
                value={routing.target === "crm_and_outreach" ? "CRM + outreach" : "Founder community"}
              />
              <Row label="Reason" value={routing.reason} />
              {routing.uplift != null && (
                <Row label="Warmth uplift" value={routing.uplift.toFixed(1)} />
              )}
              {routing.matched_candidates.length > 0 && (
                <Row
                  label="Best match"
                  value={routing.matched_candidates.map((m) => m.name).join(", ")}
                />
              )}
              {meetDraft?.gmail_compose_url ? (
                <GmailLink url={String(meetDraft.gmail_compose_url)} />
              ) : null}
            </Card>
          )}

          {followup && (
            <Card title="Post-meet follow-up">
              <div className="text-sm font-medium text-ink-900">{String(followup.subject ?? "")}</div>
              <pre className="mt-2 whitespace-pre-wrap text-sm text-ink-muted">
                {String(followup.body ?? "")}
              </pre>
              {followup.gmail_compose_url ? (
                <GmailLink url={String(followup.gmail_compose_url)} label="Open in Gmail · Lightfern polishes it there" />
              ) : null}
              <div className="mt-2 text-xs text-ink-faint">status: {String(followup.status)}</div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

function ActionButton({
  label,
  busy,
  onClick,
  primary,
}: {
  label: string;
  busy: boolean;
  onClick: () => void;
  primary?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={busy}
      className={
        primary
          ? "glass-interactive rounded-xl border border-orange/40 bg-orange/15 px-4 py-2 text-sm font-semibold text-flame disabled:opacity-50"
          : "btn-secondary disabled:opacity-50"
      }
    >
      {busy ? "Running…" : label}
    </button>
  );
}

function GmailLink({ url, label = "Open Gmail draft · Lightfern polishes there" }: { url: string; label?: string }) {
  const safe = safeGmailComposeUrl(url);
  if (!safe) return null;
  return (
    <a
      href={safe}
      target="_blank"
      rel="noreferrer"
      className="mt-3 inline-block rounded-lg bg-warmth-warm/90 px-3 py-1.5 text-xs font-medium text-ink-900 hover:bg-warmth-warm"
    >
      {label}
    </a>
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
    <div className="flex justify-between border-b border-subtle py-2 text-sm last:border-0">
      <span className="text-ink-faint">{label}</span>
      <span className="text-ink-900">{value}</span>
    </div>
  );
}
