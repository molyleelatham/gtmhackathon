import { useMemo, useState } from "react";
import { Avatar } from "../components/Avatar";
import { AudioWaveform } from "../components/AudioWaveform";
import { CompanyLogo } from "../components/CompanyLogo";
import { ICPBadge } from "../components/ICPBadge";
import { AttendeeDrawer, MetDetailDrawer } from "../components/MetDetailDrawer";
import { SignalChip } from "../components/SignalChip";
import { Toggle } from "../components/Toggle";
import { Toast } from "../components/Toast";
import {
  ATTENDEES,
  MET_PEOPLE,
  SIGNALS,
  type Attendee,
  type MetPerson,
} from "../lib/mockData";

type Tab = "attending" | "met";
type TopN = 10 | 25 | 50 | "all";

interface FollowState {
  done: boolean;
  snoozed: boolean;
}

export function Dashboard() {
  const [tab, setTab] = useState<Tab>("attending");
  const [topN, setTopN] = useState<TopN>(10);
  const [showSignals, setShowSignals] = useState(false);
  const [passiveAudio, setPassiveAudio] = useState(false);
  const [selectedAttendee, setSelectedAttendee] = useState<Attendee | null>(null);
  const [selectedMet, setSelectedMet] = useState<MetPerson | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [follow, setFollow] = useState<Record<string, FollowState>>({});

  const ranked = useMemo(
    () => [...ATTENDEES].sort((a, b) => b.icpScore - a.icpScore),
    [],
  );
  const shown = topN === "all" ? ranked : ranked.slice(0, topN);

  function toggleDone(id: string, name: string) {
    setFollow((prev) => {
      const next = { ...(prev[id] ?? { done: false, snoozed: false }) };
      next.done = !next.done;
      if (next.done) {
        next.snoozed = false;
        setToast(`Marked ${name} as followed up`);
      }
      return { ...prev, [id]: next };
    });
  }

  function snooze(id: string, name: string) {
    setFollow((prev) => ({
      ...prev,
      [id]: { done: false, snoozed: true },
    }));
    setToast(`Snoozed ${name} for 24h`);
  }

  const metFollow = selectedMet
    ? (follow[selectedMet.id] ?? { done: false, snoozed: false })
    : { done: false, snoozed: false };

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">
            Today at the GTM Hackathon 2026
          </h1>
          <p className="mt-1 text-sm text-ink-muted">
            {passiveAudio
              ? "Passive listening on — capturing conversations"
              : "Your conference roster, ranked by fit."}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <Toggle label="Passive audio" checked={passiveAudio} onChange={setPassiveAudio} accent />
          <Toggle label="Signal feed" checked={showSignals} onChange={setShowSignals} />
        </div>
      </header>

      <AudioWaveform active={passiveAudio} />

      <div className="flex gap-4">
        <div className="min-w-0 flex-1 space-y-4">
          <div className="flex items-center justify-between gap-3">
            <div className="glass inline-flex rounded-full p-1">
              <TabButton active={tab === "attending"} onClick={() => setTab("attending")}>
                Attending
              </TabButton>
              <TabButton active={tab === "met"} onClick={() => setTab("met")}>
                Met today
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
                  className="glass-interactive rounded-lg border border-black/10 bg-white px-2 py-1 text-xs font-medium text-ink-900 outline-none"
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
            <AttendingList attendees={shown} onOpen={setSelectedAttendee} />
          ) : (
            <MetList people={MET_PEOPLE} follow={follow} onOpen={setSelectedMet} />
          )}
        </div>

        {showSignals && (
          <aside className="hidden w-80 shrink-0 animate-drawer-in lg:block">
            <SignalFeed onAdd={(company) => setToast(`${company} added to your roster`)} />
          </aside>
        )}
      </div>

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
        onDraft={(m) => setToast(`Drafting email to ${m.name} via Lightfern + Gmail…`)}
        onToggleFollow={toggleDone}
        onSnooze={snooze}
        followDone={metFollow.done}
        snoozed={metFollow.snoozed}
      />

      <Toast message={toast} onDone={() => setToast(null)} />
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

function AttendingList({
  attendees,
  onOpen,
}: {
  attendees: Attendee[];
  onOpen: (a: Attendee) => void;
}) {
  return (
    <div className="glass divide-y divide-black/[0.06] overflow-hidden">
      {attendees.map((a, i) => (
        <button
          key={a.id}
          onClick={() => onOpen(a)}
          className="flex w-full items-center gap-4 px-4 py-3 text-left transition-colors hover:bg-orange/5"
        >
          <span className="w-5 shrink-0 text-sm font-semibold tabular-nums text-ink-faint">
            {i + 1}
          </span>
          <Avatar name={a.name} size="lg" />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-ink-900">{a.name}</span>
              <CompanyLogo company={a.company} size="sm" />
            </div>
            <p className="text-xs text-ink-muted">
              {a.title} · {a.company}
            </p>
            <p className="mt-0.5 truncate text-xs text-ink-faint">{a.signal}</p>
          </div>
          <ICPBadge score={a.icpScore} />
        </button>
      ))}
    </div>
  );
}

function MetList({
  people,
  follow,
  onOpen,
}: {
  people: MetPerson[];
  follow: Record<string, FollowState>;
  onOpen: (m: MetPerson) => void;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {people.map((m) => {
        const state = follow[m.id] ?? { done: false, snoozed: false };
        return (
          <article
            key={m.id}
            className="glass flex flex-col p-4 transition-colors hover:border-orange/20"
          >
            <div className="flex items-start gap-3">
              <Avatar name={m.name} size="lg" />
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <button
                      onClick={() => onOpen(m)}
                      className="text-left font-semibold text-ink-900 hover:text-flame"
                    >
                      {m.name}
                    </button>
                    <div className="mt-0.5 flex items-center gap-2">
                      <CompanyLogo company={m.company} size="sm" />
                      <span className="text-xs text-ink-muted">
                        {m.role} · {m.company}
                      </span>
                    </div>
                  </div>
                  <ICPBadge score={m.score} />
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {m.interests.slice(0, 3).map((t) => (
                    <span
                      key={t}
                      className="glass-pill border-orange/25 bg-orange/10 text-flame"
                    >
                      {t}
                    </span>
                  ))}
                </div>
                {m.mostInteresting && (
                  <p className="mt-2 line-clamp-2 text-sm leading-snug text-ink-800">
                    {m.mostInteresting}
                  </p>
                )}
                <p className="mt-1 text-xs text-ink-faint">{m.metAt}</p>
              </div>
            </div>
            {(state.done || state.snoozed) && (
              <div className="mt-3 border-t border-black/[0.06] pt-2">
                {state.done && (
                  <span className="text-xs font-medium text-red-brand">✓ Followed up</span>
                )}
                {state.snoozed && !state.done && (
                  <span className="text-xs font-medium text-ink-muted">Snoozed</span>
                )}
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}

function SignalFeed({ onAdd }: { onAdd: (company: string) => void }) {
  return (
    <section className="glass flex max-h-[calc(100vh-9rem)] flex-col overflow-hidden">
      <div className="flex items-baseline justify-between border-b border-black/[0.08] px-4 py-3">
        <h2 className="text-sm font-semibold tracking-tight text-ink-900">Signal Feed</h2>
        <span className="text-xs text-ink-faint">Background</span>
      </div>
      <div className="flex-1 overflow-y-auto">
        {SIGNALS.map((signal) => (
          <article
            key={signal.id}
            className="flex flex-col gap-2 border-b border-black/[0.06] p-3 last:border-0"
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
