# Warmth Web Dashboard

The browser-based **personal CRM** for Warmth. The iPhone + Apple Watch apps
**capture** connections at events; this dashboard is where you **monitor,
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
make run-api
```

Production builds require `web/.env.production` (copy from `.env.production.example`).

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Landing page |
| `/signin` | Google sign-in |
| `/app` | Dashboard — stats, upcoming events, top leads (auth required) |
| `/app/events` | Detected events |
| `/app/connections` | All connections by warmth |
| `/app/connections/:id` | Detail, scores, routing + follow-up actions |

## Build & quality

```bash
npm run lint       # ESLint
npm run typecheck  # TypeScript (src/)
npm run build      # Production bundle → dist/
npm run test       # Vitest
```

Deploy via `make deploy-web` from the repo root.
