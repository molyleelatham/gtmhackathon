import { useState } from "react";
import type { TeamMember } from "../../content/landingContent";
import { CrownIcon } from "./CrownIcon";

interface TeamCardProps {
  member: TeamMember;
  showCrown?: boolean;
  winner?: boolean;
}

export function TeamCard({ member, showCrown = false, winner = false }: TeamCardProps) {
  const [expanded, setExpanded] = useState(false);
  const hasBio = member.bio.length > 0;

  return (
    <article
      className={`flex h-full flex-col overflow-hidden rounded-2xl ${
        winner
          ? "border border-amber/25 bg-white/80 shadow-glass backdrop-blur-glass"
          : "glass-strong"
      }`}
    >
      <div className="p-6">
        <div className="relative mx-auto mb-4 w-fit">
          {showCrown && (
            <div
              className="absolute -top-6 left-1/2 z-10 -translate-x-1/2 drop-shadow-md"
              title="Winning team"
            >
              <CrownIcon className="h-8 w-8 sm:h-9 sm:w-9" />
            </div>
          )}
          <div
            className={`h-28 w-28 overflow-hidden rounded-full border-2 border-white/90 shadow-glass ${
              winner ? "ring-[3px] ring-amber/50 ring-offset-2 ring-offset-[#fff8f3]" : "ring-2 ring-orange/20"
            }`}
          >
            <img
              src={member.photo}
              alt={member.name}
              className="h-full w-full object-cover"
              loading="lazy"
            />
          </div>
          {winner && (
            <span className="absolute -bottom-1 left-1/2 z-10 -translate-x-1/2 whitespace-nowrap rounded-full border border-amber/40 bg-gradient-to-r from-amber/20 to-orange/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-ember">
              Winner
            </span>
          )}
        </div>

        <h3 className="mt-2 text-center text-lg font-bold text-ink-900">
          <a
            href={member.linkedin}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-flame"
          >
            {member.name}
          </a>
        </h3>
        <p className="mt-1 text-center text-xs leading-relaxed text-ink-muted">{member.title}</p>

        {expanded && (
          <p className="mt-4 text-sm leading-relaxed text-ink-secondary">{member.bio}</p>
        )}

        {hasBio && (
          <button
            type="button"
            onClick={() => setExpanded((e) => !e)}
            className={`text-xs font-semibold text-flame hover:text-ember ${expanded ? "mt-2" : "mt-4"}`}
          >
            {expanded ? "Show less" : "Read more"}
          </button>
        )}

        <div className="mt-4 flex flex-wrap justify-center gap-2">
          <a
            href={member.linkedin}
            target="_blank"
            rel="noopener noreferrer"
            className="glass-pill px-3 py-1 text-xs font-medium text-ink-muted hover:text-flame"
          >
            LinkedIn
          </a>
          {member.website && (
            <a
              href={member.website}
              target="_blank"
              rel="noopener noreferrer"
              className="glass-pill px-3 py-1 text-xs font-medium text-ink-muted hover:text-flame"
            >
              Website
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
