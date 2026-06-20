const ALLOWED_GMAIL_HOSTS = new Set(["mail.google.com", "gmail.com"]);

/** Allow only https Gmail compose links from the API (blocks javascript: / open redirects). */
export function safeGmailComposeUrl(raw: unknown): string | null {
  if (typeof raw !== "string" || !raw.trim()) return null;
  try {
    const url = new URL(raw);
    if (url.protocol !== "https:") return null;
    if (!ALLOWED_GMAIL_HOSTS.has(url.hostname)) return null;
    return url.toString();
  } catch {
    return null;
  }
}
