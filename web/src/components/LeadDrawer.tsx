import { ICPBadge } from "./ICPBadge";

export interface DrawerPerson {
  name: string;
  company: string;
  score: number;
  /** e.g. "VP RevOps · B2B SaaS" or "11:42 AM · Hall B" */
  meta?: string;
  signal?: string;
  background?: string;
  interests?: string[];
  whatYouLearned?: string[];
  mostInteresting?: string;
}

/** Frosted slide-over detail sheet shared by the Attending + Met tabs. */
export function LeadDrawer({
  person,
  onClose,
}: {
  person: DrawerPerson | null;
  onClose: () => void;
}) {
  if (!person) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/45 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <aside
        className="glass-strong fixed inset-y-0 right-0 z-50 flex w-[min(420px,100vw)] animate-drawer-in flex-col rounded-none rounded-l-3xl"
        role="dialog"
        aria-label={`${person.name} details`}
      >
        <div className="flex items-start justify-between border-b border-white/10 px-6 py-5">
          <div>
            <h2 className="text-xl font-semibold">{person.name}</h2>
            <p className="mt-0.5 text-sm text-white/55">
              {person.company}
              {person.meta ? ` · ${person.meta}` : ""}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="glass-interactive grid h-9 w-9 place-items-center rounded-full border border-white/12 text-white/70"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto px-6 py-5">
          <Section title="ICP Match">
            <ICPBadge score={person.score} />
          </Section>

          {person.signal && (
            <Section title="Why they matter">
              <p className="text-sm leading-relaxed text-white/85">{person.signal}</p>
            </Section>
          )}

          {person.background && (
            <Section title="Background">
              <p className="text-sm leading-relaxed text-white/85">{person.background}</p>
            </Section>
          )}

          {person.whatYouLearned && person.whatYouLearned.length > 0 && (
            <Section title="What you learned">
              <ul className="space-y-1.5">
                {person.whatYouLearned.map((item) => (
                  <li key={item} className="flex gap-2 text-sm text-white/85">
                    <span className="text-orange">•</span>
                    {item}
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {person.mostInteresting && (
            <Section title="Most interesting">
              <p className="glass rounded-xl p-3 text-sm leading-relaxed text-white/90">
                {person.mostInteresting}
              </p>
            </Section>
          )}

          {person.interests && person.interests.length > 0 && (
            <Section title="Interests">
              <div className="flex flex-wrap gap-2">
                {person.interests.map((t) => (
                  <span key={t} className="glass-pill border-white/12 bg-white/[0.06] text-white/70">
                    {t}
                  </span>
                ))}
              </div>
            </Section>
          )}
        </div>
      </aside>
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="mb-2 text-[0.7rem] font-semibold uppercase tracking-wider text-white/45">
        {title}
      </h4>
      {children}
    </div>
  );
}
