"""Command line interface for the ReelForge viral reel generator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .reel_generator import ReelRequest, generate_reels


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate viral-ready short-form reels from a YouTube video. "
            "The tool analyses the transcript, scores engaging moments, and "
            "exports structured clip manifests ordered by a viral score."
        )
    )
    parser.add_argument("video_url", help="YouTube video URL")
    parser.add_argument(
        "--clip-length",
        type=float,
        default=60.0,
        help="Desired clip length in seconds (default: 60).",
    )
    parser.add_argument(
        "--num-reels",
        type=int,
        default=10,
        help="How many reels to produce (default: 10).",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Transcript language to prioritise when fetching captions (default: en).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory where clip manifests and captions will be stored.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the resulting manifest as JSON to stdout.",
    )
    return parser


def emit_manifest(reels: Sequence[dict], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(reels, fh, indent=2)
    return manifest_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    request = ReelRequest(
        video_url=args.video_url,
        desired_clip_length=args.clip_length,
        num_reels=args.num_reels,
        transcript_languages=[args.language],
        output_dir=args.output_dir,
    )

    results = generate_reels(request)

    manifest_records = [reel.to_dict() for reel in results.reels]
    manifest_path = emit_manifest(manifest_records, results.output_dir)

    summary_lines = [
        f"Created {len(results.reels)} viral reel candidates for {results.video_title!r}",
        f"Manifest: {manifest_path}",
    ]
    for reel in results.reels:
        summary_lines.append(
            f"#{reel.rank:02d} | score {reel.viral_score:.1f}/10 | "
            f"{reel.start_time:.1f}s - {reel.end_time:.1f}s | hook: {reel.hook}"
        )

    print("\n".join(summary_lines))

    if args.json:
        print(json.dumps(manifest_records, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
