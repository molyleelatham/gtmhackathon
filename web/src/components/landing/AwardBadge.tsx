export function AwardBadge({ label }: { label: string }) {
  return (
    <span className="glass-pill inline-flex items-center gap-1.5 border-orange/25 bg-orange/10 px-3 py-1.5 text-xs font-semibold text-ember">
      <span aria-hidden="true">🏆</span>
      {label}
    </span>
  );
}
