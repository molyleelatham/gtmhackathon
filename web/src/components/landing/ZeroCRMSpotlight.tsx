import { landingContent } from "../../content/landingContent";
import { usePartnerBannerMouse } from "../../lib/usePartnerBannerMouse";
import { ScrollReveal } from "./ScrollReveal";
import { AcronymText } from "../Acronym";

export function ZeroCRMSpotlight() {
  const { zeroCRMSpotlight, awards } = landingContent;
  const { banner } = zeroCRMSpotlight;
  const mouse = usePartnerBannerMouse();

  return (
    <div
      ref={mouse.ref}
      className={`zero-banner-shell partner-banner-shell${mouse.hovering ? " is-hovering" : ""}`}
      onMouseEnter={mouse.onMouseEnter}
      onMouseLeave={mouse.onMouseLeave}
      onMouseMove={mouse.onMouseMove}
    >
      <section id="zero-crm" className="relative w-full overflow-hidden bg-black text-white">
        <div className="pointer-events-none absolute inset-0 bg-black" aria-hidden="true" />
        <div className="zero-banner-grid pointer-events-none absolute inset-0" aria-hidden="true" />
        <div className="zero-banner-glow pointer-events-none absolute inset-0" aria-hidden="true" />
        <div
          className="partner-banner-mouse-glow partner-banner-mouse-glow--zero"
          aria-hidden="true"
        />

        <div className="relative mx-auto max-w-6xl px-5 pt-8 pb-5 sm:px-8 sm:pt-10 sm:pb-6">
          <ScrollReveal variant="up">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <img
                  src="/logos/zero.png"
                  alt="Zero"
                  className="h-11 w-11 rounded-lg object-cover sm:h-12 sm:w-12"
                />
                <div>
                  <p className="text-xl font-bold tracking-tight text-white sm:text-2xl">Zero</p>
                  <p className="text-xs text-zero-muted sm:text-sm">The zero-click CRM</p>
                </div>
              </div>

              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-2 text-xs font-semibold sm:text-sm">
                <span
                  className="flex h-6 w-6 items-center justify-center rounded-md bg-zero-yellow/15 text-sm"
                  aria-hidden="true"
                >
                  🏆
                </span>
                {awards.zeroCRM}
              </div>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={100} variant="up">
            <p className="mt-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs font-medium text-zero-muted">
              <span className="inline-block h-2 w-2 rounded-sm bg-zero-yellow" aria-hidden="true" />
              {banner.eyebrow}
            </p>
          </ScrollReveal>

          <ScrollReveal delay={180} variant="up">
            <h2 className="mt-4 max-w-4xl text-3xl font-bold leading-[1.08] tracking-tight text-white sm:text-4xl lg:text-5xl">
              <span className="text-white">{banner.headline}</span>
              <span className="block text-zero-yellow">{banner.headlineAccent}</span>
            </h2>
          </ScrollReveal>

          <ScrollReveal delay={260} variant="up">
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-zero-muted sm:text-base">
              <AcronymText>{banner.subheadline}</AcronymText>
            </p>
          </ScrollReveal>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            {banner.features.map((feature, i) => (
              <ScrollReveal key={feature.label} delay={320 + i * 80} variant="up">
                <div className="h-full rounded-xl border border-white/10 bg-white/[0.03] p-4 transition-colors hover:border-zero-yellow/30 hover:bg-white/[0.05]">
                  <p className="text-xs font-bold text-zero-yellow sm:text-sm">
                    <AcronymText>{feature.label}</AcronymText>
                  </p>
                  <p className="mt-1.5 text-xs leading-relaxed text-neutral-300 sm:text-sm">
                    <AcronymText>{feature.detail}</AcronymText>
                  </p>
                </div>
              </ScrollReveal>
            ))}
          </div>

          <ScrollReveal delay={560} variant="fade">
            <div className="mt-5">
              <a
                href={banner.ctaUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center rounded-full bg-zero-yellow px-6 py-3 text-sm font-bold text-black transition-transform hover:scale-[1.02]"
              >
                {banner.cta}
              </a>
            </div>
          </ScrollReveal>
        </div>
      </section>
    </div>
  );
}
