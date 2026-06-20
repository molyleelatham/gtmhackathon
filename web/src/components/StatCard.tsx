export function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="glass p-5">
      <div className="text-sm text-ink-muted">{label}</div>
      <div className="mt-1 text-3xl font-semibold tracking-tight tabular-nums text-ink-900">
        {value}
      </div>
      {hint && <div className="mt-1 text-xs text-ink-faint">{hint}</div>}
    </div>
  );
}
