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
    """word -> quality score for the picker's avg-score metric.

    Tier-based, not Broda-based. Broda assigns 100 to vulgar / slang
    (DAFUCK, MURICA, LGBTQ), 70-80 to common everyday words (BREAD, HORSE),
    and only 50 to SAT vocab (LUCID, EPHEMERAL) and obscure technical
    English alike — exactly the inverse of what we want to reward.

    Our scale (matches the tier hierarchy in build_fill_list.py):
      SAT vocab:                 100   (theme priority, highest)
      Tier 1 (school vocab):      80
      Tier 2 (obscure + abbrev):  50
      Tier 3 (random acronyms):   30
      Anything else (not in any list): 30 fallback

    Within tier 1, we add an English-frequency bonus so MOTHER (rank 200)
    scores higher than ALACRITY (rank 50k+). Tier 1 score = 80 + bonus
    where bonus is 0..20 by frequency rank.
    """
    from pathlib import Path
    here = G.HERE
    sat_words = json.loads((here / "data" / "sat_words.json").read_text())
    sat_set = {w["word"].upper() for w in sat_words}
    scowl = {
        w.strip().upper() for w in (here / "data" / "scowl.txt").open()
        if w.strip().isalpha()
    }
    dwyl = {
        w.strip().upper() for w in (here / "data" / "english_words.txt").open()
        if w.strip().isalpha()
    }
    tier2_allow = {
        w.strip().upper() for w in (here / "data" / "tier2_allow.txt").open()
        if w.strip().isalpha()
    }
    freq_rank: dict[str, int] = {}
    for i, w in enumerate((here / "data" / "english_frequency.txt").open(), 1):
        w = w.strip().upper()
        if w.isalpha() and w not in freq_rank:
            freq_rank[w] = i
    freq_total = len(freq_rank)

    def freq_bonus(word: str) -> int:
        rank = freq_rank.get(word)
        if rank is None:
            return 0
        # log-ish bonus: 20 for the top, fading to 0 around rank ~50k
        return max(0, 20 - int(rank / 2500))

    out: dict[str, int] = {}
    for w in sat_set:
        out[w] = 100
    for w in scowl:
        out[w] = max(out.get(w, 0), 80 + freq_bonus(w))
    for w in dwyl - scowl:
        out[w] = max(out.get(w, 0), 50)
    for w in tier2_allow - scowl:
        out[w] = max(out.get(w, 0), 50)
    # Anything not yet scored falls back to 30 (tier 3 territory).
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
