export type LifecycleStage = "before_meet" | "meet" | "post_meet";
export type WarmthBand = "cold" | "warm" | "hot";

export interface DetectedEvent {
  id: string;
  user_id: string;
  name: string;
  event_type: string;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  confidence: number;
  stage: LifecycleStage;
  attendee_count: number;
  premeet_completed: boolean;
}

export interface PreMeetConnection {
  id: string;
  event_id: string;
  name?: string | null;
  email?: string | null;
  title?: string | null;
  company_name?: string | null;
  company_size?: number | null;
  industry?: string | null;
  funding_stage?: string | null;
  interests: string[];
  icp_score: number;
  predicted_warmth: number;
  intent_score: number;
  draft_subject?: string | null;
  draft_body?: string | null;
  status: string;
  source: string;
}

export interface WarmthScore {
  icp_score: number;
  warmth_score: number;
  predicted_score?: number | null;
  actual_score?: number | null;
  band: WarmthBand;
}

export interface DashboardSummary {
  user_id: string;
  events: number;
  connections: number;
  hot_leads: number;
  leads_in_crm: number;
  upcoming_events: DetectedEvent[];
  top_leads: PreMeetConnection[];
}

export interface RoutingDecision {
  target: "crm_and_outreach" | "founder_community";
  reason: string;
  uplift?: number | null;
  cluster_id?: number | null;
  warmth?: WarmthScore | null;
  matched_candidates: { user_id?: string; name?: string; interests?: string[] }[];
}
