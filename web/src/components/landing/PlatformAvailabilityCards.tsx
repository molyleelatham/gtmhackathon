import { Link } from "react-router-dom";
import { landingContent } from "../../content/landingContent";
import { PlatformAppMark } from "./PlatformAppMark";

interface PlatformAvailabilityCardsProps {
  webCta?: string;
  className?: string;
}

export function PlatformAvailabilityCards({
  webCta = landingContent.hero.availability.web.cta,
  className = "",
}: PlatformAvailabilityCardsProps) {
  return (
    <div className={`flex flex-wrap items-stretch justify-center gap-4 ${className}`}>
      <div className="glass flex w-full min-w-[220px] max-w-xs flex-col items-center rounded-2xl p-5 text-center sm:w-auto">
        <PlatformAppMark platform="web" />
        <p className="mt-4 text-sm font-semibold text-ink-900">
          {landingContent.hero.availability.web.label}
        </p>
        <Link
          to={landingContent.links.app}
          className="mt-4 rounded-xl bg-gradient-to-r from-ember to-flame px-6 py-3 text-sm font-semibold text-white shadow-glass transition-transform duration-300 hover:scale-[1.02]"
        >
          {webCta}
        </Link>
      </div>

      <div className="glass flex w-full min-w-[220px] max-w-xs flex-col items-center rounded-2xl p-5 text-center sm:w-auto">
        <PlatformAppMark platform="ios" />
        <p className="mt-4 text-sm font-semibold text-ink-900">
          {landingContent.hero.availability.ios.label}
        </p>
        <span className="glass-pill mt-4 border-amber/30 bg-amber/10 px-4 py-3 text-sm font-medium text-ink-muted">
          {landingContent.testFlight.label}
        </span>
      </div>
    </div>
  );
}
