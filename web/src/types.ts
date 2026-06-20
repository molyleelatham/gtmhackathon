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
  research_notes?: string[];
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

export interface Lead {
  id: string;
  contact_name?: string | null;
  contact_email?: string | null;
  company_name: string;
  company_domain?: string | null;
  company_size?: number | null;
  arr_usd?: number | null;
  funding_stage?: string | null;
  icp_score: number;
  signal_source: string;
  tags: string[];
  created_at?: string;
  updated_at?: string;
}

export interface MeetResult {
  signal_id?: string;
  routed_to?: string;
  narrative?: string | null;
  gmail_draft?: Record<string, unknown> | null;
  outreach_sequence?: Record<string, unknown> | null;
  recorded_at?: string | null;
  interests?: string[];
  relations?: { subject: string; predicate: string; object: string }[];
  knowledge_graph?: KnowledgeGraphPerson[];
}

export interface KnowledgeGraphPerson {
  speaker_id?: number;
  name?: string | null;
  company?: string | null;
  role?: string | null;
  communication_style?: string[];
  values?: string[];
  topic_weights?: Record<string, number>;
  learnings?: string[];
  pain_points?: { topic: string; intensity: number }[];
}

export interface AttendeeMatchResult {
  matched: boolean;
  name?: string;
  message: string;
  score?: number;
  matched_on?: string[];
  connection?: {
    id?: string;
    name?: string | null;
    title?: string | null;
    company_name?: string | null;
    predicted_warmth?: number;
    icp_score?: number;
  };
  interests?: string[];
  knowledge_graph?: KnowledgeGraphPerson[];
}

export interface ConnectionDetailResponse {
  connection: PreMeetConnection;
  warmth: WarmthScore | null;
  meet_result?: MeetResult | null;
  gmail_draft?: Record<string, unknown> | null;
  error?: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  listener_running: boolean;
}

export interface ConnectResult {
  status?: string;
  events_detected?: number;
  discovery_error?: string;
  [key: string]: unknown;
}

export interface CommunityMember {
  user_id: string;
  name: string;
  interests: string[];
}

export interface IcpProfileRow {
  label: string;
  value: string;
}

export interface ConferenceAttendeeInput {
  name?: string;
  email?: string;
  title?: string;
  company?: string;
  company_domain?: string;
  linkedin?: string;
  interests?: string[];
  source?: string;
}

export interface ConferenceRunRequest {
  conference_name: string;
  directory_url?: string;
  manual_attendees?: ConferenceAttendeeInput[];
  top_n?: number;
  book_meetings?: boolean;
  meeting_start_iso?: string;
  meeting_duration_minutes?: number;
  skip_scraping?: boolean;
  skip_research?: boolean;
  skip_email_drafts?: boolean;
  skip_zero_sync?: boolean;
  skip_hubspot_sync?: boolean;
}

export interface ConferenceRun {
  run_id: string;
  status: "running" | "complete" | "error" | "not_found";
  conference: string;
  started_at: string;
  completed_at?: string | null;
  summary?: Record<string, unknown> | null;
  error?: string | null;
}

export interface MeetTurn {
  speaker: number;
  text: string;
}

export interface MeetSpeakerAttr {
  name?: string;
  company?: string;
  role?: string;
}

export interface MeetEncodeRequest {
  turns: MeetTurn[];
  self_speaker_id?: number;
  speaker_attrs?: Record<number, MeetSpeakerAttr>;
  event_id?: string;
  connection_id?: string;
  use_agent?: boolean;
}

export interface MeetEncodeResponse {
  engine: string;
  signal: Record<string, unknown>;
  people: Record<string, unknown>[];
}

export interface MeetProcessResponse {
  decision?: RoutingDecision;
  routed_to?: string;
  narrative?: string;
  gmail_draft?: Record<string, unknown>;
  outreach_sequence?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface MeetingSignalInput {
  event_id?: string;
  connection_id?: string;
  name?: string;
  company?: string;
  role?: string;
  origin?: string;
  interests?: string[];
  background?: string;
  topic_time?: { topic: string; seconds?: number }[];
  most_time_topic?: string;
  what_you_learned?: string[];
  most_interesting?: string;
  transcript_excerpt?: string;
}

export interface CapturedSignalInput {
  session_id: string;
  transcript_excerpt: string;
  icp_keyword_score?: number;
  person_name?: string;
  company?: string;
  connection_id?: string;
  event_id?: string;
}

export interface SignalIngestResult {
  status: string;
  reason?: string;
  connection_id?: string;
  [key: string]: unknown;
}
