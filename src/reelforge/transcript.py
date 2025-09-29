"""Transcript retrieval utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi


@dataclass(frozen=True)
class TranscriptLine:
    text: str
    start: float
    duration: float

    @property
    def end(self) -> float:
        return self.start + self.duration


class TranscriptError(RuntimeError):
    """Raised when transcript fetching fails."""


def fetch_transcript(video_id: str, languages: Sequence[str]) -> List[TranscriptLine]:
    """Fetch the best available transcript for a video."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
    except (NoTranscriptFound, TranscriptsDisabled) as exc:
        raise TranscriptError(
            "Captions unavailable; please enable or provide manual transcript."
        ) from exc
    except Exception as exc:  # pragma: no cover - network failure
        raise TranscriptError(f"Unexpected transcript failure: {exc}") from exc

    lines = [
        TranscriptLine(text=entry["text"].strip(), start=float(entry["start"]), duration=float(entry["duration"]))
        for entry in transcript
        if entry.get("text")
    ]

    if not lines:
        raise TranscriptError("Transcript returned no caption lines.")
    return lines
