from pydantic import BaseModel, Field


class TranscriptEvent(BaseModel):
    transcript: str
    speaker: int  # speaker 0, 1, 2... (from diarization)
    confidence: float  # 0.0–1.0
    is_final: bool
    words: list[dict] = Field(default_factory=list)  # word-level timestamps


class SpeakerContext(BaseModel):
    speaker_id: int
    is_self: bool  # True = your own voice, skip
    utterances: list[str] = Field(default_factory=list)
    keywords_hit: list[str] = Field(default_factory=list)
    company_hints: list[str] = Field(default_factory=list)  # extracted company names