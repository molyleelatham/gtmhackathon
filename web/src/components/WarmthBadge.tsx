import type { WarmthBand } from "../types";

function bandFor(score: number): WarmthBand {
  if (score >= 70) return "hot";
  if (score >= 40) return "warm";
  return "cold";
}

const styles: Record<WarmthBand, string> = {
  hot: "bg-warmth-hot/20 text-warmth-hot border-warmth-hot/45",
  warm: "bg-warmth-warm/20 text-warmth-warm border-warmth-warm/45",
  cold: "bg-warmth-cold/20 text-warmth-cold border-warmth-cold/45",
};

export function WarmthBadge({
  score,
  band,
  className = "",
}: {
  score: number;
  band?: WarmthBand;
  className?: string;
}) {
  const resolved = band ?? bandFor(score);
  return (
    <span className={`glass-pill ${styles[resolved]} ${className}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {resolved.toUpperCase()} · {Math.round(score)}
    </span>
  );
}
