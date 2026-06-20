import { useMemo, useRef, useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Avatar } from "../components/Avatar";
import { AudioWaveform } from "../components/AudioWaveform";
import { AttendeeConnectedModal } from "../components/AttendeeConnectedModal";
import { ConnectionWeb } from "../components/ConnectionWeb";
import { ThinkingPipelinePanel } from "../components/ThinkingPipelinePanel";
import { ICPBadge } from "../components/ICPBadge";
import { AttendeeDrawer, MetDetailDrawer } from "../components/MetDetailDrawer";
import { LightfernMark, GmailMark } from "../components/Logos";
import { SignalChip } from "../components/SignalChip";
import { StatTile } from "../components/StatTile";
import { WarmthBadge } from "../components/WarmthBadge";
import { Toggle } from "../components/Toggle";
import { Toast } from "../components/Toast";
import { api } from "../lib/api";
import {
  normalizeSignals,
  rosterToAttendees,
  rosterToMetPeople,
} from "../lib/adapters";
import type { Attendee, MetPerson, Signal } from "../lib/uiTypes";
import type { AttendeeMatchResult } from "../types";
import { useAsync } from "../lib/useAsync";
import { initialSteps, runLiveDemo, type PipelineStep } from "../lib/liveDemo";
import { useWebSpeechCapture } from "../lib/useWebSpeechCapture";
import { extractGreetingName, speechRecognitionSupported, WAKE_PHRASE } from "../lib/speechCapture";

type Tab = "attending" | "met";
type TopN = 10 | 25 | 50 | "all";

interface FollowState {
  done: boolean;
}

export function Dashboard() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { data: roster, error, loading, reload: reloadRoster } = useAsync(
    () => api.dashboardRoster(),
    [],
  );
  const summary = useAsync(() => api.dashboard(), []);
  const [tab, setTab] = useState<Tab>("attending");
  const [topN, setTopN] = useState<TopN>(10);
  const [showSignals, setShowSignals] = useState(false);
  const [passiveAudio, setPassiveAudio] = useState(false);
  const [useMicrophone, setUseMicrophone] = useState(false);
  const speech = useWebSpeechCapture();
  const micSupported = speechRecognitionSupported();
  const matchAttemptedRef = useRef(false);
  const [selectedAttendee, setSelectedAttendee] = useState<Attendee | null>(null);
  const [selectedMet, setSelectedMet] = useState<MetPerson | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [follow, setFollow] = useState<Record<string, FollowState>>({});
  const [draftBusy, setDraftBusy] = useState(false);
  const [attendeeMatch, setAttendeeMatch] = useState<AttendeeMatchResult | null>(null);
  const [matching, setMatching] = useState(false);
  const [demoOpen, setDemoOpen] = useState(false);
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoSteps, setDemoSteps] = useState<PipelineStep[]>(() => initialSteps());
  const [demoTranscript, setDemoTranscript] = useState<string | null>(null);
  const demoAbortRef = useRef<AbortController | null>(null);

  const attendees = useMemo(
    () => (roster ? rosterToAttendees(roster) : []),
    [roster],
  );
  const metPeople = useMemo(
    () => (roster ? rosterToMetPeople(roster) : []),
    [roster],
  );
  const signals = useMemo(
    () => (roster ? normalizeSignals(roster.signals) : []),
    [roster],
  );

  const ranked = useMemo(
    () => [...attendees].sort((a, b) => b.icpScore - a.icpScore),
    [attendees],
  );
  const shown = topN === "all" ? ranked : ranked.slice(0, topN);

  const eventTitle = roster?.event?.name ?? "GTM Hackathon 2026";
  const eventLocation = roster?.event?.location;

  useEffect(() => {
    if (searchParams.get("demo") !== "1" || loading || demoRunning || attendees.length === 0) return;
    setSearchParams({}, { replace: true });
    void startLiveDemo();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- one-shot URL trigger
  }, [searchParams, loading, attendees.length, demoRunning]);

  async function runSimulatedMatch() {
    const target = ranked[0];
    if (!target) {
      setToast("No attendees on roster yet.");
      return;
    }
    setMatching(true);
    try {
      const firstName = target.name.split(" ")[0];
      const result = await api.matchAttendee({
        name: firstName,
        company: target.company,
        transcript: `Hi ${firstName}, nice to meet you.`,
      });
      if (result.matched) setAttendeeMatch(result);
      else setToast(result.message);
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Match failed");
    } finally {
      setMatching(false);
    }
  }

  async function handlePassiveAudio(on: boolean) {
    if (!on) {
      if (useMicrophone) speech.stop();
      setPassiveAudio(false);
      matchAttemptedRef.current = false;
      return;
    }

    if (useMicrophone) {
      matchAttemptedRef.current = false;
      speech.clearTranscript();
      const ok = await speech.start();
      if (!ok) {
        setToast(speech.error ?? "Microphone unavailable");
        return;
      }
      setPassiveAudio(true);
      return;
    }

    setPassiveAudio(true);
    await runSimulatedMatch();
  }

  async function handleUseMicrophone(on: boolean) {
    if (on && !micSupported) {
      setToast("Web mic needs Chrome or Safari with microphone permission.");
      return;
    }
    if (!on) {
      if (passiveAudio) {
        speech.stop();
        setPassiveAudio(false);
        matchAttemptedRef.current = false;
      }
      setUseMicrophone(false);
      return;
    }

    setUseMicrophone(true);
    if (passiveAudio && !speech.listening) {
      matchAttemptedRef.current = false;
      speech.clearTranscript();
      const ok = await speech.start();
      if (!ok) {
        setUseMicrophone(false);
        setToast(speech.error ?? "Microphone unavailable");
      }
    }
  }

  useEffect(() => {
    if (!passiveAudio || !useMicrophone || matching || matchAttemptedRef.current) return;
    const text = speech.transcript.trim();
    if (!text) return;
    const name = extractGreetingName(text);
    if (!name) return;

    matchAttemptedRef.current = true;
    void (async () => {
      setMatching(true);
      try {
        const attendee = ranked.find(
          (a) =>
            a.name.split(" ")[0]?.toLowerCase() === name.toLowerCase() ||
            a.name.toLowerCase().startsWith(name.toLowerCase()),
        );
        const result = await api.matchAttendee({
          name,
          company: attendee?.company,
          transcript: text,
        });
        if (result.matched) setAttendeeMatch(result);
        else {
          matchAttemptedRef.current = false;
          setToast(result.message);
        }
      } catch (e) {
        matchAttemptedRef.current = false;
        setToast(e instanceof Error ? e.message : "Match failed");
      } finally {
        setMatching(false);
      }
    })();
  }, [passiveAudio, useMicrophone, speech.transcript, matching, ranked]);

  function cancelLiveDemo() {
    demoAbortRef.current?.abort();
    demoAbortRef.current = null;
    setDemoRunning(false);
  }

  function closeLiveDemo() {
    cancelLiveDemo();
    setDemoOpen(false);
    setDemoTranscript(null);
    setDemoSteps(initialSteps());
  }

  async function startLiveDemo() {
    const target = ranked[0];
    if (!target) {
      setToast("No attendees on roster — connect calendar first.");
      return;
    }
    demoAbortRef.current?.abort();
    const controller = new AbortController();
    demoAbortRef.current = controller;
    setDemoOpen(true);
    setDemoRunning(true);
    setDemoTranscript(null);
    setDemoSteps(initialSteps());

    await runLiveDemo(
      target,
      {
        onSteps: setDemoSteps,
        onComplete: (match, transcript) => {
          setDemoTranscript(transcript);
          setDemoRunning(false);
          setAttendeeMatch(match);
          reloadRoster();
          summary.reload();
        },
        onError: (message) => {
          setDemoRunning(false);
          setToast(message);
        },
      },
      controller.signal,
    );
  }

  async function matchAttendeeByName(attendee: Attendee) {
    setMatching(true);
    try {
      const firstName = attendee.name.split(" ")[0];
      const result = await api.matchAttendee({
        name: firstName,
        company: attendee.company,
        transcript: `Hi ${firstName}`,
      });
      if (result.matched) setAttendeeMatch(result);
      else setToast(result.message);
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Match failed");
    } finally {
      setMatching(false);
    }
  }

  function toggleDone(id: string, name: string, next: boolean) {
    setFollow((prev) => ({ ...prev, [id]: { done: next } }));
    if (next) setToast(`Marked ${name} as followed up`);
  }

  async function draftFollowup(m: MetPerson) {
    setDraftBusy(true);
    try {
      const result = await api.sendFollowup(m.id, {
        name: m.name,
        company: m.company,
        interests: m.interests,
        most_interesting: m.mostInteresting,
        what_you_learned: m.whatYouLearned,
      });
      const url = result.gmail_compose_url;
      if (url && typeof url === "string") {
        window.open(url, "_blank", "noopener,noreferrer");
        setToast(`Gmail draft ready for ${m.name}`);
      } else {
        setToast(`Draft prepared for ${m.name} via Lightfern + Gmail`);
      }
      reloadRoster();
      summary.reload();
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Could not create draft");
    } finally {
      setDraftBusy(false);
    }
  }

  const metFollow = selectedMet
    ? (follow[selectedMet.id] ?? { done: false })
    : { done: false };

  return (
    <div className="space-y-5">
      <header className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">
            Today at {eventTitle}
          </h1>
          <p className="mt-1 text-sm text-ink-muted">
            {passiveAudio && useMicrophone
              ? "Web mic on — say “Hi {name}” or the wake phrase"
              : passiveAudio
                ? "Passive listening on — simulated match"
                : eventLocation
                  ? `${eventLocation} · ranked by ICP fit`
                  : "Your conference roster, ranked by fit."}
          </p>
        </div>
        <div className="flex max-w-full flex-wrap items-center gap-2 sm:justify-end">
          <button
            type="button"
            disabled={demoRunning || loading || attendees.length === 0}
            onClick={() => void startLiveDemo()}
            className="glass-interactive flex items-center gap-2 rounded-xl border border-orange/45 bg-orange/15 px-3 py-2 text-sm font-semibold text-flame disabled:opacity-50"
          >
            <span className="relative flex h-2 w-2">
              {demoRunning && (
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-flame opacity-75" />
              )}
              <span className="relative inline-flex h-2 w-2 rounded-full bg-flame" />
            </span>
            {demoRunning ? "Demo running…" : "Live demo"}
          </button>
          <Toggle
            label={matching ? "Matching…" : "Passive audio"}
            checked={passiveAudio}
            onChange={handlePassiveAudio}
            accent
          />
          {micSupported && (
            <Toggle
              label="Web mic"
              checked={useMicrophone}
              onChange={handleUseMicrophone}
            />
          )}
          <AudioWaveform
            active={passiveAudio}
            level={useMicrophone ? speech.audioLevel : 0}
          />
          <Toggle label="Signal feed" checked={showSignals} onChange={setShowSignals} />
        </div>
      </header>

      {passiveAudio && useMicrophone && (
        <div className="glass px-4 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-ink-faint">
            Live transcript
          </p>
          <p className="mt-1 text-sm text-ink-800">
            {speech.transcript ||
              `Listening… try “Hi Moly” or “${WAKE_PHRASE}”`}
          </p>
        </div>
      )}

      {loading && <Loading />}
      {error && <ErrorBox message={error} />}

      {summary.data && (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <StatTile label="Events" value={summary.data.events} />
          <StatTile label="Connections" value={summary.data.connections} accent />
          <StatTile label="Hot leads" value={summary.data.hot_leads} accent />
          <StatTile label="In CRM" value={summary.data.leads_in_crm} />
        </div>
      )}

      {summary.data && summary.data.top_leads.length > 0 && (
        <section className="glass p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-ink-900">Top leads</h2>
            <Link to="/leads" className="text-xs font-semibold text-flame hover:text-ember">
              View CRM →
            </Link>
          </div>
          <div className="flex flex-wrap gap-2">
            {summary.data.top_leads.map((lead) => (
              <Link
                key={lead.id}
                to={`/connections/${lead.id}`}
                className="glass-interactive flex items-center gap-2 rounded-xl border border-subtle px-3 py-2 text-sm"
              >
                <Avatar name={lead.name ?? "?"} size="sm" />
                <span className="font-medium text-ink-900">{lead.name}</span>
                <WarmthBadge score={lead.predicted_warmth} />
              </Link>
            ))}
          </div>
        </section>
      )}

      {!loading && !error && (
        <div className="flex gap-4">
          <div className="min-w-0 flex-1 space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div className="glass inline-flex rounded-full p-1">
                <TabButton active={tab === "attending"} onClick={() => setTab("attending")}>
                  Attending
                  {attendees.length > 0 && (
                    <span className="ml-1.5 text-xs opacity-70">{attendees.length}</span>
                  )}
                </TabButton>
                <TabButton active={tab === "met"} onClick={() => setTab("met")}>
                  Met today
                  {metPeople.length > 0 && (
                    <span className="ml-1.5 text-xs opacity-70">{metPeople.length}</span>
                  )}
                </TabButton>
              </div>

              {tab === "attending" && (
                <label className="flex items-center gap-2 text-xs text-ink-muted">
                  Show
                  <select
                    value={String(topN)}
                    onChange={(e) =>
                      setTopN(e.target.value === "all" ? "all" : (Number(e.target.value) as TopN))
                    }
                    className="input-glass"
                  >
                    <option value="10">Top 10</option>
                    <option value="25">Top 25</option>
                    <option value="50">Top 50</option>
                    <option value="all">All</option>
                  </select>
                </label>
              )}
            </div>

            {tab === "attending" ? (
              shown.length > 0 ? (
                <AttendingGrid
                  attendees={shown}
                  onOpen={setSelectedAttendee}
                  onConnect={matchAttendeeByName}
                />
              ) : (
                <p className="text-sm text-ink-faint">
                  No attendees yet — connect your calendar or run pre-meet from Events.
                </p>
              )
            ) : metPeople.length > 0 ? (
              <MetGrid
                people={metPeople}
                follow={follow}
                draftBusy={draftBusy}
                onOpen={setSelectedMet}
                onDraft={draftFollowup}
                onToggleFollow={toggleDone}
              />
            ) : (
              <p className="text-sm text-ink-faint">
                No meetings captured yet — simulate a meet from a connection detail page.
              </p>
            )}
          </div>

          {showSignals && (
            <aside className="hidden w-80 shrink-0 animate-drawer-in lg:block">
              <SignalFeed
                signals={signals}
                onAdd={(company) => setToast(`${company} added to your roster`)}
              />
            </aside>
          )}
        </div>
      )}

      {!loading && !error && attendees.length > 1 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-ink-900">Mutual interest map</h2>
          <ConnectionWeb />
        </section>
      )}

      <AttendeeDrawer
        person={
          selectedAttendee
            ? {
                name: selectedAttendee.name,
                company: selectedAttendee.company,
                title: selectedAttendee.title,
                industry: selectedAttendee.industry,
                score: selectedAttendee.icpScore,
                signal: selectedAttendee.signal,
                interests: selectedAttendee.interests,
              }
            : null
        }
        onClose={() => setSelectedAttendee(null)}
      />

      <MetDetailDrawer
        person={selectedMet}
        onClose={() => setSelectedMet(null)}
        onDraft={(m) => void draftFollowup({ ...m, whatYouLearned: m.whatYouLearned ?? [] })}
        onToggleFollow={(id, name, next) => toggleDone(id, name, next)}
        followDone={metFollow.done}
      />

      <Toast message={toast} onDone={() => setToast(null)} />

      <AttendeeConnectedModal
        match={attendeeMatch}
        onClose={() => setAttendeeMatch(null)}
        onViewProfile={(id) => navigate(`/connections/${id}`)}
      />

      <ThinkingPipelinePanel
        open={demoOpen}
        steps={demoSteps}
        running={demoRunning}
        transcript={demoTranscript}
        onClose={closeLiveDemo}
        onCancel={cancelLiveDemo}
      />
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-all ${
        active
          ? "bg-orange/15 text-flame shadow-sm"
          : "text-ink-muted hover:text-ink-900"
      }`}
    >
      {children}
    </button>
  );
}

function cardKeywords(interests: string[], genuine?: string[]): string[] {
  const seen = new Set<string>();
  const merged: string[] = [];
  for (const tag of [...interests, ...(genuine ?? [])]) {
    const key = tag.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    merged.push(tag);
  }
  return merged;
}

function AttendingGrid({
  attendees,
  onOpen,
  onConnect,
}: {
  attendees: Attendee[];
  onOpen: (a: Attendee) => void;
  onConnect: (a: Attendee) => void;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
      {attendees.map((a) => (
        <div key={a.id} className="person-card group relative">
          <ICPBadge score={a.icpScore} className="person-card-badge" />
          <button type="button" onClick={() => onOpen(a)} className="person-card-body w-full text-left">
            <Avatar name={a.name} size="lg" />
            <div className="person-card-info">
              <p className="truncate font-semibold text-ink-900">{a.name}</p>
              <p className="truncate text-xs text-ink-muted">
                {a.title} · {a.company}
              </p>
              {a.interests.length > 0 && (
                <div className="person-card-pills">
                  {cardKeywords(a.interests).map((t) => (
                    <span key={t} className="person-card-pill">
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </button>
          <button
            type="button"
            onClick={() => onConnect(a)}
            className="absolute bottom-2 right-2 rounded-lg border border-orange/40 bg-orange/15 px-2 py-1 text-[10px] font-semibold text-flame opacity-0 transition-opacity group-hover:opacity-100"
          >
            Hi → connect
          </button>
        </div>
      ))}
    </div>
  );
}

function MetGrid({
  people,
  follow,
  draftBusy,
  onOpen,
  onDraft,
  onToggleFollow,
}: {
  people: MetPerson[];
  follow: Record<string, FollowState>;
  draftBusy: boolean;
  onOpen: (m: MetPerson) => void;
  onDraft: (m: MetPerson) => void;
  onToggleFollow: (id: string, name: string, next: boolean) => void;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
      {people.map((m) => {
        const state = follow[m.id] ?? { done: false };
        const keywords = cardKeywords(m.interests, m.genuineInterests);
        return (
          <div key={m.id} className="person-card">
            <ICPBadge score={m.score} className="person-card-badge" />

            <div
              role="button"
              tabIndex={0}
              onClick={() => onOpen(m)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onOpen(m);
                }
              }}
              className="person-card-body cursor-pointer text-left"
            >
              <Avatar name={m.name} size="lg" />
              <div className="person-card-info">
                <p className="truncate font-semibold text-ink-900">{m.name}</p>
                <p className="truncate text-xs text-ink-muted">
                  {m.role} · {m.company}
                </p>
                {keywords.length > 0 && (
                  <div className="person-card-pills">
                    {keywords.map((t) => (
                      <span key={t} className="person-card-pill">
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="person-card-actions">
              <button
                type="button"
                disabled={draftBusy}
                onClick={() => onDraft(m)}
                className="inline-flex items-center gap-1 rounded-lg border border-orange/40 bg-orange/10 px-2 py-1 text-[11px] font-semibold text-flame hover:bg-orange/20 disabled:opacity-50"
              >
                <LightfernMark className="h-3.5 w-3.5" variant="light" />
                <GmailMark className="h-3.5 w-3.5" />
                Draft
              </button>
              <label className="flex cursor-pointer items-center gap-1.5 text-[11px] font-medium text-ink-muted">
                <input
                  type="checkbox"
                  checked={state.done}
                  onChange={(e) => onToggleFollow(m.id, m.name, e.target.checked)}
                  className="h-3.5 w-3.5 rounded border-subtle accent-red-brand"
                />
                Follow up
              </label>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SignalFeed({
  signals,
  onAdd,
}: {
  signals: Signal[];
  onAdd: (company: string) => void;
}) {
  return (
    <section className="glass flex max-h-[calc(100vh-9rem)] flex-col overflow-hidden">
      <div className="border-b border-subtle px-4 py-3">
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-semibold tracking-tight text-ink-900">Signal Feed</h2>
          <span className="text-xs text-ink-faint">Live</span>
        </div>
        <p className="mt-1 text-[10px] text-ink-faint">
          Tags: Hiring · Funding · Intent
        </p>
      </div>
      <div className="flex-1 overflow-y-auto">
        {signals.length === 0 && (
          <p className="p-4 text-xs text-ink-faint">No signals yet — enrich your roster first.</p>
        )}
        {signals.map((signal) => (
          <article
            key={signal.id}
            className="flex flex-col gap-2 border-b border-subtle p-3 last:border-0"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-semibold text-ink-900">{signal.company}</span>
              <span className="whitespace-nowrap text-xs text-ink-faint">{signal.time}</span>
            </div>
            <p className="text-xs leading-snug text-ink-muted">{signal.desc}</p>
            <div className="flex items-center justify-between gap-2">
              <SignalChip type={signal.type} />
              <button
                onClick={() => onAdd(signal.company)}
                className="text-xs font-semibold text-flame hover:text-ember"
              >
                Add to roster
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function Loading() {
  return <div className="text-sm text-ink-faint">Loading…</div>;
}

export function Empty() {
  return <li className="py-3 text-sm text-ink-faint">Nothing here yet.</li>;
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="glass rounded-xl border-red-brand/40 bg-red-brand/10 p-4 text-sm text-red-brand">
      Couldn&apos;t reach the API ({message}).
    </div>
  );
}
