import { useEffect, useState } from "react";

/** Compact inline volume bars — sits beside the passive-audio toggle. */
export function AudioWaveform({ active }: { active: boolean }) {
  const [levels, setLevels] = useState<number[]>([0.3, 0.5, 0.6, 0.4, 0.7, 0.5]);

  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => {
      setLevels(Array.from({ length: 6 }, () => 0.25 + Math.random() * 0.75));
    }, 120);
    return () => clearInterval(id);
  }, [active]);

  if (!active) return null;

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-red-brand/30 bg-red-brand/10 px-2 py-1">
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-red-brand" />
      <span className="flex h-4 items-end gap-px">
        {levels.map((h, i) => (
          <span
            key={i}
            className="w-0.5 rounded-full bg-gradient-to-t from-orange to-red-brand transition-all duration-100"
            style={{ height: `${Math.max(20, h * 100)}%` }}
          />
        ))}
      </span>
    </span>
  );
}
