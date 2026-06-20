// Brand marks for the "Draft Email" action: Lightfern (personalizes copy) +
// Gmail (creates the draft via Google MCP).

/**
 * Lightfern mark — official glyph, cropped from the supplied wordmark.
 * `lightfern.png` is white-on-transparent (for dark UI); `lightfern-dark.png`
 * is the original dark glyph (for light surfaces).
 */
export function LightfernMark({
  className = "h-4 w-4",
  variant = "light",
}: {
  className?: string;
  variant?: "light" | "dark";
}) {
  const src = variant === "dark" ? "/logos/lightfern-dark.png" : "/logos/lightfern-dark.png";
  return <img src={src} alt="Lightfern" className={`${className} object-contain`} />;
}

/** Gmail mark — current multicolor envelope (user-supplied asset). */
export function GmailMark({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <img src="/logos/gmail.png" alt="Gmail" className={`${className} object-contain`} />
  );
}
