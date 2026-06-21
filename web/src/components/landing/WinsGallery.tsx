import { useState } from "react";
import { landingContent, type LandingMoment } from "../../content/landingContent";
import { AwardBadge } from "./AwardBadge";
import { ScrollReveal } from "./ScrollReveal";

function MomentFrame({
  moment,
  className = "",
  onClick,
}: {
  moment: LandingMoment;
  className?: string;
  onClick?: () => void;
}) {
  const inner = (
    <>
      <div className={`overflow-hidden rounded-xl ${className}`}>
        <img
          src={moment.src}
          alt={moment.alt}
          className="h-full w-full object-cover transition-transform duration-700 ease-out hover:scale-[1.03]"
          loading="lazy"
        />
      </div>
      <p className="mt-2 text-sm text-ink-muted">{moment.caption}</p>
    </>
  );

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className="group w-full text-left">
        {inner}
      </button>
    );
  }

  return <div className="group">{inner}</div>;
}

export function WinsGallery() {
  const [lightbox, setLightbox] = useState<LandingMoment | null>(null);

  return (
    <section id="wins" className="landing-section py-16">
      <ScrollReveal className="mb-10 text-center" variant="up">
        <h2 className="text-3xl font-bold text-ink-900">We won.</h2>
        <div className="mt-4 flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4">
          <AwardBadge label={landingContent.awards.zeroCRM} size="lg" featured />
          <AwardBadge label={landingContent.awards.cursorTrack} size="md" />
        </div>
      </ScrollReveal>

      <div className="grid gap-6 sm:grid-cols-2">
        {landingContent.moments.map((moment, i) => (
          <ScrollReveal key={moment.src} delay={i * 120} variant="up-scale">
            <MomentFrame
              moment={moment}
              className="aspect-[4/3]"
              onClick={() => setLightbox(moment)}
            />
          </ScrollReveal>
        ))}
      </div>

      {lightbox && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-ink-900/60 p-4 backdrop-blur-sm"
          onClick={() => setLightbox(null)}
          role="dialog"
          aria-modal="true"
          aria-label="Photo preview"
        >
          <div className="glass-strong max-h-[90vh] max-w-4xl overflow-hidden rounded-2xl p-2">
            <img
              src={lightbox.src}
              alt={lightbox.alt}
              className="max-h-[80vh] w-full rounded-xl object-contain"
            />
            <p className="px-2 py-3 text-center text-sm text-ink-muted">{lightbox.caption}</p>
          </div>
        </div>
      )}
    </section>
  );
}
