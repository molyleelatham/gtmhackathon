import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { GlassCard } from "../components/Glass";
import { Toggle } from "../components/Toggle";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import type { ConferenceRun } from "../types";
import { ErrorBox, Loading } from "./Dashboard";

export function Pipeline() {
  const runs = useAsync(() => api.listConferenceRuns(), []);
  const events = useAsync(() => api.listEvents(), []);
  const connections = useAsync(() => api.listConnections(), []);

  const [conferenceName, setConferenceName] = useState("GTM Hackathon 2026");
  const [topN, setTopN] = useState(10);
  const [skipResearch, setSkipResearch] = useState(true);
  const [skipScraping, setSkipScraping] = useState(true);
  const [running, setRunning] = useState(false);
  const [activeRun, setActiveRun] = useState<ConferenceRun | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  const [signalName, setSignalName] = useState("Alex Rivera");
  const [signalCompany, setSignalCompany] = useState("NorthWind Labs");
  const [signalTranscript, setSignalTranscript] = useState(
    "We are scaling RevOps post-Series B and need better pipeline attribution after conferences.",
  );
  const [signalConnectionId, setSignalConnectionId] = useState("");
  const [ingestResult, setIngestResult] = useState<Record<string, unknown> | null>(null);
  const [ingesting, setIngesting] = useState(false);

  useEffect(() => {
    if (connections.data?.[0]?.id && !signalConnectionId) {
      setSignalConnectionId(connections.data[0].id);
    }
  }, [connections.data, signalConnectionId]);

  useEffect(() => {
    if (!activeRun || activeRun.status !== "running") return;
    const id = setInterval(async () => {
      try {
        const updated = await api.getConferenceRun(activeRun.run_id);
        setActiveRun(updated);
        if (updated.status !== "running") {
          runs.reload();
        }
      } catch {
        /* ignore poll errors */
      }
    }, 2000);
    return () => clearInterval(id);
  }, [activeRun, runs]);

  async function startConferenceRun() {
    setRunning(true);
    setRunError(null);
    try {
      const manual = (connections.data ?? []).slice(0, 5).map((c) => ({
        name: c.name ?? undefined,
        title: c.title ?? undefined,
        company: c.company_name ?? undefined,
        interests: c.interests,
        source: "roster",
      }));
      const result = await api.runConferencePipeline({
        conference_name: conferenceName,
        manual_attendees: manual,
        top_n: topN,
        skip_scraping: skipScraping,
        skip_research: skipResearch,
        skip_email_drafts: false,
        skip_zero_sync: false,
        skip_hubspot_sync: false,
      });
      setActiveRun(result);
      runs.reload();
    } catch (e) {
      setRunError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  async function ingestSignal() {
    setIngesting(true);
    setIngestResult(null);
    try {
      const result = await api.ingestCapturedSignal({
        session_id: `web_${Date.now()}`,
        transcript_excerpt: signalTranscript,
        icp_keyword_score: 82,
        person_name: signalName,
        company: signalCompany,
        connection_id: signalConnectionId || undefined,
        event_id: events.data?.[0]?.id,
      });
      setIngestResult(result);
    } catch (e) {
      setIngestResult({ status: "error", reason: e instanceof Error ? e.message : String(e) });
    } finally {
      setIngesting(false);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">Pipeline</h1>
          <p className="mt-1 text-sm text-ink-muted">
            Conference intelligence runs, meet routing, and iOS signal ingress — all backend stages
            in one place.
          </p>
        </div>
        <Link
          to="/?demo=1"
          className="glass-interactive inline-flex shrink-0 items-center gap-2 self-start rounded-xl border border-orange/45 bg-orange/15 px-4 py-2.5 text-sm font-semibold text-flame"
        >
          <span className="h-2 w-2 rounded-full bg-flame" />
          Live demo
        </Link>
      </header>

      <div className="grid gap-5 lg:grid-cols-2">
        <GlassCard className="space-y-4 p-5">
          <h2 className="text-base font-semibold text-ink-900">Conference pipeline</h2>
          <p className="text-xs text-ink-muted">
            POST /api/v1/conferences/run — scrape → Tavily → ICP score → Gmail drafts → Zero →
            HubSpot
          </p>
          <label className="block text-sm">
            <span className="text-ink-muted">Conference name</span>
            <input
              value={conferenceName}
              onChange={(e) => setConferenceName(e.target.value)}
              className="input-glass mt-1 w-full"
            />
          </label>
          <label className="block text-sm">
            <span className="text-ink-muted">Top N leads</span>
            <input
              type="number"
              min={1}
              max={50}
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value))}
              className="input-glass mt-1 w-full"
            />
          </label>
          <Toggle label="Skip scraping (use roster)" checked={skipScraping} onChange={setSkipScraping} />
          <Toggle label="Skip Tavily research" checked={skipResearch} onChange={setSkipResearch} accent />
          <button
            type="button"
            disabled={running}
            onClick={startConferenceRun}
            className="glass-interactive w-full rounded-xl border border-orange/40 bg-orange/15 py-2 text-sm font-semibold text-flame disabled:opacity-50"
          >
            {running ? "Starting…" : "Run conference pipeline"}
          </button>
          {runError && <ErrorBox message={runError} />}
          {activeRun && (
            <div className="rounded-xl border border-subtle bg-muted p-3 text-xs">
              <div className="font-semibold text-ink-900">Run {activeRun.run_id.slice(0, 8)}…</div>
              <div className="mt-1 capitalize text-ink-muted">Status: {activeRun.status}</div>
              {activeRun.error && (
                <pre className="mt-2 whitespace-pre-wrap text-red-brand">{activeRun.error}</pre>
              )}
              {activeRun.summary && (
                <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap text-ink-muted">
                  {JSON.stringify(activeRun.summary, null, 2)}
                </pre>
              )}
            </div>
          )}
        </GlassCard>

        <GlassCard className="space-y-4 p-5">
          <h2 className="text-base font-semibold text-ink-900">iOS signal ingress</h2>
          <p className="text-xs text-ink-muted">
            POST /api/signals — simulates CapturedSignal from iPhone / Apple Watch
          </p>
          <label className="block text-sm">
            <span className="text-ink-muted">Person</span>
            <input
              value={signalName}
              onChange={(e) => setSignalName(e.target.value)}
              className="input-glass mt-1 w-full"
            />
          </label>
          <label className="block text-sm">
            <span className="text-ink-muted">Company</span>
            <input
              value={signalCompany}
              onChange={(e) => setSignalCompany(e.target.value)}
              className="input-glass mt-1 w-full"
            />
          </label>
          <label className="block text-sm">
            <span className="text-ink-muted">Connection</span>
            <select
              value={signalConnectionId}
              onChange={(e) => setSignalConnectionId(e.target.value)}
              className="input-glass mt-1 w-full"
            >
              <option value="">— auto —</option>
              {connections.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name ?? c.id}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="text-ink-muted">Transcript excerpt</span>
            <textarea
              value={signalTranscript}
              onChange={(e) => setSignalTranscript(e.target.value)}
              rows={4}
              className="input-glass mt-1 w-full resize-y"
            />
          </label>
          <button
            type="button"
            disabled={ingesting}
            onClick={ingestSignal}
            className="btn-secondary w-full disabled:opacity-50"
          >
            {ingesting ? "Ingesting…" : "Ingest captured signal"}
          </button>
          {ingestResult && (
            <pre className="max-h-48 overflow-auto rounded-xl border border-subtle bg-muted p-3 text-xs text-ink-muted">
              {JSON.stringify(ingestResult, null, 2)}
            </pre>
          )}
        </GlassCard>
      </div>

      <GlassCard className="p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink-900">Pipeline runs</h2>
          <button type="button" onClick={runs.reload} className="text-xs font-semibold text-flame">
            Refresh
          </button>
        </div>
        {runs.loading && <Loading />}
        {runs.error && <ErrorBox message={runs.error} />}
        <div className="space-y-2">
          {runs.data?.map((run) => (
            <div
              key={run.run_id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-subtle px-4 py-3 text-sm"
            >
              <div>
                <span className="font-medium text-ink-900">{run.conference}</span>
                <span className="ml-2 text-xs text-ink-faint">{run.started_at.slice(0, 19)}</span>
              </div>
              <span
                className={`glass-pill capitalize ${
                  run.status === "complete"
                    ? "border-warmth-warm/40 bg-warmth-warm/15 text-ink-900"
                    : run.status === "error"
                      ? "border-red-brand/40 bg-red-brand/10 text-red-brand"
                      : "border-orange/30 bg-orange/10 text-flame"
                }`}
              >
                {run.status}
              </span>
            </div>
          ))}
          {runs.data && runs.data.length === 0 && (
            <p className="text-sm text-ink-faint">No pipeline runs yet.</p>
          )}
        </div>
      </GlassCard>

      <p className="text-xs text-ink-faint">
        Meet encode/process endpoints are on each{" "}
        <Link to="/connections" className="text-flame hover:text-ember">
          connection detail
        </Link>{" "}
        page. Pre-meet runs from{" "}
        <Link to="/events" className="text-flame hover:text-ember">
          Events
        </Link>
        .
      </p>
    </div>
  );
}
