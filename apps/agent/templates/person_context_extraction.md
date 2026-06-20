You analyze a short snippet of a sales/networking conversation spoken by ONE person.
From the transcript below, extract a JSON object describing that person.

Transcript:
"""
{transcript}
"""

Return ONLY a single minified JSON object (no prose, no markdown fences, no tool use,
do not read or write any files) with EXACTLY these keys:
- "communication_style": array of 1-3 lowercase adjectives (e.g. "analytical","data-driven","visionary","relational","pragmatic","skeptical","enthusiastic")
- "values": array of lowercase things they care about (e.g. "accuracy","transparency","growth")
- "topics": array of objects {"topic": string, "weight": number} where weights are 0..1 and sum to ~1; prefer specific phrases (e.g. "pipeline visibility") over generic buckets
- "learnings": array of net-new facts they revealed (e.g. "HubSpot has AI forecasting")
- "pain_points": array of objects {"topic": string, "intensity": number} where intensity is 0..1

If a field has nothing, use an empty array. Output JSON only.
