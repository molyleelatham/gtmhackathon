import type { WarmthBand } from "../types";

function bandFor(score: number): WarmthBand {
  if (score >= 70) return "hot";
  if (score >= 40) return "warm";
  return "cold";
}

const styles: Record<WarmthBand, string> = {
  hot: "bg-warmth-hot/15 text-warmth-hot border-warmth-hot/40",
  warm: "bg-warmth-warm/15 text-warmth-warm border-warmth-warm/40",
  cold: "bg-warmth-cold/15 text-warmth-cold border-warmth-cold/40",
};

export function WarmthBadge({ score, band }: { score: number; band?: WarmthBand }) {
  const resolved = band ?? bandFor(score);
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[resolved]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {resolved.toUpperCase()} · {Math.round(score)}
    </span>
  );
}
