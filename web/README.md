# Warmth Web Dashboard

The browser-based **personal CRM** for Warmth. The iPhone + Apple Watch apps
**capture** connections at conferences; this dashboard is where you **monitor,
review, and manage** them across the lifecycle:

1. **Before meet** — detected events, enriched + warmth-scored attendees, outreach drafts
2. **Meet** — captured signals routed by the ML pipeline (CRM + outreach vs. founder community)
3. **Post meet** — personalized follow-ups

## Stack

- Vite + React + TypeScript + Tailwind CSS
- Talks to the FastAPI backend (`apps/api`) over REST

## Run

```bash
cd web
cp .env.example .env          # set VITE_API_BASE_URL (defaults to http://localhost:8000)
npm install
npm run dev                   # http://localhost:5173
```

Start the backend separately so the dashboard has data:

```bash
# from repo root
uv run uvicorn apps.api.main:app --reload --port 8000
```

The backend ships with an in-memory demo store (`apps/api/store.py`) seeded with
a sample conference and connections, so the dashboard renders without Firebase or
external API keys.

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Dashboard — stats, upcoming events, top leads |
| `/events` | Detected conferences |
| `/events/:id` | Before-meet pipeline + ranked leads |
| `/connections` | All connections by warmth |
| `/connections/:id` | Detail, scores, routing + follow-up actions |

## Build

```bash
npm run build      # outputs to dist/ (deployable to Firebase Hosting, Vercel, etc.)
```
