import { describe, expect, it } from "vitest";
import { connectionToAttendee } from "./adapters";
import type { PreMeetConnection } from "../types";

const sampleConn: PreMeetConnection = {
  id: "conn_1",
  event_id: "evt_1",
  name: "Maya Chen",
  title: "VP RevOps",
  company_name: "NorthWind",
  industry: "SaaS",
  icp_score: 88,
  predicted_warmth: 82,
  intent_score: 70,
  interests: ["RevOps", "attribution"],
  research_notes: ["Series B fintech rebuilding attribution"],
  status: "scored",
};

describe("adapters", () => {
  it("maps connection to attendee card fields", () => {
    const attendee = connectionToAttendee(sampleConn);
    expect(attendee.name).toBe("Maya Chen");
    expect(attendee.company).toBe("NorthWind");
    expect(attendee.icpScore).toBe(88);
    expect(attendee.interests).toContain("RevOps");
  });
});
