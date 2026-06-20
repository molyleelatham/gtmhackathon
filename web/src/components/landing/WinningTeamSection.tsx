import { landingContent } from "../../content/landingContent";
import { AwardBadge } from "./AwardBadge";
import { ScrollReveal } from "./ScrollReveal";
import { TeamCard } from "./TeamCard";

export function WinningTeamSection() {
  return (
    <section id="team" className="landing-section py-10 sm:py-14">
      <div className="glass-strong relative overflow-hidden rounded-3xl border-amber/30 p-6 sm:p-10">
        <div
          className="pointer-events-none absolute inset-0 bg-gradient-to-br from-amber/10 via-orange/5 to-flame/10"
          aria-hidden="true"
        />

        <div className="relative">
          <ScrollReveal className="mb-8 text-center" variant="blur">
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-amber">
              GTM Hackathon London · June 2026
            </p>
            <h2 className="text-3xl font-bold text-ink-900 sm:text-4xl">Meet the winning team</h2>
            <p className="mx-auto mt-3 max-w-xl text-ink-muted">
              Two podium finishes in one day — built Warmth from scratch and took it live on stage.
            </p>
            <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
              <AwardBadge label={landingContent.awards.cursorTrack} />
              <AwardBadge label={landingContent.awards.zeroCRM} />
            </div>
            <p className="mx-auto mt-3 max-w-lg text-xs text-ink-faint">
              {landingContent.awards.cursorDetail} · {landingContent.awards.zeroDetail}
            </p>
          </ScrollReveal>

          <div className="grid gap-5 md:grid-cols-3">
            {landingContent.team.map((member, i) => (
              <ScrollReveal key={member.name} delay={i * 110} variant="up">
                <TeamCard member={member} showCrown winner />
              </ScrollReveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
