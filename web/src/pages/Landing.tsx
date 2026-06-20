import { Link } from "react-router-dom";
import { landingContent } from "../content/landingContent";
import { GlassCard } from "../components/Glass";
import { LandingNav } from "../components/landing/LandingNav";
import { LandingHero } from "../components/landing/LandingHero";
import { WinningTeamSection } from "../components/landing/WinningTeamSection";
import { LifecycleSteps } from "../components/landing/LifecycleSteps";
import { WinsGallery } from "../components/landing/WinsGallery";
import { HackathonContext } from "../components/landing/HackathonContext";
import { DemoVideoPlayer } from "../components/landing/DemoVideoPlayer";
import { ScrollReveal } from "../components/landing/ScrollReveal";

export function Landing() {
  return (
    <div className="min-h-screen">
      <LandingNav />
      <main>
        <LandingHero />

        <WinningTeamSection />

        <WinsGallery />

        <section id="demo" className="landing-section py-16">
          <ScrollReveal className="mb-8 text-center" variant="up">
            <h2 className="text-3xl font-bold text-ink-900">See Warmth in action</h2>
            <p className="mt-2 text-ink-muted">From phrase trigger to Gmail draft in 60 seconds.</p>
          </ScrollReveal>
          <ScrollReveal delay={120} variant="up-scale">
            <DemoVideoPlayer />
          </ScrollReveal>
        </section>

        <HackathonContext />

        <section id="story" className="landing-section py-12">
          <ScrollReveal variant="up-scale">
            <GlassCard strong className="p-8 sm:p-10">
              <h2 className="text-2xl font-bold text-ink-900">{landingContent.ask.title}</h2>
              <p className="mt-4 max-w-3xl text-base leading-relaxed text-ink-muted">
                {landingContent.ask.body}
              </p>
            </GlassCard>
          </ScrollReveal>
        </section>

        <section className="landing-section py-12">
          <ScrollReveal className="mb-10 text-center" variant="up">
            <h2 className="text-3xl font-bold text-ink-900">What we built</h2>
            <p className="mt-2 text-ink-muted">Three surfaces, one intelligence pipeline.</p>
          </ScrollReveal>
          <div className="grid gap-4 md:grid-cols-3">
            {landingContent.surfaces.map((surface, i) => (
              <ScrollReveal key={surface.title} delay={i * 100} variant="up">
                <GlassCard className="h-full p-6" strong={i === 1}>
                  <span className="text-3xl" aria-hidden="true">
                    {surface.icon}
                  </span>
                  <h3 className="mt-4 text-lg font-semibold text-ink-900">{surface.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-ink-muted">{surface.description}</p>
                </GlassCard>
              </ScrollReveal>
            ))}
          </div>
        </section>

        <LifecycleSteps />

        <section className="landing-section py-12">
          <ScrollReveal variant="blur">
            <GlassCard className="border-flame/20 bg-flame/5 p-8">
              <h2 className="text-xl font-bold text-ink-900">{landingContent.differentiator.title}</h2>
              <p className="mt-3 max-w-3xl text-sm leading-relaxed text-ink-muted">
                {landingContent.differentiator.body}
              </p>
            </GlassCard>
          </ScrollReveal>
        </section>

        <section className="landing-section py-12">
          <ScrollReveal className="mb-8 text-center" variant="fade">
            <h2 className="text-2xl font-bold text-ink-900">Built with</h2>
          </ScrollReveal>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {landingContent.integrations.map((item, i) => (
              <ScrollReveal key={item.name} delay={i * 60} variant="scale">
                <span className="glass-pill flex items-center gap-2 border-subtle bg-white/60 px-4 py-2 text-sm font-medium text-ink-900">
                  {item.logo && (
                    <img src={item.logo} alt="" className="h-5 w-5 object-contain" />
                  )}
                  {item.name}
                </span>
              </ScrollReveal>
            ))}
          </div>
        </section>

        <section className="landing-section pb-20 pt-8">
          <ScrollReveal variant="up-scale">
            <GlassCard strong className="p-10 text-center">
              <h2 className="text-2xl font-bold text-ink-900">Ready to explore?</h2>
              <p className="mx-auto mt-3 max-w-lg text-ink-muted">
                Open the live web app — review events, warmth scores, connections, and follow-ups.
              </p>
              <Link
                to={landingContent.links.app}
                className="mt-8 inline-block rounded-xl bg-gradient-to-r from-ember to-flame px-8 py-3.5 text-sm font-semibold text-white shadow-glass transition-transform duration-300 hover:scale-[1.02]"
              >
                Open the app
              </Link>
            </GlassCard>
          </ScrollReveal>
        </section>
      </main>

      <ScrollReveal as="footer" className="landing-section border-t border-subtle py-8 text-center text-xs text-ink-faint" variant="fade">
        <p>
          Warmth · GTM Hackathon London · June 2026 ·{" "}
          <a
            href={landingContent.links.hackathon}
            target="_blank"
            rel="noopener noreferrer"
            className="text-flame hover:text-ember"
          >
            GTMengineer.dev
          </a>
        </p>
      </ScrollReveal>
    </div>
  );
}
