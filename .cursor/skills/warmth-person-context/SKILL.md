---
name: warmth-person-context
description: >-
  Warmth's per-person context model — how speaker turns accumulate into an
  evolving PersonNode (communication style, values, topic weights, learnings,
  pain points) and feed the Zero CRM narrative + Faxxing outreach. Use when
  working on PersonContextBuilder, PersonNode/PersonalContext/PersonKnowledgeGraph,
  the AI-agent extractor, the context narrative, or per-person personalization.
---

# Warmth Per-Person Context

Builds an evolving, per-speaker understanding of who you met and uses it to
personalize the CRM record and outreach.

```
transcript utterance -> SpeakerID -> PersonNode -> PersonContextBuilder.update()
  -> PersonalContext accumulates over 30s windows -> PersonNode.context evolves
  -> Zero CRM narrative -> Faxxing personalises to communication_style + values
```

## Models (`packages/core/models/person.py`)

| Type | Role |
|------|------|
| `PersonalContext` | The delta from ONE ~30s window: `communication_style`, `values`, `topic_weights`, `learnings`, `pain_points`, excerpt. |
| `PersonNode` | The evolving aggregate for one speaker. `update(context)` folds a window in (merges traits, sums + renormalises topic weights, escalates pain intensity). Exposes `dominant_topic`, `top_pain`, `to_narrative()`. |
| `PersonKnowledgeGraph` | Session graph: diarization `speaker_id -> PersonNode`. `get_or_create`, `people(exclude_self=True)`; skips your own voice via `self_speaker_id`. |
| `PainPoint` | `topic` + accumulated `intensity` (0..1) → `level` (low/moderate/high). |

`to_narrative()` is what gets pushed to Zero CRM, e.g.:

> Anna is analytical, data-driven, cares about accuracy. Dominant topic: pipeline
> visibility. Recently learned HubSpot has AI forecasting. High pain intensity
> around manual data entry.

## Two ways to populate it

`PersonContextBuilder` (`apps/listener/intelligence/person_context_builder.py`)
`update(kg, speaker_id, transcript_window, ...)` maps a speaker's window to a
`PersonNode` and folds in the new context.

1. **Heuristic (default, no key)** — lexical style cues, `InterestAnalyzer`
   values, `TopicExtractor` buckets + salient repeated bigrams, regex learnings,
   intensifier-scored pains.
2. **AI agent (Cursor SDK)** — pass
   `PersonContextBuilder(extractor=AgentContextExtractor())`
   (`apps/listener/intelligence/agent_extractor.py`). It runs a one-shot
   `Agent.prompt` with the template at
   `apps/agent/templates/person_context_extraction.md`, parses the JSON, and
   maps it onto `PersonalContext` (heuristics fill any gaps). Reads
   `CURSOR_API_KEY` or `CURSOR_SDK_API_KEY`; model via `CURSOR_AGENT_MODEL`
   (default `composer-2.5`). Returns `None` on any failure so heuristics take
   over. ~15-25s per window (a coding agent) — run it off the event loop with
   `asyncio.to_thread`.

`MeetEncoder(use_agent=True)` wires the agent path automatically.

## Downstream

- **Zero CRM** — `ZeroCRMMapper.lead_to_zero_payload_with_context(lead, person)`
  attaches the narrative + structured `communication_style`/`values`/
  `dominant_topic`/`pain_points`.
- **Faxxing** — `FaxxingClient.personalize_sequence(person)` tailors tone + hook
  to the person's style and anchors copy on their values.

## Run it

```bash
python warmth/scripts/demo_person_context.py        # heuristic, reproduces the Anna example
# AI agent path (per request):
MEET_PORT=8077 python warmth/scripts/serve_meet_local.py
curl -s -X POST http://127.0.0.1:8077/meet/encode -d '{"use_agent": true, "turns": [...]}'
```

## Notes

- Window accumulation re-normalises topic weights each update; a repeated
  specific phrase (e.g. "pipeline visibility") rises to `dominant_topic`.
- To swap the agent for a direct LLM JSON call, implement the same
  `extract(transcript_window) -> dict | None` interface and pass it as
  `extractor`.
