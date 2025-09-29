# ReelForge

ReelForge is a transcript-driven viral reel generator inspired by platforms like Vizard.ai and OpusClips. Provide a YouTube link and ReelForge will analyse the transcript, score the most compelling moments, and output a ranked list of short-form reels complete with hooks, captions, and viral potential scores.

## Features

- Fetches video metadata and transcripts directly from YouTube.
- Scores transcript windows using viral-friendly heuristics (hooks, keywords, pacing, diversity).
- Produces auto-caption timelines for each reel candidate.
- Generates ten (configurable) reel manifests ordered by a 1-10 viral score.
- Highlights attention grabbing keywords to guide motion graphics or emphasis layers.

## Requirements

- Python 3.11+
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp)
- [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api)

Install dependencies via:

```bash
pip install -e .
```

## Usage

```bash
reelforge "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --clip-length 60 --num-reels 10
```

This command will output a manifest under `output/<video_id>/manifest.json` containing an ordered list of the most viral-worthy clips. Each clip includes:

- start/end timestamps relative to the full video
- a crafted 3-second hook
- an auto-caption track with time-aligned entries
- a viral score out of 10
- highlighted keywords for motion graphics overlays

Pass `--json` to print the manifest to stdout, or adjust `--clip-length` to target 30s, 60s, 120s, or longer reels.

## Output Structure

```json
[
  {
    "rank": 1,
    "start_time": 123.5,
    "end_time": 183.5,
    "duration": 60.0,
    "viral_score": 9.4,
    "hook": "This is the moment everything changed",
    "raw_text": "…",
    "captions": [
      {"text": "…", "start": 0.0, "end": 3.2},
      {"text": "…", "start": 3.2, "end": 5.9}
    ],
    "highlight_words": ["secret", "strategy", "growth"]
  }
]
```

Use the manifest as an editing script for your preferred video editor or automation platform to render the actual reels with captions and motion graphics.
