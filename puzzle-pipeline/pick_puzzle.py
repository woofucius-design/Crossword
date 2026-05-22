"""
Generates many fully-checked themed puzzles at a given size and keeps the
cleanest one (most common fill words, then most SAT words). Writes the winner
to output/<date>.json.

Run:  python3 pick_puzzle.py --size 6 --theme 3
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict

from wordfreq import zipf_frequency

import generator as G


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=6)
    ap.add_argument("--theme", type=int, default=3)
    ap.add_argument("--date", default="2026-05-22")
    ap.add_argument("--number", type=int, default=48)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--want", type=int, default=30, help="candidates to compare")
    args = ap.parse_args()

    sat = G.load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    sat_list = [w["word"] for w in sat if len(w["word"]) <= args.size]
    sat_by_len: dict[int, int] = defaultdict(int)
    for w in sat_list:
        sat_by_len[len(w)] += 1
    pool = sat_list + [w for w in G.load_fill() if w not in sat_lookup]
    rng = random.Random(args.seed)

    best = None
    best_score = -1.0
    found = 0
    attempts = 0
    while found < args.want and attempts < 12000:
        attempts += 1
        grid = G.build_grid(args.size, rng)
        if grid is None:
            continue
        slots = G.extract_slots(grid)
        filler = G.Filler(slots, pool, len(sat_list))
        for _try in range(5):
            filler.theme_slots = G.choose_theme_slots(
                slots, sat_by_len, args.theme, rng
            )
            if len(filler.theme_slots) < args.theme:
                continue
            assign = filler.solve(rng, restarts=6)
            if assign is None:
                continue
            found += 1
            common = sum(
                1 for w in assign if zipf_frequency(w.lower(), "en") >= 3.0
            )
            sat_n = sum(1 for w in assign if w in sat_lookup)
            score = common + sat_n * 0.5  # cleaner fill first, then more theme
            if score > best_score:
                best_score = score
                best = (grid, slots, assign)
            break

    if best is None:
        raise SystemExit("no puzzle found")

    grid, slots, assign = best
    puzzle = G.to_puzzle(grid, slots, assign, sat_lookup, args.date, args.number)
    out = G.HERE / "output" / f"{args.date}.json"
    out.write_text(json.dumps(puzzle, indent=2))

    for row in puzzle["solution"]:
        print(" ".join("." if ch == "#" else ch for ch in row))
    sat_words = [w for w in puzzle["words"] if w["isSATVocab"]]
    fills = [w for w in puzzle["words"] if not w["isSATVocab"]]
    print(f"\ncompared {found} puzzles")
    print(f"SAT vocab ({len(sat_words)}): {', '.join(w['answer'] for w in sat_words)}")
    print(f"fill ({len(fills)}): {', '.join(w['answer'] for w in fills)}")
    obscure = [
        w["answer"]
        for w in fills
        if zipf_frequency(w["answer"].lower(), "en") < 3.0
    ]
    print(f"obscure fill: {obscure or 'none'}")
    print(f"written -> {out.relative_to(G.HERE)}")


if __name__ == "__main__":
    main()
