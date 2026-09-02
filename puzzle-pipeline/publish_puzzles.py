"""
Publishes generated puzzles into the app bundle.

For a free v1 the whole corpus ships inside the binary: no backend, no
per-request cost, and every puzzle is playable on a plane. 300 puzzles cost
a few MB, which is noise next to a React Native bundle.

Two decisions are baked in here rather than in the app:

  Calendar shape. Sundays get a 15x15, every other day an 11x11 or smaller.
  A daily that is always the same size gets monotonous, and a 15x15 every
  day is too much for a student on a bus — this mirrors how newspaper
  crosswords pace a week.

  Determinism. A date maps to a puzzle by counting days from a fixed anchor,
  so every player sees the same grid on the same day with no server telling
  them so. That is what makes a shared result meaningful.

  python3 publish_puzzles.py [--anchor-back 90]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parent / "src" / "data" / "corpus.json"

# Fields the app actually reads. Everything else is pipeline bookkeeping
# (clueSource, isSATSynonym, per-word altClues) and is dropped.
WORD_KEYS = (
    "id", "number", "direction", "row", "col", "length",
    "answer", "clue", "isSATVocab", "definition", "isMarquee",
)
FEATURED_KEYS = ("word", "clue", "definition")


def load(path: str) -> dict:
    d = json.loads(Path(path).read_text())
    return {
        "number": d["number"],
        "size": d["size"],
        "solution": d["solution"],
        "cells": d["cells"],
        "words": [
            {k: w[k] for k in WORD_KEYS if k in w} for w in d["words"]
        ],
        "featured": [
            {k: f[k] for k in FEATURED_KEYS if k in f}
            for f in d.get("featured", [])
        ],
    }


def collect(dirname: str) -> list[dict]:
    paths = sorted(
        p for p in glob.glob(str(HERE / "output" / dirname / "*.json"))
        if not os.path.basename(p).startswith("_")
    )
    return [load(p) for p in paths]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--anchor-back", type=int, default=90,
        help="Days of back-catalogue before today, so the archive isn't "
             "empty on launch day.",
    )
    args = ap.parse_args()

    # Marquee sets lead: their SAT words are deliberately placed in the long
    # symmetric slots, so they read as constructed rather than incidental.
    small = collect("marquee_11x11") + collect("factory")
    large = collect("marquee_15x15") + collect("factory_15x15")

    anchor = date.today() - timedelta(days=args.anchor_back)
    by_date: dict[str, dict] = {}
    si = li = 0
    day = anchor
    while si < len(small) or li < len(large):
        # Sunday is the big one.
        want_large = day.weekday() == 6
        pool, idx = (large, li) if want_large else (small, si)
        if idx >= len(pool):  # that pool is exhausted; fall back to the other
            pool, idx = (small, si) if want_large else (large, li)
            want_large = not want_large
            if idx >= len(pool):
                break
        puzzle = dict(pool[idx])
        iso = day.isoformat()
        puzzle["date"] = iso
        # Renumber sequentially by date: the pipeline's own numbers restart
        # per output directory, so raw they collide across sets.
        puzzle["number"] = len(by_date) + 1
        by_date[iso] = puzzle
        if want_large:
            li += 1
        else:
            si += 1
        day += timedelta(days=1)

    dates = sorted(by_date)
    payload = {
        "anchor": dates[0],
        "lastDate": dates[-1],
        "count": len(dates),
        "puzzles": [by_date[d] for d in dates],
    }
    OUT.write_text(json.dumps(payload, separators=(",", ":")))

    size_mb = OUT.stat().st_size / 1e6
    sundays = sum(1 for d in dates if date.fromisoformat(d).weekday() == 6)
    print(f"wrote {OUT.relative_to(HERE.parent)}  {size_mb:.2f} MB")
    print(f"  {len(dates)} puzzles  {dates[0]} -> {dates[-1]}")
    print(f"  {sundays} Sundays (15x15), {len(dates) - sundays} weekdays")
    sat = sum(
        1 for p in payload["puzzles"] for w in p["words"] if w.get("isSATVocab")
    )
    print(f"  {sat:,} SAT entries, {sat / len(dates):.1f} per puzzle")


if __name__ == "__main__":
    main()
