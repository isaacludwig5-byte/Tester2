"""Helpers for interacting with YouTube."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlparse

import yt_dlp

_VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


class YouTubeError(RuntimeError):
    """Raised when a YouTube lookup fails."""


@dataclass(frozen=True)
class VideoMetadata:
    video_id: str
    title: str
    duration: float


def extract_video_id(url: str) -> str:
    """Extract the canonical video id from a YouTube URL."""
    parsed = urlparse(url)

    if parsed.hostname in {"youtu.be"}:
        video_id = parsed.path.lstrip("/")
    else:
        query = parse_qs(parsed.query)
        video_id = query.get("v", [""])[0]
        if not video_id and parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/")[2]

    if not _VIDEO_ID_PATTERN.match(video_id):
        raise YouTubeError(f"Could not determine video id from URL: {url}")
    return video_id


def fetch_video_metadata(url: str) -> VideoMetadata:
    """Retrieve title and duration information via yt_dlp."""
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        raise YouTubeError(f"Failed to retrieve metadata for {url}")

    duration = float(info.get("duration") or 0.0)
    if not duration:
        raise YouTubeError("Video duration unavailable; cannot build reels.")

    video_id = info.get("id") or extract_video_id(url)
    title = info.get("title") or "Untitled"
    return VideoMetadata(video_id=video_id, title=title, duration=duration)
