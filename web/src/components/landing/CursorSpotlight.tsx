import { landingContent } from "../../content/landingContent";
import { usePartnerBannerMouse } from "../../lib/usePartnerBannerMouse";
import { ScrollReveal } from "./ScrollReveal";

export function CursorSpotlight() {
  const { cursorSpotlight, awards } = landingContent;
  const { banner } = cursorSpotlight;
  const mouse = usePartnerBannerMouse();

  return (
    <div
      ref={mouse.ref}
      className={`cursor-banner-shell partner-banner-shell${mouse.hovering ? " is-hovering" : ""}`}
      onMouseEnter={mouse.onMouseEnter}
      onMouseLeave={mouse.onMouseLeave}
      onMouseMove={mouse.onMouseMove}
    >
      <section id="cursor" className="relative overflow-hidden text-cursor-ink">
        <div className="cursor-banner-grid pointer-events-none absolute inset-0" aria-hidden="true" />
        <div className="cursor-banner-glow pointer-events-none absolute inset-0" aria-hidden="true" />
        <div
          className="partner-banner-mouse-glow partner-banner-mouse-glow--cursor"
          aria-hidden="true"
        />

        <div className="relative mx-auto max-w-6xl px-5 py-6 sm:px-8 sm:py-7">
          <ScrollReveal variant="up">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between sm:gap-8">
              <div className="flex min-w-0 flex-1 flex-col gap-4 sm:flex-row sm:items-center sm:gap-6">
                <div className="shrink-0 rounded-2xl border border-cursor-border bg-cursor-surface p-3 shadow-sm sm:p-4">
                  <img
                    src="/logos/cursor-icon.png"
                    alt="Cursor"
                    className="h-16 w-16 object-contain sm:h-20 sm:w-20"
                  />
                </div>

                <div className="min-w-0">
                  <p className="inline-flex items-center gap-2 rounded-full border border-cursor-border bg-cursor-surface px-3 py-1 text-[11px] font-semibold text-cursor-muted sm:text-xs">
                    <span aria-hidden="true">🏆</span>
                    {awards.cursorTrack}
                  </p>
                  <h2 className="mt-3 text-xl font-bold leading-tight text-cursor-ink sm:text-2xl">
                    {banner.headline}
                  </h2>
                  <p className="mt-2 max-w-xl text-xs leading-relaxed text-cursor-muted sm:text-sm">
                    {banner.subheadline}
                  </p>
                </div>
              </div>

              <a
                href={banner.ctaUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex shrink-0 items-center justify-center self-start rounded-full bg-cursor-ink px-5 py-2.5 text-xs font-bold text-white transition-transform hover:scale-[1.02] sm:self-center sm:text-sm"
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
