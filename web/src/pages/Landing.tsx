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
import { PlatformAppMark } from "../components/landing/PlatformAppMark";
import { ScrollReveal } from "../components/landing/ScrollReveal";
import { Acronym, AcronymText } from "../components/Acronym";
import { ZeroCRMSpotlight } from "../components/landing/ZeroCRMSpotlight";
import { CursorSpotlight } from "../components/landing/CursorSpotlight";

export function Landing() {
  return (
    <div className="min-h-screen">
      <LandingNav />
      <main>
        <LandingHero />

        <WinningTeamSection />

        <div className="flex flex-col gap-6 sm:gap-8">
          <ScrollReveal variant="up-scale" className="w-full">
            <ZeroCRMSpotlight />
          </ScrollReveal>
          <ScrollReveal delay={120} variant="up-scale" className="w-full">
            <CursorSpotlight />
          </ScrollReveal>
        </div>

        <WinsGallery />

        <section id="demo" className="landing-section py-16">
          <ScrollReveal className="mb-8 text-center" variant="up">
            <h2 className="text-3xl font-bold text-ink-900">See Warmth in action</h2>
            <p className="mt-2 text-ink-muted">From phrase trigger to Gmail draft in 60 seconds.</p>
          </ScrollReveal>
          <ScrollReveal delay={120} variant="fade">
            <DemoVideoPlayer />
          </ScrollReveal>
        </section>

        <HackathonContext />

        <section id="story" className="landing-section py-12">
          <ScrollReveal variant="up-scale">
            <GlassCard strong className="p-8 sm:p-10">
              <h2 className="text-2xl font-bold text-ink-900">{landingContent.ask.title}</h2>
              <p className="mt-4 max-w-3xl text-base leading-relaxed text-ink-muted">
                <AcronymText>{landingContent.ask.body}</AcronymText>
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
                  <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                    <AcronymText>{surface.description}</AcronymText>
                  </p>
                </GlassCard>
              </ScrollReveal>
            ))}
          </div>
        </section>

        <LifecycleSteps />

        <section className="landing-section py-12">
          <ScrollReveal variant="blur">
            <GlassCard className="border-flame/20 bg-flame/5 p-8 sm:p-10">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-flame">
                Zero <Acronym term="CRM">CRM</Acronym> × Warmth
              </p>
              <h2 className="mt-2 text-2xl font-bold text-ink-900 sm:text-3xl">
                Warmth ≠ <Acronym term="ICP">ICP</Acronym>
              </h2>
              <p className="mt-3 max-w-3xl text-base font-medium leading-relaxed text-ink-800">
                <AcronymText>{landingContent.differentiator.icpLead}</AcronymText>
              </p>
              <p className="mt-4 max-w-3xl text-base leading-relaxed text-ink-muted sm:text-lg">
                <AcronymText>{landingContent.differentiator.body}</AcronymText>
              </p>
            </GlassCard>
          </ScrollReveal>
        </section>

        <section className="landing-section py-12">
          <ScrollReveal className="mb-8 text-center" variant="fade">
            <h2 className="text-2xl font-bold text-ink-900">Built with</h2>
          </ScrollReveal>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {landingContent.integrations.map((item, i) => {
              const isZeroCRM = item.name === "Zero CRM";
              const isCursor = item.name === "Cursor";
              const pillClass = isZeroCRM
                ? "glass-pill flex items-center gap-2.5 border-2 border-flame/35 bg-gradient-to-r from-orange/15 to-flame/10 px-6 py-3 text-base font-bold text-ink-900 shadow-glass sm:px-7 sm:py-3.5 sm:text-lg"
                : isCursor
                  ? "glass-pill flex items-center gap-2 border-orange/25 bg-orange/10 px-5 py-2.5 text-sm font-semibold text-ink-900 sm:text-base"
                  : "glass-pill flex items-center gap-2 border-subtle bg-white/60 px-4 py-2 text-sm font-medium text-ink-900";

              return (
                <ScrollReveal key={item.name} delay={i * 60} variant="scale">
                  <span className={pillClass}>
                    {item.logo && (
                      <img
                        src={item.logo}
                        alt=""
                        className={`object-contain ${
                          isZeroCRM
                            ? "h-7 w-7 rounded-md"
                            : isCursor
                              ? "h-8 w-8"
                              : "h-5 w-5"
                        }`}
                      />
                    )}
                    {item.name}
                  </span>
                </ScrollReveal>
              );
            })}
          </div>
        </section>

        <section className="landing-section pb-20 pt-8">
          <ScrollReveal variant="up-scale">
            <GlassCard strong className="p-8 sm:p-10">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-ink-900">{landingContent.explore.title}</h2>
                <p className="mx-auto mt-3 max-w-lg text-ink-muted">{landingContent.explore.subtitle}</p>
              </div>
              <div className="mt-8 grid gap-4 sm:grid-cols-2">
                <GlassCard className="flex h-full flex-col p-6 text-center">
                  <PlatformAppMark platform="web" />
                  <h3 className="mt-4 text-lg font-semibold text-ink-900">
                    {landingContent.explore.web.title}
                  </h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-ink-muted">
                    <AcronymText>{landingContent.explore.web.description}</AcronymText>
                  </p>
                  <Link
                    to={landingContent.links.app}
                    className="mt-6 inline-block rounded-xl bg-gradient-to-r from-ember to-flame px-6 py-3 text-sm font-semibold text-white shadow-glass transition-transform duration-300 hover:scale-[1.02]"
                  >
                    {landingContent.explore.web.cta}
                  </Link>
                </GlassCard>
                <GlassCard className="flex h-full flex-col p-6 text-center">
                  <PlatformAppMark platform="ios" />
                  <h3 className="mt-4 text-lg font-semibold text-ink-900">
                    {landingContent.explore.ios.title}
                  </h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-ink-muted">
                    <AcronymText>{landingContent.explore.ios.description}</AcronymText>
                  </p>
                  <span className="glass-pill mx-auto mt-6 border-amber/30 bg-amber/10 px-4 py-3 text-sm font-medium text-ink-muted">
                    {landingContent.testFlight.label}
                  </span>
                </GlassCard>
              </div>
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
        <p className="mt-2 text-ink-muted">{landingContent.testFlight.label}</p>
      </ScrollReveal>
    </div>
  );
}
