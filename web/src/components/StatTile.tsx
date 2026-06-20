export function StatTile({
  label,
  value,
  active = false,
  accent = false,
  onClick,
}: {
  label: string;
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
          ? "border-white/30 bg-white/15 shadow-glass"
          : "border-white/12 bg-white/[0.06]"
      }`}
    >
      <span className="text-[0.7rem] font-medium uppercase tracking-wider text-white/55">
        {label}
      </span>
      <span
        className={`mt-1 text-3xl font-bold tabular-nums ${
          accent ? "text-warmth-hot" : "text-white"
        }`}
      >
        {value}
      </span>
    </button>
  );
}
