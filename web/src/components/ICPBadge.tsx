import { bandFor, type ICPBand } from "../lib/uiTypes";

const LABELS: Record<ICPBand, string> = { hot: "Hot", warm: "Warm", cold: "Cold" };

const STYLES: Record<ICPBand, string> = {
  hot: "border-red-brand/40 bg-red-brand/10 text-red-brand",
  warm: "border-orange/40 bg-orange/10 text-flame",
  cold: "border-ink-faint/40 bg-muted text-ink-muted",
};

export function ICPBadge({
  score,
  band,
  className = "",
}: {
  score: number;
  band?: ICPBand;
  className?: string;
}) {
  const resolved = band ?? bandFor(score);
  return (
    <span className={`glass-pill ${STYLES[resolved]} ${className}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {Math.round(score)} · {LABELS[resolved]}
    </span>
  );
}
