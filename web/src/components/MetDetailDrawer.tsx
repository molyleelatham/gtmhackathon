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
  /** Personal passions e.g. biotech, climbing */
  genuineInterests?: string[];
  whatYouLearned?: string[];
  mostInteresting?: string;
  topics?: string[];
  painPoints?: string[];
  goals?: string[];
  conversationExcerpt?: string;
}

interface MetDetailDrawerProps {
  person: MetDetailData | null;
  onClose: () => void;
  onDraft: (person: MetDetailData) => void;
  onToggleFollow: (id: string, name: string) => void;
  onSnooze: (id: string, name: string) => void;
  followDone: boolean;
  snoozed: boolean;
}

/** Rich slide-over for people you've met — conversation intel + actions. */
export function MetDetailDrawer({
  person,
  onClose,
  onDraft,
  onToggleFollow,
  onSnooze,
  followDone,
  snoozed,
}: MetDetailDrawerProps) {
  if (!person) return null;

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" onClick={onClose} aria-hidden />
      <aside
        className="glass-strong fixed inset-y-0 right-0 z-50 flex w-[min(460px,100vw)] animate-drawer-in flex-col rounded-none rounded-l-3xl"
        role="dialog"
        aria-label={`${person.name} conversation details`}
      >
        <div className="border-b border-black/[0.08] px-6 py-5">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-4">
              <Avatar name={person.name} size="xl" />
              <div>
                <button
                  onClick={() => {}}
                  className="text-left text-xl font-bold text-ink-900 hover:text-flame"
                >
                  {person.name}
                </button>
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
              className="grid h-9 w-9 place-items-center rounded-full border border-black/10 text-ink-muted hover:bg-black/5"
            >
              ✕
            </button>
          </div>
          <div className="mt-4">
            <ICPBadge score={person.score} />
          </div>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-6 py-5">
          {person.conversationExcerpt && (
            <Section title="From the conversation">
              <blockquote className="glass rounded-xl border-l-4 border-orange p-3 text-sm italic leading-relaxed text-ink-800">
                "{person.conversationExcerpt}"
              </blockquote>
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
                  <span key={t} className="glass-pill border-black/10 bg-white text-ink-muted">
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

        <div className="space-y-2 border-t border-black/[0.08] px-6 py-4">
          <button
            onClick={() => onDraft(person)}
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-orange/40 bg-orange/15 py-2.5 text-sm font-semibold text-flame hover:bg-orange/25"
          >
            <LightfernMark className="h-4 w-4" variant="dark" />
            <span className="text-ink-faint">+</span>
            <GmailMark className="h-4 w-4" />
            Draft Email
          </button>
          <div className="flex gap-2">
            <button
              onClick={() => onToggleFollow(person.id, person.name)}
              className={`flex flex-1 items-center justify-center gap-1.5 rounded-xl border py-2 text-sm font-medium ${
                followDone
                  ? "border-red-brand/40 bg-red-brand/10 text-red-brand"
                  : "border-black/10 bg-white text-ink-800 hover:bg-orange/10"
              }`}
            >
              {followDone ? "✓ Followed up" : "Follow up?"}
            </button>
            <button
              onClick={() => onSnooze(person.id, person.name)}
              className={`flex-1 rounded-xl border py-2 text-sm font-medium ${
                snoozed
                  ? "border-ink-faint bg-stone-100 text-ink-muted"
                  : "border-black/10 bg-white text-ink-muted hover:bg-black/5"
              }`}
            >
              {snoozed ? "Snoozed" : "Snooze"}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

/** Lighter drawer for attending-tab preview (no action footer). */
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

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" onClick={onClose} aria-hidden />
      <aside className="glass-strong fixed inset-y-0 right-0 z-50 flex w-[min(400px,100vw)] animate-drawer-in flex-col rounded-none rounded-l-3xl">
        <div className="flex items-start gap-4 border-b border-black/[0.08] px-6 py-5">
          <Avatar name={person.name} size="lg" />
          <div className="flex-1">
            <h2 className="text-lg font-bold text-ink-900">{person.name}</h2>
            <div className="mt-1 flex items-center gap-2">
              <CompanyLogo company={person.company} />
              <span className="text-sm text-ink-muted">
                {person.title} · {person.company}
              </span>
            </div>
            <div className="mt-2">
              <ICPBadge score={person.score} />
            </div>
          </div>
          <button onClick={onClose} className="text-ink-muted">✕</button>
        </div>
        <div className="space-y-4 px-6 py-5">
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
    </>
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
