
# Warmth — Demo Pitch Script
### GTM Hackathon · June 20, 2026

---

## Before you present

**Have open:**
- iPhone with Warmth app on the Capture screen (orb visible)
- `warmth_event_demo.xlsx` open on your laptop, on the **Summary** sheet
- Terminal with the API running (`make run-api` from `warmth/`)

**Timing:** ~3–4 minutes

---

## The Pitch

---

**"Every time you go to an event, you come home with the same problem."**

You met maybe 30 people. You remember 8. You follow up with 3. And the 3 you follow up with — you write basically the same email to all of them because you can't remember what made each conversation different.

That's not a discipline problem. That's a tooling problem. There's nothing capturing the signal in the room.

---

**"This is Warmth."**

*[hold up the phone — show the orb on Capture screen]*

I'm at an event. I walk up to someone. I say:

**"Hey, it's nice to meet you."**

That's it. Warmth hears the phrase, starts recording. Everything from here is automatic.

---

**"Let me show you what it captured today."**

*[switch to laptop — open Sheet 2: Live Conversations]*

Five conversations. All from this hackathon. Each one: who I met, what they said, what I learned, where their pain is.

Look at Anna — she runs RevOps at Acme. She told me in 90 seconds that her team spends more time cleaning CRM data than selling. She just found out HubSpot has AI forecasting but honestly doesn't care about features — she cares about accuracy.

I didn't write that down. Warmth extracted it, live, from the transcript. On-device. No cloud audio.

---

**"Then it scores them."**

*[click to Sheet 3: Connections Scored]*

Every person I met gets two scores. Not one — two.

**ICP score** — how well do they fit my ideal customer profile. That's Zero CRM's data, not ours.

**Warmth score** — how warm is the *relationship*. Intent, engagement, what they were actually talking about.

Then it computes **uplift** — did the conversation go better or worse than I expected before I walked in?

Anna: ICP 82, warmth 71, predicted 60. Uplift **+11**. That conversation went better than the model expected. She's a hot lead.

Federico from Atomico: ICP only 45 — he's a VC, not a direct buyer — but warmth 68, uplift **+18**. He told me warm intros move 10x faster than cold decks. That's not a lead, that's a connector. Warmth routes him to CRM with a different framing.

Sam Rivera: good ICP, but warmth went *down* vs. prediction. Warmth says don't push outreach — route to the founder community. Someone in your network is a better path in.

---

**"And then it writes the email."**

*[click to Sheet 4: Follow-up Drafts]*

Not a template. A draft grounded in the actual conversation.

Anna's email leads with the accuracy pain she told me about, references the HubSpot AI forecasting moment, and asks for 20 minutes. That's not a mail merge. That's context.

This drops into Gmail. Lightfern polishes it. I review, I send. The whole follow-up loop closes before I've left the building.

---

**"Here's what that looks like across a full day."**

*[back to Sheet 0: Event Summary]*

10 people researched before I walked in. Pre-meet emails drafted overnight.

5 conversations captured today. 3 hot, 1 warm, 1 routed to community.

4 Gmail drafts sitting in my inbox right now, ready to send.

Zero manual logging.

---

**"The insight behind this is simple."**

Most GTM tools treat events as a lead list problem. Scrape the attendees, send everyone the same sequence, hope something lands.

That's not how good relationships start. Good GTM is real connection — and real connection has a moment. It's in the room. It's in what someone actually says when they're not on a sales call.

Warmth instruments that moment. It turns the 60-second hallway conversation into a CRM record, a warmth score, and a personalised email — automatically.

---

**"We built this in one day."**

Python backend. FastAPI. iOS app in SwiftUI with Apple's Liquid Glass. On-device NLP. Zero CRM and UnifyGTM for enrichment. Lightfern for outreach. Gmail via Google MCP.

The pipeline is: phrase trigger → on-device transcript → ML warmth model → CRM routing → Gmail draft.

It runs. The drafts in that spreadsheet are real outputs from the API we built today.

---

**"Best GTM is real connection. Warmth makes every conversation count."**

---

## Q&A prep

**"Isn't this just note-taking?"**
Note-taking captures words. Warmth captures a person model — communication style, values, pain intensity, topic weights. That's what drives the email. Try writing a personalised follow-up from notes at midnight after 30 conversations.

**"What about privacy — recording people?"**
Wake phrase requires active trigger. Audio never leaves the device for NLP — Apple NaturalLanguage runs on-device. Only the structured signal (names, topics, keywords) hits the backend. We're explicit about that in the app permissions flow.

**"Why not just use Notion or HubSpot notes?"**
Because you're not on your laptop when you're on the event floor. And even if you were — structured data that feeds a warmth model is different from a text block in a note. The scoring and routing only work because the data is structured at capture time, not retrospectively.

**"What's the business model?"**
Per-seat SaaS. Sales teams, founders, BD people who go to more than two events a year. The ROI is one warm deal that wouldn't have converted from a cold follow-up.

---
