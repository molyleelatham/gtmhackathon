import type {
  AttendeeMatchResult,
  CapturedSignalInput,
  CommunityMember,
  ConferenceRun,
  ConferenceRunRequest,
  ConnectResult,
  ConnectionDetailResponse,
  DashboardSummary,
  DetectedEvent,
  HealthStatus,
  IcpProfileRow,
  Lead,
  MeetEncodeRequest,
  MeetEncodeResponse,
  MeetProcessResponse,
  MeetingSignalInput,
  PreMeetConnection,
  RoutingDecision,
  SignalIngestResult,
} from "../types";
import type { DashboardRoster } from "./adapters";
import type { Integration } from "./uiTypes";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // --- Health & onboarding ---
  health: () => request<HealthStatus>("/health"),
  connect: (userId = "demo-user") =>
    request<ConnectResult>("/api/v1/connect", {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    }),

  // --- Dashboard data ---
  dashboard: () => request<DashboardSummary>("/api/v1/dashboard"),
  dashboardRoster: () => request<DashboardRoster>("/api/v1/dashboard/roster"),
  icpProfile: () => request<IcpProfileRow[]>("/api/v1/icp"),
  integrations: () => request<Integration[]>("/api/v1/integrations"),

  // --- Events & pre-meet ---
  listEvents: () => request<DetectedEvent[]>("/api/v1/events"),
  getEvent: (id: string) => request<DetectedEvent>(`/api/v1/events/${id}`),
  runPremeet: (
    eventId: string,
    manualAttendees: Record<string, unknown>[] = [],
    topN = 10,
  ) =>
    request<{ event_id: string; ranked_leads: PreMeetConnection[] }>(
      `/api/v1/events/${eventId}/premeet`,
      {
        method: "POST",
        body: JSON.stringify({ manual_attendees: manualAttendees, top_n: topN }),
      },
    ),
  eventLeads: (eventId: string) =>
    request<PreMeetConnection[]>(`/api/v1/events/${eventId}/leads`),

  // --- Connections & leads ---
  listConnections: () => request<PreMeetConnection[]>("/api/v1/connections"),
  getConnection: (id: string) =>
    request<ConnectionDetailResponse>(`/api/v1/connections/${id}`),
  listLeads: () => request<Lead[]>("/api/v1/leads"),

  // --- Meet stage ---
  encodeMeet: (body: MeetEncodeRequest) =>
    request<MeetEncodeResponse>("/api/v1/meet/encode", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  processMeet: (body: MeetEncodeRequest) =>
    request<MeetProcessResponse>("/api/v1/meet/process", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  processSignal: (body: MeetingSignalInput) =>
    request<MeetProcessResponse & RoutingDecision>(
      "/api/v1/meet/signals",
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    ),

  // --- Post-meet ---
  sendFollowup: (connectionId: string, body: Record<string, unknown>) =>
    request<Record<string, unknown>>(`/api/v1/connections/${connectionId}/followup`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // --- Community ---
  communityMembers: () => request<CommunityMember[]>("/api/v1/community/members"),

  // --- Conference pipeline ---
  listConferenceRuns: () => request<ConferenceRun[]>("/api/v1/conferences/"),
  getConferenceRun: (runId: string) =>
    request<ConferenceRun>(`/api/v1/conferences/${runId}`),
  runConferencePipeline: (body: ConferenceRunRequest) =>
    request<ConferenceRun>("/api/v1/conferences/run", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // --- iOS signal ingress (CapturedSignal shape) ---
  ingestCapturedSignal: (body: CapturedSignalInput) =>
    request<SignalIngestResult>("/api/signals", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  matchAttendee: (body: { name: string; company?: string; transcript?: string }) =>
    request<AttendeeMatchResult>("/api/v1/match/attendee", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
