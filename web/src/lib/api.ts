import type {
  DashboardSummary,
  PreMeetConnection,
  RoutingDecision,
} from "../types";

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
  dashboard: () => request<DashboardSummary>("/api/v1/dashboard"),
  connect: () => request<{ status: string }>("/api/v1/connect", { method: "POST", body: "{}" }),
  listEvents: () => request<import("../types").DetectedEvent[]>("/api/v1/events"),
  getEvent: (id: string) => request<import("../types").DetectedEvent>(`/api/v1/events/${id}`),
  runPremeet: (
    eventId: string,
    manualAttendees: Record<string, unknown>[] = [],
    topN = 10,
  ) =>
    request<{ ranked_leads: PreMeetConnection[] }>(`/api/v1/events/${eventId}/premeet`, {
      method: "POST",
      body: JSON.stringify({ manual_attendees: manualAttendees, top_n: topN }),
    }),
  eventLeads: (eventId: string) =>
    request<PreMeetConnection[]>(`/api/v1/events/${eventId}/leads`),
  listConnections: () => request<PreMeetConnection[]>("/api/v1/connections"),
  getConnection: (id: string) =>
    request<{
      connection: PreMeetConnection;
      warmth: import("../types").WarmthScore | null;
      gmail_draft?: Record<string, unknown>;
    }>(`/api/v1/connections/${id}`),
  processSignal: (body: Record<string, unknown>) =>
    request<RoutingDecision & { gmail_draft?: Record<string, unknown>; scores?: Record<string, unknown> }>(
      "/api/v1/meet/signals",
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    ),
  sendFollowup: (connectionId: string, body: Record<string, unknown>) =>
    request<Record<string, unknown>>(`/api/v1/connections/${connectionId}/followup`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
