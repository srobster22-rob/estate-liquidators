"""Command line interface.

    clipper VIDEO_OR_URL [--transcript SUBS] [-n 5] [--layout blur] [-o out/]

`--dry-run` does everything except encode, which is the fast way to argue with
the scorer: it prints what it would cut, why, and the feature breakdown behind
each choice.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

from . import captions as C
from . import framing as F
from . import render as R
from . import score as SC
from . import segment as S
from . import sources
from . import transcript as T


def slugify(text: str, limit: int = 48) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in text]
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:limit] or "clip"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="clipper",
        description="Cut a long talking-head video into short vertical clips.",
    )
    p.add_argument("target", help="a local video file, or a URL for yt-dlp")
    p.add_argument("--transcript", help="subtitle file (.vtt/.srt); found automatically if omitted")
    p.add_argument("-o", "--out", default="clips", help="output directory (default: clips)")
    p.add_argument("-n", "--count", type=int, default=5, help="how many clips (default: 5)")
    p.add_argument(
        "--layout",
        choices=("auto",) + R.LAYOUTS,
        default="auto",
        help="reframing. 'auto' crops when the subject can be located, else letterboxes",
    )
    p.add_argument("--min-duration", type=float, default=15.0)
    p.add_argument("--max-duration", type=float, default=60.0)
    p.add_argument("--no-captions", action="store_true", help="do not burn in captions")
    p.add_argument("--weights", help="JSON file of scoring weights")
    p.add_argument("--dry-run", action="store_true", help="pick clips, print them, encode nothing")
    p.add_argument("--json", action="store_true", help="emit a machine-readable manifest")
    p.add_argument("--crf", type=int, default=20, help="x264 quality, lower is better")
    return p


def pick(
    tr: T.Transcript,
    *,
    count: int,
    min_duration: float,
    max_duration: float,
    weights: SC.Weights | None,
) -> tuple[list[SC.Scored], S.Segmentation]:
    seg = S.segment(tr)
    cands = S.candidates(seg, min_duration=min_duration, max_duration=max_duration)
    if not cands:
        return [], seg
    return SC.select(SC.rank(cands, seg, weights), count=count), seg


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = Path(args.out)

    with tempfile.TemporaryDirectory(prefix="clipper-ingest-") as workdir:
        try:
            ingest = sources.resolve(args.target, workdir, args.transcript)
        except sources.IngestError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        if ingest.transcript is None:
            print(
                "error: no transcript found. Pass --transcript, or put a .vtt/.srt "
                "next to the video.",
                file=sys.stderr,
            )
            return 2

        tr = T.load(ingest.transcript)
        if not tr.words:
            print(f"error: {ingest.transcript} parsed to zero words", file=sys.stderr)
            return 2

        weights = SC.Weights.load(args.weights) if args.weights else None
        picks, seg = pick(
            tr,
            count=args.count,
            min_duration=args.min_duration,
            max_duration=args.max_duration,
            weights=weights,
        )
        if not picks:
            print(
                f"error: no candidate clip between {args.min_duration}s and "
                f"{args.max_duration}s. The transcript is {tr.duration:.0f}s long.",
                file=sys.stderr,
            )
            return 1

        if not args.json:
            kind = "auto-captions" if tr.rolling or not seg.punctuated else "captions"
            print(
                f"{ingest.video.name}: {tr.duration:.0f}s, {len(tr.words)} words "
                f"({kind}), {len(seg)} utterances"
            )
            if not tr.has_real_word_timings:
                print("  note: word timings are interpolated — caption highlighting is off")
            if not seg.punctuated:
                print(
                    "  note: no punctuation or capitals in this transcript, so clip "
                    "boundaries rest on silence alone — selection is measurably less "
                    "reliable here (see DECISIONS.md D-20)"
                )

        manifest = []
        info = None if args.dry_run else R.probe(ingest.video)

        for i, s in enumerate(picks, 1):
            name = f"{i:02d}-{slugify(s.text)}"
            entry = {
                "index": i,
                "start": round(s.start, 3),
                "end": round(s.end, 3),
                "duration": round(s.duration, 3),
                "score": round(s.total, 3),
                "features": {k: round(v, 3) for k, v in s.features.items()},
                "text": s.text,
                "file": None,
            }

            if not args.json:
                print(f"\n[{i}] {s.start:7.1f} → {s.end:7.1f}  ({s.duration:4.1f}s)  {s.explain()}")
                print(f"    {s.text[:160]}{'…' if len(s.text) > 160 else ''}")

            layout, aimed = args.layout, None
            if layout in ("auto", "fill") and not args.dry_run:
                aimed = F.aim(
                    ingest.video,
                    start=s.start, duration=s.duration,
                    source_width=info.width, source_height=info.height,
                    target_width=R.CANVAS_W, target_height=R.CANVAS_H,
                )
                if layout == "auto":
                    layout = F.choose_layout(aimed)
                entry["aim"] = round(aimed.center, 3)
                entry["aim_confidence"] = round(aimed.confidence, 3)
            entry["layout"] = layout

            if not args.json and aimed is not None:
                if aimed.fell_back:
                    print(
                        f"    subject not locatable (confidence {aimed.confidence:.2f})"
                        f" -> {layout}"
                    )
                else:
                    print(
                        f"    subject at {aimed.center * 100:.0f}% across"
                        f" (confidence {aimed.confidence:.2f}) -> {layout}"
                    )

            if not args.dry_run:
                ass = None
                if not args.no_captions:
                    ass = C.build_ass(
                        tr.slice(s.start, s.end), offset=s.start, duration=s.duration
                    )
                dest = out_dir / f"{name}.mp4"
                try:
                    R.render_clip(
                        ingest.video, dest,
                        start=s.start, end=s.end,
                        ass=ass, layout=layout, info=info, crf=args.crf,
                        aim=aimed.center if aimed else 0.5,
                    )
                except R.RenderError as exc:
                    print(f"error: clip {i} failed to render: {exc}", file=sys.stderr)
                    return 3
                entry["file"] = str(dest)
                if not args.json:
                    print(f"    -> {dest}")

            manifest.append(entry)

        if args.json:
            print(json.dumps({"source": str(ingest.video), "clips": manifest}, indent=2))
        elif not args.dry_run:
            (out_dir / "manifest.json").write_text(
                json.dumps({"source": str(ingest.video), "clips": manifest}, indent=2),
                encoding="utf-8",
            )
            print(f"\n{len(manifest)} clips in {out_dir}/")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
