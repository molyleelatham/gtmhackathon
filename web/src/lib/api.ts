import type {
  DashboardSummary,
  DetectedEvent,
  PreMeetConnection,
  RoutingDecision,
  WarmthScore,
} from "../types";
import {
  CONNECTIONS,
  DASHBOARD_SUMMARY,
  EVENTS,
  routingFor,
  warmthFor,
} from "./mockData";

/**
 * Mock-backed API client.
 *
 * The real FastAPI backend (`apps/api`) is wired the same way, so swapping this
 * for `fetch(`${import.meta.env.VITE_API_BASE_URL}/...`)` later requires no
 * changes at the call sites. For this first draft everything resolves from the
 * in-memory mock data so the dashboard runs with zero backend/keys.
 */
function delay<T>(value: T, ms = 220): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export const api = {
  dashboard(): Promise<DashboardSummary> {
    return delay(DASHBOARD_SUMMARY);
  },

  connect(): Promise<{ ok: true }> {
    return delay({ ok: true });
  },

  listEvents(): Promise<DetectedEvent[]> {
    return delay(EVENTS);
  },

  getEvent(id: string): Promise<DetectedEvent> {
    const event = EVENTS.find((e) => e.id === id) ?? EVENTS[0];
    return delay(event);
  },

  eventLeads(eventId: string): Promise<PreMeetConnection[]> {
    return delay(CONNECTIONS.filter((c) => c.event_id === eventId));
  },

  runPremeet(_eventId: string, _attendees: unknown[]): Promise<{ ok: true }> {
    return delay({ ok: true }, 400);
  },

  listConnections(): Promise<PreMeetConnection[]> {
    return delay(CONNECTIONS);
  },

  getConnection(
    id: string,
  ): Promise<{ connection: PreMeetConnection; warmth: WarmthScore }> {
    const connection = CONNECTIONS.find((c) => c.id === id) ?? CONNECTIONS[0];
    return delay({ connection, warmth: warmthFor(connection.predicted_warmth) });
  },

  processSignal(payload: {
    connection_id: string;
    [key: string]: unknown;
  }): Promise<RoutingDecision> {
    const connection =
      CONNECTIONS.find((c) => c.id === payload.connection_id) ?? CONNECTIONS[0];
    return delay(routingFor(connection), 500);
  },

  sendFollowup(
    _connectionId: string,
    payload: { name?: string | null; company?: string | null; [key: string]: unknown },
  ): Promise<Record<string, unknown>> {
    return delay(
      {
        subject: `Great meeting you at SaaStr, ${payload.name ?? "there"}`,
        body: `Hi ${payload.name ?? "there"},\n\nReally enjoyed our chat${
          payload.company ? ` about ${payload.company}` : ""
        }. Here's the follow-up I promised — let's find time next week.\n\nBest,\nAlex`,
        status: "drafted",
      },
      450,
    );
  },
};
