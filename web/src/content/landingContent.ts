export type DemoVideoType = "firebase" | "youtube";

export interface LandingMoment {
  src: string;
  alt: string;
  caption: string;
}

export interface TeamMember {
  name: string;
  title: string;
  photo: string;
  linkedin: string;
  website?: string;
  bio: string;
}

export const landingContent = {
  awards: {
    cursorTrack: "3rd Overall — Cursor Top 3",
    cursorDetail: "3 months Cursor Ultra per teammate",
    zeroCRM: "2nd Place — Best Use of Zero CRM",
    zeroDetail: "Zero tech partner challenge",
  },
  hero: {
    headline: "Never forget a conversation.",
    subheadline:
      "Warmth turns chaotic event networking into structured, scored, and actionable GTM intelligence — in real time.",
    builtIn: "Built in one day",
    event: "GTM Hackathon London · 20 June 2026",
    venue: "The Building Centre",
    availability: {
      web: {
        label: "Available on web",
        cta: "See it live",
      },
      ios: {
        label: "iOS app",
      },
    },
  },
  hackathon: {
    title: "The hackathon",
    pitch:
      "One day where builders, operators, and GTM engineers ship real go-to-market results — not a project that gathers dust, but distribution you can feel.",
    hosts: ["Lightfern", "Cursor"],
    track: "Lightfern Main Track",
    trackNote:
      "We worked the real GTM case from Lightfern — turning live event conversations into scored, routed GTM intelligence.",
    venue: "The Building Centre, London",
    schedule: "Saturday 20 June · 9:30 – 20:00",
    timeline: [
      { time: "11:00", label: "Hacking started" },
      { time: "17:30", label: "Submitted our walkthrough" },
      { time: "18:30", label: "Prize ceremony" },
    ],
    stackNote: "Built on the required partner stack:",
    stack: ["UnifyGTM", "Zero CRM", "Cursor", "Lightfern", "Gmail"],
  },
  ask: {
    title: "The problem we solved",
    body: "Startups don't fail at building product — they fail at turning attention into customers. On the event floor you meet dozens of people; names blur, notes never get typed, follow-ups slip. Most tools help after you're back at your desk — half the context is already gone. We had under 12 hours to capture signal in the room and turn it into real GTM action.",
  },
  surfaces: [
    {
      title: "iOS + Apple Watch",
      description:
        "Phrase trigger or one tap. On-device speech and NLP extract names, companies, and pain points on the event floor.",
      icon: "📱",
    },
    {
      title: "Web Dashboard",
      description:
        "Review events, warmth scores, ICP fit, connections, and follow-ups before and after every event.",
      icon: "◫",
    },
    {
      title: "Python Backend",
      description:
        "ML scoring pipeline, CRM routing, Gmail draft generation — always-on intelligence behind every capture.",
      icon: "⚡",
    },
  ],
  lifecycle: [
    {
      step: "Onboarding",
      description: "Connect Google Calendar + Gmail. Warmth detects events and seeds the lifecycle automatically.",
    },
    {
      step: "Before Meet",
      description:
        "Enrich attendees via UnifyGTM, score ICP via Zero CRM, draft pre-meet outreach via Lightfern.",
    },
    {
      step: "Meet",
      description:
        "Say the phrase or tap record. On-device NLP builds a person model; the backend routes in real time.",
    },
    {
      step: "Post Meet",
      description:
        "Gmail draft lands in your inbox. Lightfern polishes. You review and send — loop closed.",
    },
  ],
  differentiator: {
    title: "Warmth ≠ ICP",
    body: "Two independent scores: ICP fit from Zero CRM, and relationship warmth from our ML. A perfect ICP can be cold; a warm non-ICP routes to your founder community. Uplift drives the decision.",
  },
  integrations: [
    { name: "Zero CRM", logo: null },
    { name: "Lightfern", logo: "/logos/lightfern.png" },
    { name: "Gmail", logo: "/logos/gmail.png" },
    { name: "UnifyGTM", logo: null },
    { name: "Google MCP", logo: null },
    { name: "Cursor", logo: null },
  ],
  moments: [
    {
      src: "/landing/moments/winning-team-presentation.png",
      alt: "Team presenting Warmth on stage",
      caption: "Presenting Warmth live on stage",
    },
    {
      src: "/landing/moments/team-selfie-building-centre.png",
      alt: "Team celebration selfie at The Building Centre",
      caption: "Celebrating at The Building Centre",
    },
  ] satisfies LandingMoment[],
  demoVideo:
    import.meta.env.VITE_DEMO_VIDEO_URL ??
    "https://storage.googleapis.com/warmth-gtm-hackathon-landing/landing/demo.mp4",
  demoVideoType: (import.meta.env.VITE_DEMO_VIDEO_TYPE ?? "firebase") as DemoVideoType,
  team: [
    {
      name: "Moly Leelatham",
      title: "Marketing Analytics @ CLARK · UK & DACH · InsurTech",
      photo: "/landing/team/moly-leelatham.png",
      linkedin: "https://www.linkedin.com/in/moly-leelatham/",
      website: "https://molyleelatham.com",
      bio: "Marketing Analyst with a focus on computational marketing — combining data analytics, ML, and applied agentic AI. 2× hackathon winner (Google Cloud & Cursor). Double degree graduate: Economics and Management BSc at the University of Bristol and Economics BA (EBA) at Chulalongkorn University. Former Director of a social enterprise. Passionate about initiatives that push boundaries and redefine possibilities.",
    },
    {
      name: "Nicholas Wong",
      title: "Chemistry & Engineering @ Imperial · First-Class BSc · Deloitte Summer Analyst",
      photo: "/landing/team/nicholas-wong.png",
      linkedin: "https://www.linkedin.com/in/nicholasyswong/",
      bio: "Completing a Master's in Chemistry and Engineering at Imperial College London, with First-Class Honours in Chemistry from Bristol. Academic work from pharmaceutical catalysts to Nobel Prize–rooted reaction systems. At Deloitte, contributed to payroll consulting and tech advisory; at DB Schenker Singapore, built cost and carbon models for packaging; through 180 Degrees Consulting, led student teams advising charities on fundraising.",
    },
    {
      name: "Dzak Dzulzalani",
      title: "IBM Offerings & Growth · Hybrid Cloud & Data · Ex Eli Lilly",
      photo: "/landing/team/dzak-dzulzalani.png",
      linkedin: "https://www.linkedin.com/in/dzakdzulzalani/",
      bio: "BSc Computing & IT at the University of Surrey and Sarawak Energy Berhad Scholarship Recipient. Excels in public speaking, graphic design, and video editing. Former bakery owner turned technologist. Public Relations Executive for Tutors in Action (Malaysia). Volunteer with WormingUp at Rainforest World Music Festival — passionate about technology for positive social impact.",
    },
  ] satisfies TeamMember[],
  testFlight: {
    label: "iOS on TestFlight — coming soon",
  },
  explore: {
    title: "Ready to explore?",
    subtitle: "Try Warmth on the web today — the native iOS app is on the way.",
    web: {
      title: "Web app",
      description:
        "Review events, warmth scores, ICP fit, connections, and follow-ups in your browser.",
      cta: "Open the app",
    },
    ios: {
      title: "iOS app",
      description:
        "Capture conversations on the event floor with phrase trigger, on-device NLP, and Apple Watch.",
      cta: "Coming soon",
    },
  },
  links: {
    app: "/sign-in",
    hackathon: "https://gtmengineer.dev",
  },
} as const;
