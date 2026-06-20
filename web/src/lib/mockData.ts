import type {
  DashboardSummary,
  DetectedEvent,
  PreMeetConnection,
  RoutingDecision,
  WarmthScore,
} from "../types";

export type ICPBand = "hot" | "warm" | "cold";
export type SignalType = "hiring" | "funding" | "intent";
export type PermissionLevel = "read" | "comment" | "edit" | "admin";

export interface Lead {
  id: string;
  name: string;
  company: string;
  band: ICPBand;
  score: number;
  insight: string;
  topics: string[];
  metAt: string;
}

export interface Followup {
  leadId: string;
  insight: string;
  priority: number;
}

export interface Signal {
  id: string;
  company: string;
  type: SignalType;
  desc: string;
  time: string;
}

export interface Integration {
  name: string;
  status: "connected" | "pending" | "offline";
}

export interface CommunityGroup {
  id: string;
  name: string;
  members: number;
  permission: PermissionLevel;
  sharedLeads: number;
}

export const LEADS: Lead[] = [
  {
    id: "1",
    name: "Sarah Mitchell",
    company: "RevLoop",
    band: "hot",
    score: 92,
    insight: "Scaling RevOps team post-Series B; pain around pipeline attribution.",
    topics: ["RevOps", "PLG", "Expansion"],
    metAt: "11:42 AM · Hall B",
  },
  {
    id: "2",
    name: "James Okonkwo",
    company: "Stackframe",
    band: "hot",
    score: 88,
    insight: "Evaluating CRM enrichment tools before Q3 board review.",
    topics: ["DevTools", "CRM", "Data"],
    metAt: "10:15 AM · Coffee bar",
  },
  {
    id: "3",
    name: "Priya Sharma",
    company: "Ledgerly",
    band: "warm",
    score: 71,
    insight: "Interested in conference intel sharing with her co-founder network.",
    topics: ["Fintech", "Community"],
    metAt: "9:50 AM · Pavilion booth",
  },
  {
    id: "4",
    name: "Marcus Webb",
    company: "Northstar SaaS",
    band: "hot",
    score: 85,
    insight: "Needs faster follow-up after back-to-back meetings.",
    topics: ["Founder-led sales", "Events"],
    metAt: "11:05 AM · Main stage",
  },
  {
    id: "5",
    name: "Elena Vasquez",
    company: "Cloudmint",
    band: "warm",
    score: 68,
    insight: "Uses HubSpot; asked about auto-drafting post-event emails.",
    topics: ["HubSpot", "Email automation"],
    metAt: "8:30 AM · Registration",
  },
  {
    id: "6",
    name: "Tom Berger",
    company: "Dataweave",
    band: "cold",
    score: 41,
    insight: "Early-stage, no budget this quarter but open to an intro call.",
    topics: ["Analytics"],
    metAt: "12:10 PM · Lunch",
  },
  {
    id: "7",
    name: "Aisha Khan",
    company: "Payflow",
    band: "hot",
    score: 90,
    insight: "Hiring 3 AEs; wants tooling to prioritize booth conversations.",
    topics: ["Hiring", "Sales enablement"],
    metAt: "12:45 PM · Expo floor",
  },
];

export const FOLLOWUPS: Followup[] = [
  { leadId: "7", insight: "Hiring 3 AEs — send playbook on prioritizing booth leads.", priority: 1 },
  { leadId: "1", insight: "RevOps attribution pain — share case study + book demo.", priority: 2 },
  { leadId: "2", insight: "CRM enrichment eval — draft email with UnifyGTM angle.", priority: 3 },
  { leadId: "4", insight: "Wants faster follow-ups — offer Warmth walkthrough tonight.", priority: 4 },
  { leadId: "5", insight: "HubSpot user — send auto-draft email feature preview.", priority: 5 },
  { leadId: "3", insight: "Community sharing interest — invite to Founders Circle.", priority: 6 },
];

export const SIGNALS: Signal[] = [
  { id: "s1", company: "RevLoop", type: "funding", desc: "Closed $18M Series B — expanding GTM team.", time: "12 min ago" },
  { id: "s2", company: "Payflow", type: "hiring", desc: "Posted 3 AE roles in San Francisco.", time: "28 min ago" },
  { id: "s3", company: "Stackframe", type: "intent", desc: "CEO quoted on CRM data quality in SaaStr panel recap.", time: "45 min ago" },
  { id: "s4", company: "Ledgerly", type: "funding", desc: "Rumored seed extension — fintech press mention.", time: "1h ago" },
  { id: "s5", company: "Northstar SaaS", type: "intent", desc: "Blog post on event ROI measurement published today.", time: "1h ago" },
  { id: "s6", company: "Cloudmint", type: "hiring", desc: "RevOps manager role listed on LinkedIn.", time: "2h ago" },
];

export const INTEGRATIONS: Integration[] = [
  { name: "Deepgram", status: "connected" },
  { name: "Zero CRM", status: "connected" },
  { name: "UnifyGTM", status: "connected" },
  { name: "Google MCP", status: "pending" },
  { name: "Tavily", status: "connected" },
];

export const COMMUNITY_GROUPS: CommunityGroup[] = [
  { id: "g1", name: "Founders Circle", members: 8, permission: "admin", sharedLeads: 12 },
  { id: "g2", name: "Core Team", members: 5, permission: "edit", sharedLeads: 6 },
  { id: "g3", name: "Conference Friends", members: 14, permission: "read", sharedLeads: 3 },
];

export const ICP_PROFILE: { label: string; value: string }[] = [
  { label: "Company size", value: "50–500 employees" },
  { label: "ARR", value: "$2M – $20M" },
  { label: "Industries", value: "B2B SaaS, Fintech, DevTools" },
  { label: "Tech stack", value: "Salesforce, HubSpot, Snowflake" },
  { label: "Keywords", value: "PLG, expansion, RevOps" },
];

export function bandFor(score: number): ICPBand {
  if (score >= 80) return "hot";
  if (score >= 55) return "warm";
  return "cold";
}

// ---- Attending tab: everyone at the conference, ranked by ICP -------------

export interface Attendee {
  id: string;
  name: string;
  title: string;
  company: string;
  industry: string;
  icpScore: number;
  interests: string[];
  /** Why this person matters to your work (the "signal"). */
  signal: string;
}

export const ATTENDEES: Attendee[] = [
  { id: "a1", name: "Sarah Mitchell", title: "VP RevOps", company: "RevLoop", industry: "B2B SaaS", icpScore: 96, interests: ["RevOps", "PLG", "Attribution"], signal: "Just closed Series B — scaling GTM team now." },
  { id: "a2", name: "Aisha Khan", title: "Head of Sales", company: "Payflow", industry: "Fintech", icpScore: 93, interests: ["Hiring", "Sales enablement"], signal: "Hiring 3 AEs — active tooling budget." },
  { id: "a3", name: "James Okonkwo", title: "Founder & CEO", company: "Stackframe", industry: "DevTools", icpScore: 90, interests: ["CRM", "Data quality"], signal: "Evaluating enrichment tools before Q3 board review." },
  { id: "a4", name: "Marcus Webb", title: "Co-founder", company: "Northstar SaaS", industry: "B2B SaaS", icpScore: 86, interests: ["Founder-led sales", "Events"], signal: "Published a post on event ROI today." },
  { id: "a5", name: "Lena Fischer", title: "CRO", company: "Bright Funnel", industry: "MarTech", icpScore: 84, interests: ["Pipeline", "Forecasting"], signal: "Quoted on a SaaStr panel about pipeline gaps." },
  { id: "a6", name: "Diego Alvarez", title: "VP Marketing", company: "Cohorted", industry: "B2B SaaS", icpScore: 81, interests: ["Demand gen", "ABM"], signal: "Running an ABM revamp this quarter." },
  { id: "a7", name: "Priya Sharma", title: "Co-founder", company: "Ledgerly", industry: "Fintech", icpScore: 74, interests: ["Fintech", "Community"], signal: "Wants to share conference intel with her network." },
  { id: "a8", name: "Elena Vasquez", title: "Head of Growth", company: "Cloudmint", industry: "B2B SaaS", icpScore: 69, interests: ["HubSpot", "Email automation"], signal: "HubSpot user — asked about auto-drafting follow-ups." },
  { id: "a9", name: "Tom Berger", title: "Founder", company: "Dataweave", industry: "Analytics", icpScore: 64, interests: ["Analytics"], signal: "Early-stage; open to an intro call." },
  { id: "a10", name: "Hannah Lee", title: "Sales Director", company: "Quotient", industry: "B2B SaaS", icpScore: 62, interests: ["Outbound", "Sequences"], signal: "Rebuilding outbound motion." },
  { id: "a11", name: "Owen Patel", title: "VP Product", company: "Gridline", industry: "DevTools", icpScore: 58, interests: ["Product-led", "Onboarding"], signal: "Curious about signal-based prioritization." },
  { id: "a12", name: "Maya Rossi", title: "Head of Partnerships", company: "Stitchwork", industry: "MarTech", icpScore: 55, interests: ["Partnerships", "Ecosystem"], signal: "Exploring co-marketing partners." },
  { id: "a13", name: "Carlos Mendez", title: "Founder", company: "Pulsegrid", industry: "Fintech", icpScore: 51, interests: ["Payments"], signal: "Pre-seed; networking widely." },
  { id: "a14", name: "Nina Brandt", title: "RevOps Manager", company: "Vela", industry: "B2B SaaS", icpScore: 48, interests: ["Ops", "Tooling"], signal: "Evaluating CRM add-ons." },
  { id: "a15", name: "Sam Rivera", title: "RevOps Lead", company: "Glide", industry: "B2B SaaS", icpScore: 46, interests: ["RevOps", "Attribution"], signal: "Met briefly last year." },
  { id: "a16", name: "Ivy Chen", title: "Growth PM", company: "Lumen", industry: "DevTools", icpScore: 43, interests: ["Activation"], signal: "Researching the space." },
  { id: "a17", name: "Felix Wood", title: "AE", company: "Cordial", industry: "MarTech", icpScore: 39, interests: ["Sales"], signal: "Individual contributor — low buying power." },
  { id: "a18", name: "Grace Okafor", title: "Analyst", company: "Northwind", industry: "Analytics", icpScore: 34, interests: ["BI"], signal: "Student / early career." },
];

// ---- Met tab: people you've actually met today ----------------------------

export interface MetPerson {
  id: string;
  name: string;
  company: string;
  role: string;
  origin?: string;
  score: number;
  interests: string[];
  /** Personal passions outside work e.g. biotech, climbing */
  genuineInterests?: string[];
  background?: string;
  whatYouLearned: string[];
  mostInteresting?: string;
  topics: string[];
  painPoints?: string[];
  goals?: string[];
  conversationExcerpt?: string;
  metAt: string;
}

export const MET_PEOPLE: MetPerson[] = [
  {
    id: "m1",
    name: "Sarah Mitchell",
    company: "RevLoop",
    role: "VP RevOps",
    origin: "San Francisco",
    score: 94,
    interests: ["RevOps", "PLG", "Attribution"],
    genuineInterests: ["Biotech investing", "Trail running", "Climate tech"],
    background: "Built RevOps at two unicorns before RevLoop. Engineer-turned-operator.",
    whatYouLearned: [
      "Just closed an $18M Series B, hiring 4 on GTM.",
      "Biggest pain is multi-touch pipeline attribution.",
      "Wants a demo the week after the conference.",
    ],
    mostInteresting: "They're consolidating 3 tools into one and have budget approved for Q3.",
    topics: ["pipeline", "attribution", "team scaling"],
    painPoints: ["Fragmented attribution across 3 tools", "Manual follow-up after events"],
    goals: ["Unify GTM stack by Q3", "Cut time-to-follow-up from days to hours"],
    conversationExcerpt:
      "We're drowning in spreadsheets after every conference — I need something that just tells me who to email first.",
    metAt: "11:42 AM · Hall B",
  },
  {
    id: "m2",
    name: "James Okonkwo",
    company: "Stackframe",
    role: "Founder & CEO",
    origin: "London",
    score: 88,
    interests: ["DevTools", "CRM", "Data quality"],
    genuineInterests: ["Open source", "Afrobeats", "Angel investing"],
    background: "Second-time founder; sold his last company to a public devtools firm.",
    whatYouLearned: [
      "Evaluating CRM enrichment tools before a Q3 board review.",
      "Frustrated with stale contact data.",
    ],
    mostInteresting: "Already shortlisted two vendors — we'd be a late but strong entrant.",
    topics: ["enrichment", "data quality", "board prep"],
    painPoints: ["Stale CRM data", "No signal layer on top of calendar"],
    goals: ["Pick enrichment vendor by August"],
    conversationExcerpt: "Our CRM is only as good as what we put in at conferences — and we put in nothing.",
    metAt: "10:15 AM · Coffee bar",
  },
  {
    id: "m3",
    name: "Priya Sharma",
    company: "Ledgerly",
    role: "Co-founder",
    origin: "Bangalore",
    score: 71,
    interests: ["Fintech", "Community"],
    genuineInterests: ["Biotech", "Founder communities", "South Asian startup ecosystem"],
    background: "Ex-Stripe. Runs a 200-person fintech founder Slack.",
    whatYouLearned: [
      "Keen to share conference intelligence with her co-founder network.",
      "Less interested in buying, more in community.",
    ],
    mostInteresting: "Could be a great community channel rather than a direct lead.",
    topics: ["community", "fintech", "networking"],
    metAt: "9:50 AM · Pavilion booth",
  },
  {
    id: "m4",
    name: "Elena Vasquez",
    company: "Cloudmint",
    role: "Head of Growth",
    origin: "Austin",
    score: 68,
    interests: ["HubSpot", "Email automation"],
    background: "Growth leader scaling a PLG motion on HubSpot.",
    whatYouLearned: [
      "Asked specifically about auto-drafting post-event emails.",
      "Team of 6, moving fast.",
    ],
    mostInteresting: "The auto-draft feature was the exact hook she lit up on.",
    topics: ["email automation", "HubSpot", "PLG"],
    metAt: "8:30 AM · Registration",
  },
];

// ---- Adapters so the existing team pages keep rendering -------------------

function leadToConnection(lead: Lead): PreMeetConnection {
  return {
    id: lead.id,
    event_id: "evt-saastr",
    name: lead.name,
    email: `${lead.name.split(" ")[0].toLowerCase()}@${lead.company.toLowerCase().replace(/\s+/g, "")}.com`,
    title: lead.topics[0] ?? null,
    company_name: lead.company,
    company_size: 120,
    industry: lead.topics[0] ?? null,
    funding_stage: lead.band === "hot" ? "Series B" : "Seed",
    interests: lead.topics,
    icp_score: lead.score,
    predicted_warmth: lead.score,
    intent_score: Math.max(20, lead.score - 10),
    draft_subject: `Following up from SaaStr — ${lead.company}`,
    draft_body: `Hi ${lead.name.split(" ")[0]},\n\nGreat chatting at the conference. ${lead.insight}\n\nWould love to continue the conversation.\n\nBest,\nAlex`,
    status: "enriched",
    source: "conference",
  };
}

export const CONNECTIONS: PreMeetConnection[] = LEADS.map(leadToConnection);

export const EVENTS: DetectedEvent[] = [
  {
    id: "evt-saastr",
    user_id: "demo",
    name: "SaaStr Annual",
    event_type: "conference",
    location: "San Francisco, CA",
    start_date: "2026-06-19",
    end_date: "2026-06-21",
    confidence: 0.96,
    stage: "meet",
    attendee_count: 12,
    premeet_completed: true,
  },
  {
    id: "evt-pavilion",
    user_id: "demo",
    name: "Pavilion CRO Summit",
    event_type: "conference",
    location: "Austin, TX",
    start_date: "2026-07-12",
    end_date: "2026-07-13",
    confidence: 0.82,
    stage: "before_meet",
    attendee_count: 0,
    premeet_completed: false,
  },
];

export const DASHBOARD_SUMMARY: DashboardSummary = {
  user_id: "demo",
  events: EVENTS.length,
  connections: LEADS.length,
  hot_leads: LEADS.filter((l) => l.band === "hot").length,
  leads_in_crm: 5,
  upcoming_events: EVENTS,
  top_leads: [...CONNECTIONS].sort((a, b) => b.predicted_warmth - a.predicted_warmth).slice(0, 5),
};

export function warmthFor(score: number): WarmthScore {
  const band = bandFor(score);
  return { icp_score: score, warmth_score: score, predicted_score: score, actual_score: null, band };
}

export function routingFor(conn: PreMeetConnection): RoutingDecision {
  const community = conn.predicted_warmth < 60;
  return {
    target: community ? "founder_community" : "crm_and_outreach",
    reason: community
      ? "Below outreach threshold — better fit for the founder community."
      : "Strong ICP + intent — route to CRM and personalized outreach.",
    uplift: community ? null : 12.5,
    cluster_id: 2,
    warmth: warmthFor(conn.predicted_warmth),
    matched_candidates: [{ name: "Priya Sharma", interests: ["Fintech", "Community"] }],
  };
}
