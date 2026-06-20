import { useMemo, useState } from "react";
import { Avatar } from "../components/Avatar";
import { AudioWaveform } from "../components/AudioWaveform";
import { ICPBadge } from "../components/ICPBadge";
import { AttendeeDrawer, MetDetailDrawer } from "../components/MetDetailDrawer";
import { LightfernMark, GmailMark } from "../components/Logos";
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

  function toggleDone(id: string, name: string, next: boolean) {
    setFollow((prev) => ({ ...prev, [id]: { done: next } }));
    if (next) setToast(`Marked ${name} as followed up`);
  }

  const metFollow = selectedMet
    ? (follow[selectedMet.id] ?? { done: false })
    : { done: false };

  return (
    <div className="space-y-5">
      <header className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">
            Today at the GTM Hackathon 2026
          </h1>
          <p className="mt-1 text-sm text-ink-muted">
            {passiveAudio
              ? "Passive listening on — capturing conversations"
              : "Your conference roster, ranked by fit."}
          </p>
        </div>
        <div className="flex max-w-full flex-wrap items-center gap-2 sm:justify-end">
          <Toggle label="Passive audio" checked={passiveAudio} onChange={setPassiveAudio} accent />
          <AudioWaveform active={passiveAudio} />
          <Toggle label="Signal feed" checked={showSignals} onChange={setShowSignals} />
        </div>
      </header>

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
            <AttendingGrid attendees={shown} onOpen={setSelectedAttendee} />
          ) : (
            <MetGrid
              people={MET_PEOPLE}
              follow={follow}
              onOpen={setSelectedMet}
              onDraft={(m) => setToast(`Drafting email to ${m.name} via Lightfern + Gmail…`)}
              onToggleFollow={toggleDone}
            />
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
        onToggleFollow={(id, name, next) => toggleDone(id, name, next)}
        followDone={metFollow.done}
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

function cardKeywords(interests: string[], genuine?: string[]): string[] {
  const seen = new Set<string>();
  const merged: string[] = [];
  for (const tag of [...interests, ...(genuine ?? [])]) {
    const key = tag.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    merged.push(tag);
    if (merged.length >= 3) break;
  }
  return merged;
}

function AttendingGrid({
  attendees,
  onOpen,
}: {
  attendees: Attendee[];
  onOpen: (a: Attendee) => void;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
      {attendees.map((a) => (
        <button key={a.id} onClick={() => onOpen(a)} className="person-card">
          <ICPBadge score={a.icpScore} className="person-card-badge" />
          <div className="person-card-body">
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
          </div>
        </button>
      ))}
    </div>
  );
}

function MetGrid({
  people,
  follow,
  onOpen,
  onDraft,
  onToggleFollow,
}: {
  people: MetPerson[];
  follow: Record<string, FollowState>;
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
                onClick={() => onDraft(m)}
                className="inline-flex items-center gap-1 rounded-lg border border-orange/40 bg-orange/10 px-2 py-1 text-[11px] font-semibold text-flame hover:bg-orange/20"
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

function SignalFeed({ onAdd }: { onAdd: (company: string) => void }) {
  return (
    <section className="glass flex max-h-[calc(100vh-9rem)] flex-col overflow-hidden">
      <div className="border-b border-subtle px-4 py-3">
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-semibold tracking-tight text-ink-900">Signal Feed</h2>
          <span className="text-xs text-ink-faint">Background</span>
        </div>
        <p className="mt-1 text-[10px] text-ink-faint">
          Tags: Hiring · Funding · Intent
        </p>
      </div>
      <div className="flex-1 overflow-y-auto">
        {SIGNALS.map((signal) => (
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
