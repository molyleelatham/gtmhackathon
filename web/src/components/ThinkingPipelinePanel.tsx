import { useEffect, useRef } from "react";
import type { PipelineStep } from "../lib/liveDemo";

interface ThinkingPipelinePanelProps {
  open: boolean;
  steps: PipelineStep[];
  running: boolean;
  transcript?: string | null;
  onClose: () => void;
  onCancel?: () => void;
}

function StepIcon({ status }: { status: PipelineStep["status"] }) {
  if (status === "done") {
    return (
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-warmth-warm/20 text-xs text-flame">
        ✓
      </span>
    );
  }
  if (status === "running") {
    return (
      <span className="relative flex h-6 w-6 shrink-0 items-center justify-center">
        <span className="absolute h-6 w-6 animate-ping rounded-full bg-orange/25" />
        <span className="relative h-2.5 w-2.5 rounded-full bg-flame" />
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-red-brand/15 text-xs text-red-brand">
        !
      </span>
    );
  }
  return (
    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-subtle bg-muted">
      <span className="h-1.5 w-1.5 rounded-full bg-ink-faint" />
    </span>
  );
}

export function ThinkingPipelinePanel({
  open,
  steps,
  running,
  transcript,
  onClose,
  onCancel,
}: ThinkingPipelinePanelProps) {
  const listRef = useRef<HTMLDivElement>(null);
  const activeId =
    steps.find((s) => s.status === "running")?.id ??
    [...steps].reverse().find((s) => s.status === "done")?.id;

  useEffect(() => {
    if (!open || !activeId || !listRef.current) return;
    const el = listRef.current.querySelector(`[data-step="${activeId}"]`);
    el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [open, activeId]);

  if (!open) return null;

  const doneCount = steps.filter((s) => s.status === "done").length;
  const progress = Math.round((doneCount / Math.max(steps.length, 1)) * 100);

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/25 backdrop-blur-[2px]"
        onClick={running ? undefined : onClose}
        aria-hidden
      />
      <aside
        className="glass-strong fixed inset-y-0 right-0 z-50 flex w-[min(420px,100vw)] animate-drawer-in flex-col border-l border-subtle shadow-glass-lg"
        role="dialog"
        aria-label="Thinking pipeline"
      >
        <div className="border-b border-subtle px-5 py-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                {running && (
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-flame opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-flame" />
                  </span>
                )}
                <p className="text-xs font-semibold uppercase tracking-wider text-flame">
                  Live demo
                </p>
              </div>
              <h2 className="mt-1 text-lg font-bold text-ink-900">Thinking pipeline</h2>
              <p className="mt-1 text-xs text-ink-muted">
                iOS capture → roster match → knowledge graph → warmth score
              </p>
            </div>
            <button
              type="button"
              onClick={running ? onCancel : onClose}
              className="icon-btn h-8 w-8 shrink-0 text-ink-muted"
              aria-label={running ? "Cancel demo" : "Close"}
            >
              ✕
            </button>
          </div>

          <div className="mt-4">
            <div className="mb-1 flex justify-between text-[10px] font-medium text-ink-faint">
              <span>{running ? "Processing…" : doneCount === steps.length ? "Complete" : "Paused"}</span>
              <span>{progress}%</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-gradient-to-r from-flame to-red-brand transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {transcript && (
          <div className="border-b border-subtle bg-orange/5 px-5 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-ink-faint">
              Live transcript
            </p>
            <p className="mt-1 text-sm italic text-ink-800">&ldquo;{transcript}&rdquo;</p>
          </div>
        )}

        <div ref={listRef} className="flex-1 space-y-0 overflow-y-auto px-5 py-4">
          {steps.map((step, index) => {
            const isActive = step.status === "running";
            const isDone = step.status === "done";
            const isError = step.status === "error";
            return (
              <div
                key={step.id}
                data-step={step.id}
                className={`relative flex gap-3 pb-5 last:pb-0 ${
                  isActive ? "animate-fade-up" : ""
                }`}
              >
                {index < steps.length - 1 && (
                  <span
                    className={`absolute left-3 top-7 h-[calc(100%-12px)] w-px ${
                      isDone ? "bg-orange/40" : "bg-subtle"
                    }`}
                  />
                )}
                <StepIcon status={step.status} />
                <div className="min-w-0 flex-1 pt-0.5">
                  <p
                    className={`text-sm font-semibold ${
                      isActive
                        ? "text-flame"
                        : isError
                          ? "text-red-brand"
                          : isDone
                            ? "text-ink-900"
                            : "text-ink-muted"
                    }`}
                  >
                    {step.label}
                  </p>
                  <p
                    className={`mt-0.5 text-xs leading-relaxed ${
                      isActive || isDone || isError ? "text-ink-muted" : "text-ink-faint"
                    }`}
                  >
                    {step.detail}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        <div className="border-t border-subtle px-5 py-4">
          {running ? (
            <button type="button" onClick={onCancel} className="btn-secondary w-full py-2.5">
              Cancel demo
            </button>
          ) : (
            <button type="button" onClick={onClose} className="glass-interactive w-full rounded-xl border border-orange/30 bg-orange/10 py-2.5 text-sm font-semibold text-flame">
              Close pipeline
            </button>
          )}
        </div>
      </aside>
    </>
  );
}
