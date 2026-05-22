"""
Grid-size study: which fully-checked square grid is easiest to generate, and
how well can it feature SAT vocabulary?

For each size it builds symmetric, fully-checked grids and measures:

  fill%    — share of grids the solver completes with NO theme constraint
             (pure "can this fully-checked grid be filled at all")
  time     — average solve time of a completed grid
  common%  — share of fill words that are common (wordfreq Zipf >= 3.0); the
             rest are obscure dictionary words forced by tight interlock
  themed   — out of THEME grids, how many accept `theme` forced SAT words
  SAT/pzl  — average SAT words in those themed puzzles

Run:  python3 size_study.py
"""
from __future__ import annotations

import random
import time
from collections import defaultdict

from wordfreq import zipf_frequency

from generator import (
    Filler,
    build_grid,
    choose_theme_slots,
    extract_slots,
    load_fill,
    load_sat,
)

# (size, grids for the no-theme test, grids for the theme test, theme target)
PLAN = [
    (5, 30, 20, 2),
    (7, 30, 20, 3),
    (9, 24, 20, 3),
    (11, 18, 16, 4),
    (13, 12, 12, 4),
]
RESTARTS = 5
COMMON_ZIPF = 3.0


def main() -> None:
    sat = load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    fill = load_fill()
    print(f"fill dictionary: {len(fill):,} words (lowercase — no proper nouns)\n")
    print(f"{'grid':>6} | {'fill%':>6} | {'time':>8} | {'common fill%':>13} "
          f"| {'themed':>14} | {'SAT/pzl':>8}")
    print("-" * 74)

    for size, n_plain, n_theme, theme in PLAN:
        sat_list = [w["word"] for w in sat if len(w["word"]) <= size]
        sat_by_len: dict[int, int] = defaultdict(int)
        for w in sat_list:
            sat_by_len[len(w)] += 1
        pool = sat_list + [w for w in fill if w not in sat_lookup]
        rng = random.Random(100 + size)

        # ── no-theme: pure fully-checked fill feasibility ──
        solved = 0
        solve_time = 0.0
        common_pcts: list[float] = []
        got = 0
        while got < n_plain:
            grid = build_grid(size, rng)
            if grid is None:
                continue
            got += 1
            slots = extract_slots(grid)
            filler = Filler(slots, pool, len(sat_list))
            t0 = time.time()
            assign = filler.solve(rng, restarts=RESTARTS)
            if assign is None:
                continue
            solved += 1
            solve_time += time.time() - t0
            common = sum(
                1 for w in assign if zipf_frequency(w.lower(), "en") >= COMMON_ZIPF
            )
            common_pcts.append(100 * common / len(assign))

        # ── theme: can the grid feature `theme` forced SAT words ──
        themed = 0
        sat_counts: list[int] = []
        got = 0
        while got < n_theme:
            grid = build_grid(size, rng)
            if grid is None:
                continue
            got += 1
            slots = extract_slots(grid)
            filler = Filler(slots, pool, len(sat_list))
            for _try in range(4):  # a few theme-slot selections per grid
                filler.theme_slots = choose_theme_slots(
                    slots, sat_by_len, theme, rng
                )
                if len(filler.theme_slots) < theme:
                    continue
                assign = filler.solve(rng, restarts=RESTARTS)
                if assign is not None:
                    themed += 1
                    sat_counts.append(sum(1 for w in assign if w in sat_lookup))
                    break

        ft = solve_time / solved if solved else 0
        cp = sum(common_pcts) / len(common_pcts) if common_pcts else 0
        sp = sum(sat_counts) / len(sat_counts) if sat_counts else 0
        print(f"{size:>4}x{size:<1}| {100*solved/n_plain:>5.0f}% "
              f"| {ft*1000:>6.0f}ms | {cp:>12.0f}% "
              f"| {themed:>3}/{n_theme:<3} ({100*themed//n_theme:>3}%) "
              f"| {sp:>8.1f}")


if __name__ == "__main__":
    main()
