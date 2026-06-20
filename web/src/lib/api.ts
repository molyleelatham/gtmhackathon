import type {
  AttendeeMatchResult,
  CapturedSignalInput,
  CommunityMember,
  EventRun,
  EventRunRequest,
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

export interface UserProfile {
  uid: string;
  email: string | null;
  display_name: string | null;
  photo_url: string | null;
  demo_seeded?: boolean;
  created_at: string;
  updated_at: string;
}

type TokenGetter = () => Promise<string | null>;

let authTokenGetter: TokenGetter | null = null;

export function setAuthTokenGetter(getter: TokenGetter | null): void {
  authTokenGetter = getter;
}

async function authHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (authTokenGetter) {
    const token = await authTokenGetter();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { ...headers, ...(init?.headers ?? {}) },
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
  connect: () =>
    request<ConnectResult>("/api/v1/connect", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  getProfile: () => request<UserProfile>("/api/v1/users/me"),
  bootstrapProfile: () =>
    request<UserProfile>("/api/v1/users/bootstrap", { method: "POST" }),

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

  // --- Event pipeline ---
  listEventRuns: () => request<EventRun[]>("/api/v1/event-runs/"),
  getEventRun: (runId: string) =>
    request<EventRun>(`/api/v1/event-runs/${runId}`),
  runEventPipeline: (body: EventRunRequest) =>
    request<EventRun>("/api/v1/event-runs/run", {
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
