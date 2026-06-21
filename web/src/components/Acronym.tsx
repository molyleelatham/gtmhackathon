import { Fragment, type ReactNode } from "react";
import { ACRONYM_PATTERN, ACRONYMS, type AcronymKey } from "../lib/acronyms";

export function Acronym({
  term,
  children,
  className = "",
}: {
  term: AcronymKey;
  children?: ReactNode;
  className?: string;
}) {
  const label = children ?? term;

  return (
    <span className={`acronym-tip group/acronym relative inline ${className}`} tabIndex={0}>
      <span className="border-b border-dotted border-current/40">{label}</span>
      <span className="acronym-tip__popup" role="tooltip">
        {ACRONYMS[term].full}
      </span>
    </span>
  );
}

export function AcronymText({
  children,
  className = "",
}: {
  children: string;
  className?: string;
}) {
  const parts = children.split(ACRONYM_PATTERN);

  return (
    <span className={className}>
      {parts.map((part, index) =>
        part in ACRONYMS ? (
          <Acronym key={`${part}-${index}`} term={part as AcronymKey} />
        ) : (
          <Fragment key={index}>{part}</Fragment>
        ),
      )}
    </span>
  );
}
