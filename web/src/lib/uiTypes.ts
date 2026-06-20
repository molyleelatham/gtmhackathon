/** UI-only types and helpers (not persisted on the backend). */

export type ICPBand = "hot" | "warm" | "cold";
export type SignalType = "hiring" | "funding" | "intent";

export interface Attendee {
  id: string;
  name: string;
  title: string;
  company: string;
  industry: string;
  icpScore: number;
  interests: string[];
  signal: string;
}

export interface MetPerson {
  id: string;
  name: string;
  company: string;
  role: string;
  origin?: string;
  score: number;
  interests: string[];
  genuineInterests?: string[];
  background?: string;
  whatYouLearned?: string[];
  mostInteresting?: string;
  topics?: string[];
  painPoints?: string[];
  goals?: string[];
  conversationExcerpt?: string;
  conversationTranscript?: string;
  metAt: string;
}

export interface Signal {
  id: string;
  company: string;
  type: SignalType;
  desc: string;
  time: string;
}

export type IntegrationStatus = "connected" | "pending" | "offline";

export interface Integration {
  name: string;
  status: IntegrationStatus;
}

export function bandFor(score: number): ICPBand {
  if (score >= 80) return "hot";
  if (score >= 55) return "warm";
  return "cold";
}
