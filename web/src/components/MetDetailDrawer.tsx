import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Avatar } from "./Avatar";
import { CompanyLogo } from "./CompanyLogo";
import { ICPBadge } from "./ICPBadge";
import { LightfernMark, GmailMark } from "./Logos";

export interface MetDetailData {
  id: string;
  name: string;
  company: string;
  role: string;
  score: number;
  metAt: string;
  origin?: string;
  background?: string;
  interests: string[];
  genuineInterests?: string[];
  whatYouLearned?: string[];
  mostInteresting?: string;
  topics?: string[];
  painPoints?: string[];
  goals?: string[];
  conversationExcerpt?: string;
  conversationTranscript?: string;
}

interface MetDetailDrawerProps {
  person: MetDetailData | null;
  onClose: () => void;
  onDraft: (person: MetDetailData) => void;
  onToggleFollow: (id: string, name: string, next: boolean) => void;
  followDone: boolean;
}

/** Slide-over for people you've met — intel on open, draft + follow-up at bottom. */
export function MetDetailDrawer({
  person,
  onClose,
  onDraft,
  onToggleFollow,
  followDone,
}: MetDetailDrawerProps) {
  const [showTranscript, setShowTranscript] = useState(false);

  useEffect(() => {
    setShowTranscript(false);
  }, [person?.id]);

  if (!person) return null;

  return createPortal(
    <>
      <div
        className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <aside
        className="drawer-panel fixed inset-y-0 right-0 z-50 flex h-dvh max-h-dvh w-[min(460px,100vw)] animate-drawer-in flex-col overflow-hidden"
        role="dialog"
        aria-label={`${person.name} conversation details`}
      >
        <div className="shrink-0 border-b border-subtle px-6 py-5">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-4">
              <Avatar name={person.name} size="xl" />
              <div>
                <h2 className="text-xl font-bold text-ink-900">{person.name}</h2>
                <div className="mt-1 flex items-center gap-2">
                  <CompanyLogo company={person.company} size="md" />
                  <span className="text-sm text-ink-muted">
                    {person.role} · {person.company}
                  </span>
                </div>
                <p className="mt-0.5 text-xs text-ink-faint">{person.metAt}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              aria-label="Close"
              className="icon-btn h-9 w-9 rounded-full"
            >
              ✕
            </button>
          </div>
          <div className="mt-4">
            <ICPBadge score={person.score} />
          </div>
        </div>

        <div className="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-5">
          {person.conversationExcerpt && (
            <Section title="From the conversation">
              <blockquote className="glass rounded-xl border-l-4 border-orange p-3 text-sm italic leading-relaxed text-ink-800">
                &ldquo;{person.conversationExcerpt}&rdquo;
              </blockquote>
              {person.conversationTranscript && (
                <div className="mt-3">
                  <button
                    type="button"
                    onClick={() => setShowTranscript((v) => !v)}
                    className="text-xs font-semibold text-flame hover:text-ember"
                  >
                    {showTranscript ? "Hide full transcript" : "View full transcript"}
                  </button>
                  {showTranscript && (
                    <div className="mt-2 max-h-56 overflow-y-auto rounded-xl border border-subtle bg-muted p-3 text-xs leading-relaxed text-ink-800">
                      <pre className="whitespace-pre-wrap font-sans">{person.conversationTranscript}</pre>
                    </div>
                  )}
                </div>
              )}
            </Section>
          )}

          {person.background && (
            <Section title="Background">
              <p className="text-sm leading-relaxed text-ink-800">{person.background}</p>
            </Section>
          )}

          {person.whatYouLearned && person.whatYouLearned.length > 0 && (
            <Section title="What you learned">
              <ul className="space-y-1.5">
                {person.whatYouLearned.map((item) => (
                  <li key={item} className="flex gap-2 text-sm text-ink-800">
                    <span className="text-flame">•</span>
                    {item}
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {person.mostInteresting && (
            <Section title="Most interesting">
              <p className="glass rounded-xl p-3 text-sm font-medium leading-relaxed text-ink-900">
                {person.mostInteresting}
              </p>
            </Section>
          )}

          {person.genuineInterests && person.genuineInterests.length > 0 && (
            <Section title="Genuinely interested in">
              <div className="flex flex-wrap gap-2">
                {person.genuineInterests.map((t) => (
                  <span
                    key={t}
                    className="glass-pill border-red-brand/30 bg-red-brand/10 text-red-brand"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {person.interests.length > 0 && (
            <Section title="Work interests">
              <div className="flex flex-wrap gap-2">
                {person.interests.map((t) => (
                  <span
                    key={t}
                    className="glass-pill border-orange/30 bg-orange/10 text-flame"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {person.topics && person.topics.length > 0 && (
            <Section title="Topics discussed">
              <div className="flex flex-wrap gap-2">
                {person.topics.map((t) => (
                  <span key={t} className="glass-pill border-subtle text-ink-muted">
                    {t}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {person.painPoints && person.painPoints.length > 0 && (
            <Section title="Pain points">
              <ul className="space-y-1 text-sm text-ink-800">
                {person.painPoints.map((p) => (
                  <li key={p}>— {p}</li>
                ))}
              </ul>
            </Section>
          )}

          {person.goals && person.goals.length > 0 && (
            <Section title="Goals">
              <ul className="space-y-1 text-sm text-ink-800">
                {person.goals.map((g) => (
                  <li key={g}>→ {g}</li>
                ))}
              </ul>
            </Section>
          )}

          {person.origin && (
            <Section title="From">
              <p className="text-sm text-ink-800">{person.origin}</p>
            </Section>
          )}
        </div>

        <div className="shrink-0 border-t border-subtle px-4 py-2.5">
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => onDraft(person)}
              className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-orange/40 bg-orange/10 py-2 text-xs font-semibold text-flame hover:bg-orange/20"
            >
              <LightfernMark className="h-3.5 w-3.5" variant="light" />
              <GmailMark className="h-3.5 w-3.5" />
              Draft Email
            </button>
            <label className="flex shrink-0 cursor-pointer items-center gap-2 rounded-lg border border-subtle px-2.5 py-2">
              <input
                type="checkbox"
                checked={followDone}
                onChange={(e) => onToggleFollow(person.id, person.name, e.target.checked)}
                className="h-3.5 w-3.5 rounded border-subtle accent-red-brand"
              />
              <span className="text-xs font-medium text-ink-900">Followed up</span>
            </label>
          </div>
        </div>
      </aside>
    </>,
    document.body,
  );
}

export function AttendeeDrawer({
  person,
  onClose,
}: {
  person: {
    name: string;
    company: string;
    title: string;
    industry: string;
    score: number;
    signal: string;
    interests: string[];
  } | null;
  onClose: () => void;
}) {
  if (!person) return null;

  return createPortal(
    <>
      <div
        className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <aside className="drawer-panel fixed inset-y-0 right-0 z-50 flex h-dvh max-h-dvh w-[min(400px,100vw)] animate-drawer-in flex-col overflow-hidden">
        <div className="flex shrink-0 items-start gap-4 border-b border-subtle px-6 py-5">
          <Avatar name={person.name} size="lg" />
          <div className="flex-1">
            <h2 className="text-lg font-bold text-ink-900">{person.name}</h2>
            <p className="mt-1 text-sm text-ink-muted">
              {person.title} · {person.company}
            </p>
            <div className="mt-2">
              <ICPBadge score={person.score} />
            </div>
          </div>
          <button onClick={onClose} className="text-ink-muted">
            ✕
          </button>
        </div>
        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-6 py-5">
          <Section title="Why they matter">
            <p className="text-sm text-ink-800">{person.signal}</p>
          </Section>
          <Section title="Industry">{person.industry}</Section>
          <Section title="Interests">
            <div className="flex flex-wrap gap-2">
              {person.interests.map((t) => (
                <span key={t} className="glass-pill border-orange/30 bg-orange/10 text-flame">
                  {t}
                </span>
              ))}
            </div>
          </Section>
        </div>
      </aside>
    </>,
    document.body,
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="mb-2 text-[0.7rem] font-semibold uppercase tracking-wider text-ink-faint">
        {title}
      </h4>
      {typeof children === "string" ? (
        <p className="text-sm text-ink-800">{children}</p>
      ) : (
        children
      )}
    </div>
  );
}
