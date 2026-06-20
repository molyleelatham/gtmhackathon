export function Toggle({
  checked,
  onChange,
  label,
  accent = false,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  label?: string;
  accent?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="glass-interactive flex items-center gap-2.5 rounded-full border border-subtle bg-glass-strong px-3 py-1.5"
    >
      {label && <span className="text-xs font-medium text-ink-800">{label}</span>}
      <span
        className={`relative h-5 w-9 shrink-0 overflow-hidden rounded-full transition-colors ${
          checked ? (accent ? "bg-red-brand" : "bg-orange") : "bg-ink-faint/40"
        }`}
      >
        <span
          className={`absolute top-0.5 h-4 w-4 rounded-full bg-[var(--surface-page)] shadow transition-all ${
            checked ? "left-[calc(100%-1rem-0.125rem)]" : "left-0.5"
          }`}
        />
      </span>
    </button>
  );
}
