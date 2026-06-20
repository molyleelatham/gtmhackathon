/** Wake phrase aligned with iOS `WakeWord.phrase`. */
export const WAKE_PHRASE = "hey it's nice to meet you";

export function speechRecognitionSupported(): boolean {
  if (typeof window === "undefined") return false;
  const w = window as Window & { webkitSpeechRecognition?: unknown; SpeechRecognition?: unknown };
  return Boolean(w.SpeechRecognition ?? w.webkitSpeechRecognition) && Boolean(navigator.mediaDevices?.getUserMedia);
}

/** Pull a first name from common event greetings in live transcript text. */
export function extractGreetingName(transcript: string): string | null {
  const lowered = transcript.toLowerCase();
  const patterns = [
    /\bhi\s+([a-z][a-z'-]{1,24})\b/i,
    /\bhey\s+([a-z][a-z'-]{1,24})\b/i,
    /\bnice to meet you[,\s]+([a-z][a-z'-]{1,24})\b/i,
  ];
  for (const pattern of patterns) {
    const match = lowered.match(pattern);
    if (!match?.[1]) continue;
    const raw = match[1].toLowerCase();
    if (["there", "everyone", "all", "guys", "team"].includes(raw)) continue;
    return raw.charAt(0).toUpperCase() + raw.slice(1);
  }
  return null;
}

export function containsWakePhrase(transcript: string): boolean {
  return transcript.toLowerCase().includes(WAKE_PHRASE);
}
