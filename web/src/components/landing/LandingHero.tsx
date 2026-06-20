import { landingContent } from "../../content/landingContent";
import { WarmthLogo } from "../WarmthLogo";
import { useScrollParallax } from "../../lib/useScrollReveal";
import { ScrollReveal } from "./ScrollReveal";
import { AwardBadge } from "./AwardBadge";
import { PlatformAvailabilityCards } from "./PlatformAvailabilityCards";

export function LandingHero() {
  const { ref: parallaxRef, offset } = useScrollParallax(0.06);

  return (
    <section ref={parallaxRef} className="landing-section relative py-16 sm:py-24">
      <div className="relative text-center">
        <ScrollReveal delay={0} variant="fade" eager>
          <div className="mb-6 flex flex-wrap items-center justify-center gap-2">
            <AwardBadge label={landingContent.awards.cursorTrack} />
            <AwardBadge label={landingContent.awards.zeroCRM} />
          </div>
        </ScrollReveal>

        <ScrollReveal delay={80} variant="up" eager>
          <p className="mb-4 text-sm font-semibold uppercase tracking-widest text-amber">
            Award-winning team
          </p>
        </ScrollReveal>

        <ScrollReveal delay={160} variant="up-scale" eager>
          <div
            className="mx-auto mb-6 w-fit transition-transform duration-100 ease-out"
            style={{ transform: `translateY(${offset * 0.5}px)` }}
          >
            <WarmthLogo size="lg" className="shadow-glass-lg" />
          </div>
        </ScrollReveal>

        <ScrollReveal delay={280} variant="blur" eager>
          <h1 className="text-4xl font-bold tracking-tight text-ink-900 sm:text-5xl lg:text-6xl">
            {landingContent.hero.headline}
          </h1>
        </ScrollReveal>

        <ScrollReveal delay={400} variant="up" eager>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-ink-muted sm:text-xl">
            {landingContent.hero.subheadline}
          </p>
        </ScrollReveal>

        <ScrollReveal delay={520} variant="fade" eager>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3 text-sm text-ink-faint">
            <span className="glass-pill px-3 py-1">{landingContent.hero.builtIn}</span>
            <span className="glass-pill px-3 py-1">{landingContent.hero.event}</span>
            <span className="glass-pill px-3 py-1">{landingContent.hero.venue}</span>
          </div>
        </ScrollReveal>

        <ScrollReveal delay={640} variant="up" eager>
          <PlatformAvailabilityCards className="mt-10" />
        </ScrollReveal>
      </div>
    </section>
  );
}
