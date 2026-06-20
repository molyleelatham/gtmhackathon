---
name: warmth-meet-pipeline
description: >-
  How Warmth's MEET stage turns a captured conversation into routed GTM actions:
  diarized transcript -> encoders -> ML models -> routing -> Zero CRM + Faxxing/Lightfern.
  Use when working on the meet pipeline, MeetEncoder, MeetIntelligencePipeline,
  MeetStageAgent, routing decisions, the local meet server, or wiring captured
  signals into the warmth/lead/cluster models.
---

# Warmth MEET Pipeline

The MEET stage runs a captured conversation through encoders → models → routing
→ outreach. Everything runs as the `warmth.*` package from the **repo root** (the
directory that contains `warmth/`); relative imports assume a parent `warmth`
package.

## Data flow

```
diarized transcript ([{speaker, text}], self_speaker_id)
  -> MeetEncoder            encoders: per-person context + MeetingSignal
  -> MeetIntelligencePipeline  models: warmth/lead/cluster -> RoutingDecision
  -> warmth uplift?  yes -> Zero CRM push + Faxxing sequence + Lightfern Gmail draft
                     no  -> founder community (nearest friend/founder)
```

## Key files

| Concern | File |
|---------|------|
| Encoder: transcript → `MeetingSignal` + `PersonKnowledgeGraph` | `apps/listener/intelligence/meet_encoder.py` |
| Per-person context models + AI extractor | see the `warmth-person-context` skill |
| Models + routing (`MeetIntelligencePipeline`, `RoutingDecision`, `RoutingTarget`) | `packages/ml/pipeline.py` |
| Warmth / lead / cluster models | `packages/ml/warmth_model.py`, `lead_scorer.py`, `clustering.py` |
| Meet lifecycle (CRM push + Faxxing + Lightfern) | `apps/lifecycle/meet.py` (`MeetPipeline`) |
| Autonomous meet agent | `apps/agent/meet_pipeline.py` (`MeetStageAgent`) |
| Zero CRM narrative payload | `packages/integrations/zero_crm/mapper.py` (`lead_to_zero_payload_with_context`) |
| Faxxing outreach personalisation | `packages/integrations/faxxing/client.py` |
| Lightfern Gmail draft handoff | `packages/integrations/lightfern/workflow.py` |
| API endpoints | `apps/api/routers/meet.py`, `postmeet.py` |
| Local test server (no Firebase/audio) | `scripts/serve_meet_local.py` |

## MeetingSignal is the contract

`MeetingSignal` (`packages/core/models/meeting_signal.py`) is what the models
consume: `name`, `company`, `interests`, `topic_time` (per-topic seconds),
`most_time_topic`, `what_you_learned`, `most_interesting`, and
`personal_context` (the evolved `PersonNode`). The encoder produces it; the API
also accepts one directly.

## Routing rule

`MeetIntelligencePipeline.run()` scores post-meet warmth and routes:
- with a pre-meet baseline: route to CRM when `uplift > uplift_threshold`
- with no baseline: route to CRM when `actual_score >= 70`
- otherwise → `FOUNDER_COMMUNITY`

The warmth model scales engagement at ~10 pts/min of `topic_time`, so short
transcripts score cold by design. `RoutingDecision.outreach_sequence` holds the
Faxxing sequence and is only populated on the CRM branch when a `PersonNode`
rides along on the signal.

## Run it locally

Boot the lightweight meet server (only fastapi + uvicorn needed):

```bash
pip install fastapi uvicorn
MEET_PORT=8077 python warmth/scripts/serve_meet_local.py   # from repo root
```

Endpoints (add `"use_agent": true` to populate context via the Cursor SDK agent):
- `POST /meet/encode` — transcript → `MeetingSignal` + knowledge graph
- `POST /meet/signals` — structured `MeetingSignal` → `RoutingDecision`
- `POST /meet/process` — encode + models in one call

Run the autonomous agent demo:

```bash
python -m warmth.apps.agent.meet_pipeline
```

## Extending

- New conversational features → add to `MeetEncoder._signal_from_node` and the
  `MeetingSignal` model, then map into `WarmthFeatures` in `warmth_model.py`.
- Replace a stub model → keep the method signature in `packages/ml/` stable;
  `MeetIntelligencePipeline` orchestrates them.
- Outreach tone/channels → edit `FaxxingClient._draft_sequence`.
