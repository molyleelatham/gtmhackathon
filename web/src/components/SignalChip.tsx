import type { SignalType } from "../lib/mockData";

const LABELS: Record<SignalType, string> = {
  hiring: "Hiring",
  funding: "Funding",
  intent: "Intent",
};

const STYLES: Record<SignalType, string> = {
  hiring: "border-signal-hiring/45 bg-signal-hiring/15 text-signal-hiring",
  funding: "border-signal-funding/45 bg-signal-funding/15 text-signal-funding",
  intent: "border-signal-intent/45 bg-signal-intent/15 text-signal-intent",
};

/** Signal-type chip for the Signal Feed (Hiring / Funding / Intent). */
export function SignalChip({ type }: { type: SignalType }) {
  return (
    <span className={`glass-pill uppercase tracking-wide ${STYLES[type]}`}>
      {LABELS[type]}
    </span>
  );
}
