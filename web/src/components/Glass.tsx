import type { ReactNode } from "react";

/** Frosted "liquid glass" surface (iOS 26 style). */
export function GlassCard({
  children,
  className = "",
  strong = false,
}: {
  children: ReactNode;
  className?: string;
  strong?: boolean;
}) {
  return (
    <div className={`${strong ? "glass-strong" : "glass"} ${className}`}>{children}</div>
  );
}

/** Glass panel with a header row — used for the dashboard columns. */
export function GlassPanel({
  title,
  meta,
  children,
  className = "",
  bodyClassName = "",
}: {
  title: string;
  meta?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section className={`glass flex flex-col overflow-hidden ${className}`}>
      <div className="flex items-baseline justify-between border-b border-subtle px-4 py-3">
        <h2 className="text-sm font-semibold tracking-tight text-ink-900">{title}</h2>
        {meta && <span className="text-xs text-ink-faint">{meta}</span>}
      </div>
      <div className={`flex-1 overflow-y-auto p-2 ${bodyClassName}`}>{children}</div>
    </section>
  );
}
