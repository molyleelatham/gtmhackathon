import { Link } from "react-router-dom";
import { landingContent } from "../../content/landingContent";
import { WarmthLogo } from "../WarmthLogo";

export function LandingNav() {
  const anchors = [
    { href: "#team", label: "Team" },
    { href: "#wins", label: "Wins" },
    { href: "#demo", label: "Demo" },
    { href: "#story", label: "Story" },
  ];

  return (
    <header className="nav-enter sticky top-0 z-50 border-b border-subtle bg-[rgba(255,248,243,0.72)] backdrop-blur-glass">
      <div className="landing-section flex items-center justify-between gap-4 py-3">
        <a href="#" className="flex items-center gap-2.5">
          <WarmthLogo size="sm" />
          <span className="text-sm font-bold text-ink-900">Warmth</span>
        </a>

        <nav className="hidden items-center gap-6 sm:flex">
          {anchors.map((a) => (
            <a
              key={a.href}
              href={a.href}
              className="text-sm text-ink-muted transition-colors hover:text-flame"
            >
              {a.label}
            </a>
          ))}
        </nav>

        <Link
          to={landingContent.links.app}
          className="glass-pill border-orange/30 bg-orange/10 px-4 py-2 text-sm font-semibold text-ember transition-all hover:bg-orange/20"
        >
          Open app
        </Link>
      </div>
    </header>
  );
}
