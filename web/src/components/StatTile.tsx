import type { ReactNode } from "react";

export function StatTile({
  label,
  value,
  active = false,
  accent = false,
  onClick,
}: {
  label: ReactNode;
  value: string | number;
  active?: boolean;
  accent?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`glass-interactive flex flex-col items-start rounded-2xl border px-4 py-3 text-left ${
        active
          ? "border-orange/30 bg-orange/10 shadow-glass"
          : "border-subtle bg-muted"
      }`}
    >
      <span className="text-[0.7rem] font-medium uppercase tracking-wider text-ink-faint">
        {label}
      </span>
      <span
        className={`mt-1 text-3xl font-bold tabular-nums ${
          accent ? "text-warmth-hot" : "text-ink-900"
        }`}
      >
        {value}
      </span>
    </button>
  );
}
