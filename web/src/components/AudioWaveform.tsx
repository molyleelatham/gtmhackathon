import { useEffect, useState } from "react";

/** Animated volume bars shown when passive audio is active. */
export function AudioWaveform({ active }: { active: boolean }) {
  const [levels, setLevels] = useState<number[]>([0.3, 0.5, 0.7, 0.4, 0.6, 0.8, 0.5, 0.3]);

  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => {
      setLevels(Array.from({ length: 8 }, () => 0.2 + Math.random() * 0.8));
    }, 120);
    return () => clearInterval(id);
  }, [active]);

  if (!active) return null;

  return (
    <div className="glass flex items-center gap-3 px-4 py-2.5">
      <span className="flex h-2 w-2 shrink-0 animate-pulse rounded-full bg-red-brand" />
      <span className="text-xs font-medium text-ink-900">Listening</span>
      <div className="flex h-8 items-end gap-0.5">
        {levels.map((h, i) => (
          <span
            key={i}
            className="w-1 rounded-full bg-gradient-to-t from-orange to-red-brand transition-all duration-100"
            style={{ height: `${h * 100}%` }}
          />
        ))}
      </div>
      <span className="text-xs text-ink-muted">Passive audio on</span>
    </div>
  );
}
