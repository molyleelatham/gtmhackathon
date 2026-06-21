"""AI-agent-backed extractor for per-person context.

Uses the Cursor SDK (`cursor-sdk`) to populate a PersonalContext from a
transcript window with an LLM agent instead of the lexical/regex heuristics.
Falls back cleanly (returns None) whenever the SDK isn't installed, no API key
is configured, or the agent run fails — so the heuristic builder can take over.

Wire it into `PersonContextBuilder(extractor=AgentContextExtractor())`.
"""
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Optional

# Prompt template lives in the agent directory; fall back to an inline copy so
# the extractor still works if the file is missing.
_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2] / "agent" / "templates" / "person_context_extraction.md"
)
_INLINE_PROMPT = """You analyze a short snippet of a sales/networking conversation spoken by ONE person.
From the transcript below, extract a JSON object describing that person.

Transcript:
\"\"\"
{transcript}
\"\"\"

Return ONLY a single minified JSON object (no prose, no markdown fences, no tool use,
do not read or write any files) with EXACTLY these keys:
- "communication_style": array of 1-3 lowercase adjectives
- "values": array of lowercase things they care about
- "topics": array of objects {{"topic": string, "weight": number}} (weights 0..1, sum ~1)
- "learnings": array of net-new facts they revealed
- "pain_points": array of objects {{"topic": string, "intensity": number}} (0..1)

If a field has nothing, use an empty array. Output JSON only."""


def _load_prompt() -> str:
    try:
        return _TEMPLATE_PATH.read_text()
    except Exception:
        return _INLINE_PROMPT


class AgentContextExtractor:
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        cwd: Optional[str] = None,
    ):
        self.model = model or os.getenv("CURSOR_AGENT_MODEL", "composer-2.5")
        # The repo stores the Cursor key as CURSOR_SDK_API_KEY; the SDK reads
        # CURSOR_API_KEY by default — accept either.
        self.api_key = (
            api_key
            or os.getenv("CURSOR_API_KEY")
            or os.getenv("CURSOR_SDK_API_KEY")
        )
        # Isolate the agent in a scratch dir so it has no repo files to wander.
        self.cwd = cwd or tempfile.mkdtemp(prefix="warmth_agent_")
        self.prompt_template = _load_prompt()

    @property
    def available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import cursor_sdk  # noqa: F401
        except Exception:
            return False
        return True

    def extract(self, transcript_window: str) -> Optional[dict[str, Any]]:
        """Run the agent and return the parsed context dict, or None on failure."""
        if not transcript_window.strip() or not self.available:
            return None

        try:
            from cursor_sdk import Agent, AgentOptions, LocalAgentOptions
        except Exception as e:  # pragma: no cover
            print(f"AgentContextExtractor: cursor_sdk import failed: {e}")
            return None

        try:
            result = Agent.prompt(
                self.prompt_template.format(transcript=transcript_window.strip()),
                AgentOptions(
                    api_key=self.api_key,
                    model=self.model,
                    local=LocalAgentOptions(cwd=self.cwd),
                ),
            )
        except Exception as e:  # CursorAgentError or anything else -> fall back
            print(f"AgentContextExtractor: agent run failed: {e}")
            return None

        if getattr(result, "status", None) != "finished":
            print(f"AgentContextExtractor: non-finished status: {getattr(result, 'status', '?')}")
            return None

        return self._parse(getattr(result, "result", "") or "")

    @staticmethod
    def _parse(text: str) -> Optional[dict[str, Any]]:
        """Pull the first JSON object out of the agent's text response."""
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None
