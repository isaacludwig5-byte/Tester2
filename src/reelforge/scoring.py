"""Scoring heuristics for evaluating transcript windows."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .transcript import TranscriptLine

TRENDING_KEYWORDS = {
    "secret": 2.5,
    "revealed": 2.0,
    "mistake": 2.0,
    "hack": 1.8,
    "viral": 1.8,
    "strategy": 1.6,
    "surprising": 1.5,
    "profit": 1.5,
    "fail": 1.5,
    "don't": 1.4,
    "never": 1.4,
    "imagine": 1.3,
    "insane": 1.3,
    "incredible": 1.3,
    "why": 1.2,
    "how": 1.2,
    "lesson": 1.1,
    "warning": 1.1,
}


@dataclass(frozen=True)
class Window:
    start: float
    end: float
    text: str
    lines: Sequence[TranscriptLine]
    score: float


def _tokenise(text: str) -> List[str]:
    return [token.lower() for token in text.replace("\n", " ").split() if token]


def score_window(lines: Sequence[TranscriptLine]) -> float:
    """Assign a viral-worthiness score to a caption window."""
    if not lines:
        return 0.0

    tokens = _tokenise(" ".join(line.text for line in lines))
    length_penalty = 1.0 / (1.0 + abs(len(tokens) - 80) / 80)

    keyword_bonus = sum(TRENDING_KEYWORDS.get(token.strip(".,!?"), 0.0) for token in tokens)
    question_bonus = 1.5 if any("?" in line.text for line in lines) else 0.0
    excitement_bonus = sum(1 for token in tokens if token.isupper()) * 0.2

    unique_tokens = len(set(tokens)) or 1
    diversity_score = unique_tokens / len(tokens) if tokens else 0.0

    pace = statistics.mean(line.duration for line in lines)
    pace_score = 1.0 / (1.0 + abs(pace - 2.5))

    raw_score = keyword_bonus + 5 * diversity_score + 3 * pace_score + question_bonus + excitement_bonus
    return raw_score * length_penalty


def sliding_windows(transcript: Sequence[TranscriptLine], window_seconds: float, stride: float = 5.0) -> Iterable[Window]:
    """Generate sliding windows over the transcript with approximate duration."""
    if not transcript:
        return []

    n = len(transcript)
    start_idx = 0
    while start_idx < n:
        window_lines: List[TranscriptLine] = []
        end_time = transcript[start_idx].start
        target_end = transcript[start_idx].start + window_seconds

        idx = start_idx
        while idx < n and transcript[idx].start < target_end:
            window_lines.append(transcript[idx])
            end_time = transcript[idx].end
            idx += 1

        if window_lines:
            yield Window(
                start=window_lines[0].start,
                end=end_time,
                text=" ".join(line.text for line in window_lines),
                lines=tuple(window_lines),
                score=score_window(window_lines),
            )

        next_start_time = transcript[start_idx].start + stride
        while start_idx < n and transcript[start_idx].start < next_start_time:
            start_idx += 1


def normalise_scores(windows: Sequence[Window]) -> List[float]:
    if not windows:
        return []
    scores = [window.score for window in windows]
    if len(set(scores)) == 1:
        return [5.0 for _ in windows]

    min_score = min(scores)
    max_score = max(scores)
    spread = max_score - min_score or 1.0
    return [((score - min_score) / spread) * 9 + 1 for score in scores]
