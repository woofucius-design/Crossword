"""
Generates a 15×15 fully-checked SAT-themed puzzle (legacy entry point —
the actively-used scripts are seed_15.py and themed_15.py).

Also exposes load_scores() which returns the tier-based quality score
the picker uses to evaluate candidate puzzles. The scoring agrees with
the tier classification in build_fill_list.py.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from collections import defaultdict
from pathlib import Path

import generator as G


def _classify_tier(word: str,
                   sat: set[str],
                   scowl_all: set[str],
                   scowl_lower: set[str],
                   dwyl: set[str],
                   tier2_allow: set[str],
                   tier3_force: set[str],
                   freq: dict[str, int]) -> int:
    """Return 0 (SAT) / 1 / 2 / 3. Matches build_fill_list tiering exactly."""
    if word in sat:
        return 0
    if word in tier3_force:
        return 3
    if word in scowl_lower:
        return 1
    if word in scowl_all - scowl_lower:
        r = freq.get(word, 1 << 30)
        if r <= 12_000:
            return 1
        if r <= 100_000:
            return 2
        return 3
    if word in tier2_allow:
        return 2
    if word in dwyl:
        r = freq.get(word, 1 << 30)
        return 2 if r <= 100_000 else 3
    return 3


def load_scores() -> dict[str, int]:
    """word -> quality score for the picker's avg-score metric.

    Tier-based, not Broda-based. Broda assigns 100 to vulgar / slang
    (DAFUCK, MURICA, LGBTQ), 70-80 to common everyday words (BREAD, HORSE),
    and only 50 to SAT vocab (LUCID, EPHEMERAL) and obscure technical
    English — exactly the inverse of what we want to reward.

    Our scale (matches build_fill_list.py exactly):
      SAT vocab:                 100
      Tier 1 (school vocab):      80 + 0..20 frequency bonus
      Tier 2 (in-top-100k or curated abbrev/Roman): 50
      Tier 3 (archaic, niche, forced):              30
    """
    here = G.HERE
    sat_words = json.loads((here / "data" / "sat_words.json").read_text())
    sat_set = {w["word"].upper() for w in sat_words}

    def load_alpha(path: Path, *, lower_only: bool = False) -> set[str]:
        out: set[str] = set()
        for w in path.open():
            w = w.strip()
            if not w or not w.isalpha():
                continue
            if lower_only and not w.islower():
                continue
            out.add(w.upper())
        return out

    scowl_all = load_alpha(here / "data" / "scowl.txt")
    scowl_lower = load_alpha(here / "data" / "scowl.txt", lower_only=True)
    dwyl = load_alpha(here / "data" / "english_words.txt")
    tier2_allow = load_alpha(here / "data" / "tier2_allow.txt")
    tier3_force: set[str] = set()
    for line in (here / "data" / "tier3_force.txt").open():
        line = line.split("#", 1)[0].strip().upper()
        if line and line.isalpha():
            tier3_force.add(line)

    freq: dict[str, int] = {}
    for i, w in enumerate((here / "data" / "english_frequency.txt").open(), 1):
        w = w.strip().upper()
        if w.isalpha() and w not in freq:
            freq[w] = i
    freq_no_rank = len(freq) + 1

    def freq_bonus(word: str) -> int:
        rank = freq.get(word)
        if rank is None:
            return 0
        return max(0, 20 - int(rank / 2500))

    out: dict[str, int] = {}
    # We need to score every word that might appear in a puzzle, so iterate
    # the union of all known sources rather than per-tier sets.
    universe = sat_set | scowl_all | dwyl | tier2_allow | tier3_force
    for w in universe:
        tier = _classify_tier(
            w, sat_set, scowl_all, scowl_lower, dwyl,
            tier2_allow, tier3_force, freq,
        )
        if tier == 0:
            out[w] = 100
        elif tier == 1:
            out[w] = 80 + freq_bonus(w)
        elif tier == 2:
            out[w] = 50
        else:
            out[w] = 30
    return out


def main() -> None:
    """Legacy 15x15 generator — kept for the original demo puzzle.
    Use seed_15.py for the current pipeline."""
    raise SystemExit(
        "pick_15.py is legacy; use seed_15.py for the current pipeline. "
        "load_scores() is still imported by other scripts."
    )


if __name__ == "__main__":
    main()
