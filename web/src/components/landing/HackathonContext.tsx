import { landingContent } from "../../content/landingContent";
import { GlassCard } from "../Glass";
import { ScrollReveal } from "./ScrollReveal";

export function HackathonContext() {
  const { hackathon } = landingContent;

  return (
    <section className="landing-section py-12">
      <ScrollReveal className="mb-8 text-center" variant="up">
        <h2 className="text-3xl font-bold text-ink-900">{hackathon.title}</h2>
        <p className="mx-auto mt-3 max-w-2xl text-ink-muted">{hackathon.pitch}</p>
      </ScrollReveal>

      <ScrollReveal variant="up-scale">
        <GlassCard strong className="p-8 sm:p-10">
          <div className="flex flex-wrap gap-2">
            {hackathon.hosts.map((host) => (
              <span
                key={host}
                className="glass-pill border-amber/30 bg-amber/10 px-3 py-1 text-xs font-semibold text-ember"
              >
                Co-hosted by {host}
              </span>
            ))}
            <span className="glass-pill px-3 py-1 text-xs font-medium text-ink-muted">
              {hackathon.track}
            </span>
            <span className="glass-pill px-3 py-1 text-xs font-medium text-ink-muted">
              {hackathon.venue}
            </span>
            <span className="glass-pill px-3 py-1 text-xs font-medium text-ink-muted">
              {hackathon.schedule}
            </span>
          </div>

          <p className="mt-5 text-sm leading-relaxed text-ink-muted">{hackathon.trackNote}</p>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            {hackathon.timeline.map((item, i) => (
              <ScrollReveal key={item.time} delay={i * 80} variant="up">
                <div className="glass rounded-xl border-subtle px-4 py-3 text-center">
                  <p className="text-lg font-bold tabular-nums text-flame">{item.time}</p>
                  <p className="mt-1 text-xs text-ink-muted">{item.label}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>

          <p className="mt-8 text-xs font-semibold uppercase tracking-wider text-ink-faint">
            {hackathon.stackNote}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {hackathon.stack.map((tool) => (
              <span
                key={tool}
                className="glass-pill border-subtle bg-white/50 px-3 py-1 text-xs font-medium text-ink-900"
              >
                {tool}
              </span>
            ))}
          </div>
        </GlassCard>
      </ScrollReveal>
    </section>
  );
}
