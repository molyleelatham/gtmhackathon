import type { PreMeetConnection } from "../types";
import type { Attendee, MetPerson, Signal, SignalType } from "./uiTypes";

export interface MeetResultPayload {
  signal_id?: string;
  routed_to?: string;
  narrative?: string | null;
  gmail_draft?: Record<string, unknown> | null;
  outreach_sequence?: Record<string, unknown> | null;
  recorded_at?: string | null;
  interests?: string[];
  relations?: { subject: string; predicate: string; object: string }[];
  knowledge_graph?: import("../types").KnowledgeGraphPerson[];
}

export interface DashboardRosterMetRow {
  connection: PreMeetConnection;
  meet_result: MeetResultPayload;
}

export interface DashboardRoster {
  event: {
    id: string;
    name: string;
    location?: string | null;
    stage?: string;
  } | null;
  attendees: PreMeetConnection[];
  met: DashboardRosterMetRow[];
  signals: unknown[];
}

function formatMetTime(iso?: string | null): string {
  if (!iso) return "Today";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "Today";
  return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function firstNote(conn: PreMeetConnection): string | undefined {
  const n = conn.research_notes;
  if (!n) return undefined;
  if (Array.isArray(n)) return n[0];
  return String(n);
}

function attendeeSignal(conn: PreMeetConnection): string {
  const note = firstNote(conn);
  if (note) return note.length > 100 ? `${note.slice(0, 100)}…` : note;
  if (conn.funding_stage && conn.industry) {
    return `${conn.funding_stage} · ${conn.industry}`;
  }
  if (conn.interests[0]) return conn.interests[0];
  return "On your event roster";
}

export function connectionToAttendee(conn: PreMeetConnection): Attendee {
  return {
    id: conn.id,
    name: conn.name ?? "Unknown",
    title: conn.title ?? "",
    company: conn.company_name ?? "—",
    industry: conn.industry ?? "",
    icpScore: Math.round(conn.icp_score),
    interests: conn.interests,
    signal: attendeeSignal(conn),
  };
}

export function connectionToMetPerson(
  conn: PreMeetConnection,
  meet?: MeetResultPayload | null,
): MetPerson {
  const narrative = meet?.narrative?.trim();
  const allInterests = mergeInterestLists(conn.interests, meet?.interests);
  const kg = meet?.knowledge_graph?.[0];
  const topicInterests = kg?.topic_weights
    ? Object.entries(kg.topic_weights)
        .sort((a, b) => b[1] - a[1])
        .map(([topic]) => topic)
    : [];
  const mergedInterests = mergeInterestLists(allInterests, topicInterests);
  const genuine = mergeInterestLists(kg?.values, kg?.communication_style);
  const note = firstNote(conn);
  const learned =
    narrative != null && narrative.length > 0
      ? [narrative]
      : note
        ? [note]
        : ["Met at the event — follow up while context is fresh."];

  return {
    id: conn.id,
    name: conn.name ?? "Unknown",
    company: conn.company_name ?? "—",
    role: conn.title ?? "",
    score: Math.round(conn.predicted_warmth),
    interests: mergedInterests,
    genuineInterests: genuine.length > 0 ? genuine : undefined,
    whatYouLearned: learned,
    mostInteresting: note ?? kg?.learnings?.[0] ?? narrative ?? undefined,
    topics: topicInterests.length > 0 ? topicInterests : mergedInterests,
    painPoints: kg?.pain_points?.map((p) => p.topic),
    conversationExcerpt: narrative ?? undefined,
    metAt: formatMetTime(meet?.recorded_at),
  };
}

function mergeInterestLists(...sources: (string[] | undefined)[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const source of sources) {
    for (const item of source ?? []) {
      const key = item.toLowerCase();
      if (!key || seen.has(key)) continue;
      seen.add(key);
      out.push(item);
    }
  }
  return out;
}

const SIGNAL_TYPES = new Set<SignalType>(["hiring", "funding", "intent"]);

export function normalizeSignals(raw: unknown[]): Signal[] {
  return raw
    .map((item) => {
      const row = item as Record<string, unknown>;
      const type = String(row.type ?? "intent");
      return {
        id: String(row.id ?? crypto.randomUUID()),
        company: String(row.company ?? "Unknown"),
        type: SIGNAL_TYPES.has(type as SignalType) ? (type as SignalType) : "intent",
        desc: String(row.desc ?? ""),
        time: String(row.time ?? "Today"),
      };
    })
    .filter((s) => s.desc.length > 0);
}

export function rosterToAttendees(roster: DashboardRoster): Attendee[] {
  return roster.attendees.map(connectionToAttendee);
}

export function rosterToMetPeople(roster: DashboardRoster): MetPerson[] {
  return roster.met.map(({ connection, meet_result }) =>
    connectionToMetPerson(connection, meet_result),
  );
}
