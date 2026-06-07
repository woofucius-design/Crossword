"""
Generates a 15×15 fully-checked SAT-themed puzzle.

Uses a pre-built grid template (data/template_15.json) so we skip the slow
grid-search step, and tries several theme-slot placements with the constraint
solver, keeping the cleanest fill (highest-scoring xwordlist entries).

Run:  python3 pick_15.py [--theme 5] [--candidates 8]
"""
from __future__ import annotations

import argparse
import json
import random
import time
from collections import defaultdict
from pathlib import Path

import generator as G


def load_scores() -> dict[str, int]:
    """Parse word->score from broda_wordlist.txt so we can rank candidate
    puzzles. Broda's scoring is what build_fill_list.py now uses to order
    the fill pool, so the picker quality metric needs to agree."""
    out: dict[str, int] = {}
    with (G.HERE / "data" / "broda_wordlist.txt").open(encoding="latin-1") as fh:
        for line in fh:
            word, _, score_str = line.strip().partition(";")
            try:
                out[word.upper()] = int(score_str)
            except ValueError:
                pass
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", type=int, default=5)
    ap.add_argument("--candidates", type=int, default=8)
    ap.add_argument("--date", default="2026-05-22")
    ap.add_argument("--number", type=int, default=48)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    grid = json.loads((G.HERE / "data" / "template_15.json").read_text())
    slots = G.extract_slots(grid)
    sat = G.load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    sat_list = [w["word"] for w in sat]
    sat_by_len: dict[int, int] = defaultdict(int)
    for w in sat_list:
        sat_by_len[len(w)] += 1
    fill = G.load_fill()
    pool = sat_list + [w for w in fill if w not in sat_lookup]
    scores = load_scores()
    print(f"template: {len(slots)} entries; pool: {len(pool):,}", flush=True)

    rng = random.Random(args.seed)
    best = None
    best_score = -1.0
    candidates_found = 0
    attempt = 0
    while candidates_found < args.candidates and attempt < 60:
        attempt += 1
        filler = G.Filler(slots, pool, len(sat_list))
        filler.theme_slots = G.choose_theme_slots(slots, sat_by_len, args.theme, rng)
        if len(filler.theme_slots) < args.theme:
            continue
        t = time.time()
        assign = filler.solve(rng, restarts=3)
        dt = time.time() - t
        if assign is None:
            print(f"  attempt {attempt}: fail in {dt:.0f}s", flush=True)
            continue
        candidates_found += 1
        sat_n = sum(1 for w in assign if w in sat_lookup)
        word_scores = [scores.get(w, 30) for w in assign]
        avg_score = sum(word_scores) / len(word_scores)
        weak = sum(1 for s in word_scores if s < 50)
        # quality rewards average score and bonus SAT words, penalises every
        # below-editor-quality entry hard so the chosen puzzle is clean
        quality = avg_score + sat_n * 1.5 - weak * 4
        print(
            f"  attempt {attempt}: SOLVED {dt:.0f}s SAT={sat_n} "
            f"avg-score={avg_score:.1f} weak={weak} q={quality:.1f}",
            flush=True,
        )
        if quality > best_score:
            best_score = quality
            best = assign

    if best is None:
        raise SystemExit("no puzzle found")

    puzzle = G.to_puzzle(grid, slots, best, sat_lookup, args.date, args.number)
    out = G.HERE / "output" / f"{args.date}.json"
    out.write_text(json.dumps(puzzle, indent=2))

    print()
    for row in puzzle["solution"]:
        print(" ".join("." if c == "#" else c for c in row))
    print()
    sat_words = [w for w in puzzle["words"] if w["isSATVocab"]]
    fills = [w for w in puzzle["words"] if not w["isSATVocab"]]
    print(f"SAT vocab ({len(sat_words)}): {', '.join(w['answer'] for w in sat_words)}")
    weak = [w["answer"] for w in fills if scores.get(w["answer"], 30) < 50]
    print(f"low-score fill ({len(weak)}): {', '.join(weak) if weak else 'none'}")
    print(f"avg fill score: {sum(scores.get(w['answer'], 30) for w in fills) / len(fills):.1f}")
    print(f"written -> {out.relative_to(G.HERE)}")


if __name__ == "__main__":
    main()
