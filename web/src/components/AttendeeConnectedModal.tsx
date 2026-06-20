import { Avatar } from "./Avatar";
import { ICPBadge } from "./ICPBadge";
import { KnowledgeGraphView } from "./KnowledgeGraphView";
import { WarmthBadge } from "./WarmthBadge";
import type { AttendeeMatchResult } from "../types";

interface AttendeeConnectedModalProps {
  match: AttendeeMatchResult | null;
  onClose: () => void;
  onViewProfile?: (connectionId: string) => void;
}

export function AttendeeConnectedModal({ match, onClose, onViewProfile }: AttendeeConnectedModalProps) {
  if (!match?.matched) return null;

  const conn = match.connection;
  const name = conn?.name ?? match.name ?? "Attendee";
  const company = conn?.company_name ?? "";
  const title = conn?.title ?? "";
  const kg = match.knowledge_graph?.[0];
  const interests = match.interests ?? [];
  const connectionId = conn?.id;

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm animate-fade-up"
        onClick={onClose}
        aria-hidden
      />
      <div
        className="glass-strong fixed left-1/2 top-1/2 z-50 w-[min(440px,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 animate-drawer-in rounded-3xl p-6 shadow-glass"
        role="dialog"
        aria-label={`Connected with ${name}`}
      >
        <div className="flex items-start gap-4">
          <Avatar name={name} size="xl" />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-flame">
              Attendee matched
            </p>
            <h2 className="mt-1 text-xl font-bold text-ink-900">{match.message}</h2>
            <p className="mt-1 text-sm text-ink-muted">
              {title}
              {title && company ? " · " : ""}
              {company}
            </p>
            {match.score != null && (
              <p className="mt-1 text-xs text-ink-faint">
                Match confidence {Math.round(match.score * 100)}%
                {match.matched_on?.length ? ` · ${match.matched_on.join(", ")}` : ""}
              </p>
            )}
          </div>
          <button type="button" onClick={onClose} className="icon-btn h-8 w-8 shrink-0" aria-label="Close">
            ✕
          </button>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          {conn?.predicted_warmth != null && <WarmthBadge score={conn.predicted_warmth} />}
          {conn?.icp_score != null && <ICPBadge score={conn.icp_score} />}
        </div>

        <div className="mt-4">
          <KnowledgeGraphView
            personName={name}
            interests={interests}
            topicWeights={kg?.topic_weights}
            values={kg?.values}
            height={260}
          />
        </div>

        {interests.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {interests.map((i) => (
              <span key={i} className="glass-pill border-orange/30 bg-orange/10 text-flame">
                {i}
              </span>
            ))}
          </div>
        )}

        <div className="mt-5 flex gap-2">
          {connectionId && onViewProfile && (
            <button
              type="button"
              onClick={() => {
                onViewProfile(connectionId);
                onClose();
              }}
              className="glass-interactive flex-1 rounded-xl border border-orange/40 bg-orange/15 py-2.5 text-sm font-semibold text-flame"
            >
              View full profile
            </button>
          )}
          <button type="button" onClick={onClose} className="btn-secondary flex-1 py-2.5">
            Keep capturing
          </button>
        </div>
      </div>
    </>
  );
}
