"""Core orchestration logic for producing reel manifests."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Sequence

from .scoring import normalise_scores, sliding_windows
from .transcript import TranscriptLine, fetch_transcript
from .youtube import VideoMetadata, fetch_video_metadata


@dataclass(frozen=True)
class ReelRequest:
    video_url: str
    desired_clip_length: float
    num_reels: int = 10
    transcript_languages: Sequence[str] = ("en",)
    output_dir: Path = Path("output")


@dataclass
class ReelClip:
    """Represents a single reel suggestion."""

    rank: int
    start_time: float
    end_time: float
    duration: float
    viral_score: float
    hook: str
    raw_text: str
    caption_lines: List[dict]
    highlight_words: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "viral_score": round(self.viral_score, 2),
            "hook": self.hook,
            "raw_text": self.raw_text,
            "captions": self.caption_lines,
            "highlight_words": self.highlight_words,
        }


@dataclass(frozen=True)
class ReelResult:
    video_id: str
    video_title: str
    output_dir: Path
    reels: Sequence[ReelClip]


def _generate_caption_lines(window_lines: Sequence[TranscriptLine], start_offset: float) -> List[dict]:
    captions = []
    for line in window_lines:
        captions.append(
            {
                "text": line.text,
                "start": max(line.start - start_offset, 0.0),
                "end": max(line.end - start_offset, 0.0),
            }
        )
    return captions


def _hook_from_text(text: str) -> str:
    sentences = re.split(r"(?<=[.!?]) +", text.strip())
    if not sentences:
        return text[:80]
    hook = sentences[0]
    if len(hook.split()) < 6 and len(sentences) > 1:
        hook = " ".join(sentences[:2])
    hook = hook.strip()
    if not hook.endswith("?"):
        hook = hook.rstrip(".!")
    if len(hook.split()) > 18:
        hook_words = hook.split()[:18]
        hook = " ".join(hook_words) + "…"
    if not hook:
        hook = "You won't believe this"
    return hook


def _highlight_keywords(text: str) -> List[str]:
    words = [word.strip(".,!?\"'").lower() for word in text.split()]
    counts = {}
    for word in words:
        if not word or len(word) < 4:
            continue
        counts[word] = counts.get(word, 0) + 1
    sorted_words = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [word for word, _ in sorted_words[:5]]


def _build_reel(window, score: float, rank: int) -> ReelClip:
    duration = window.end - window.start
    captions = _generate_caption_lines(window.lines, window.start)
    hook = _hook_from_text(window.text)
    highlights = _highlight_keywords(window.text)
    return ReelClip(
        rank=rank,
        start_time=round(window.start, 2),
        end_time=round(window.end, 2),
        duration=round(duration, 2),
        viral_score=score,
        hook=hook,
        raw_text=window.text,
        caption_lines=captions,
        highlight_words=highlights,
    )


def _prepare_output_dir(request: ReelRequest, metadata: VideoMetadata) -> Path:
    output_root = request.output_dir / metadata.video_id
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root


def generate_reels(request: ReelRequest) -> ReelResult:
    """Generate viral-ready reels based on a YouTube transcript."""
    metadata = fetch_video_metadata(request.video_url)
    transcript = fetch_transcript(metadata.video_id, request.transcript_languages)

    windows = list(sliding_windows(transcript, window_seconds=request.desired_clip_length))
    if not windows:
        raise RuntimeError("Unable to compute candidate reels; transcript too short.")

    scores = normalise_scores(windows)
    scored_windows = list(zip(windows, scores))
    scored_windows.sort(key=lambda item: item[1], reverse=True)

    top_windows = scored_windows[: request.num_reels]

    reels: List[ReelClip] = []
    for idx, (window, score) in enumerate(top_windows, start=1):
        reels.append(_build_reel(window, score=score, rank=idx))

    output_dir = _prepare_output_dir(request, metadata)
    return ReelResult(video_id=metadata.video_id, video_title=metadata.title, output_dir=output_dir, reels=reels)
