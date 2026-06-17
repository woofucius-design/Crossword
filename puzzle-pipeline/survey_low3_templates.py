"""
Generate new 11x11 templates with constraints aimed at higher SAT%:

  - Maximum len-3 slot count (default 8). 3-letter words are almost
    never SAT vocab and dilute the SAT% metric, so we cap them.
  - Maximum word count (default 38). Each entry is a slot the solver
    has to fill; fewer entries means each themer pulls a bigger %.
  - Quick fillability test (still need to confirm grid solves).

Run:  python3 survey_low3_templates.py [--max-len3 8] [--max-entries 38]
"""
from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from pathlib import Path

import generator as G
from pick_15 import load_scores
from seed_15 import seed_solve


HERE = Path(__file__).parent
OUT_DIR = HERE / "data" / "templates_11_low3"
SIZE = 11
SOLVE_TIMEOUT = 6.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-len3", type=int, default=8,
                    help="reject any template with more len-3 slots")
    ap.add_argument("--max-entries", type=int, default=38,
                    help="reject any template with more total entries")
    ap.add_argument("--min-entries", type=int, default=28,
                    help="reject any template with fewer total entries")
    ap.add_argument("--candidates", type=int, default=300,
                    help="random grid attempts to make")
    ap.add_argument("--keep", type=int, default=12,
                    help="how many fillable templates to save")
    args = ap.parse_args()

    G.NODE_LIMIT = 80_000
    OUT_DIR.mkdir(exist_ok=True)

    sat = G.load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    sat_list = [w["word"] for w in sat]
    fill = G.load_fill()
    pool = sat_list + [w for w in fill if w not in sat_lookup]
    word_to_id = {w: i for i, w in enumerate(pool)}
    # tier-1+2 pool (same as factory)
    scores = load_scores()
    pool_clean = [w for w in pool if w in sat_lookup or scores.get(w, 30) >= 50]
    word_to_id_clean = {w: i for i, w in enumerate(pool_clean)}

    rng = random.Random(2027)
    kept: list[dict] = []

    print(f"target: max len-3={args.max_len3}, entries in "
          f"[{args.min_entries},{args.max_entries}]", flush=True)
    print(f"trying {args.candidates} grids...", flush=True)

    for i in range(args.candidates):
        # try varied black ratios
        min_bk = rng.uniform(0.17, 0.24)
        max_bk = min_bk + rng.uniform(0.04, 0.08)
        grid = G.build_grid(SIZE, rng, min_bk, max_bk)
        if grid is None:
            continue
        slots = G.extract_slots(grid)
        if not (args.min_entries <= len(slots) <= args.max_entries):
            continue
        by_len = Counter(s.length for s in slots)
        n3 = by_len[3]
        if n3 > args.max_len3:
            continue
        max_len = max(by_len)
        ascii_grid = "\n".join(
            "".join("#" if c == "#" else "." for c in row) for row in grid
        )
        if any(k["ascii"] == ascii_grid for k in kept):
            continue

        # Quick fillability test — try 2 SAT seeds with the clean pool
        seeds_to_try = ["LUCID", "ASTUTE", "NOVICE", "EPHEMERAL"]
        from collections import defaultdict
        by_lens: dict[int, list[int]] = defaultdict(list)
        for j, s in enumerate(slots):
            by_lens[s.length].append(j)
        ok = 0
        for seed_w in seeds_to_try[:2]:
            if len(seed_w) not in by_lens:
                continue
            if seed_w not in word_to_id_clean:
                continue
            seed_wid = word_to_id_clean[seed_w]
            seed_slot = rng.choice(by_lens[len(seed_w)])
            t0 = time.time()
            assign = seed_solve(
                slots, pool_clean,
                sum(1 for w in pool_clean if w in sat_lookup),
                seed_slot, seed_wid, rng, restarts=2,
            )
            if assign is not None and (time.time() - t0) <= SOLVE_TIMEOUT:
                ok += 1
        if ok == 0:
            continue

        kept.append({
            "grid": grid, "ascii": ascii_grid, "entries": len(slots),
            "len3": n3, "max_len": max_len,
            "len3_pct": 100 * n3 / len(slots),
            "by_len": dict(by_len),
            "fillability": ok,
        })
        print(
            f"  kept #{len(kept)}: entries={len(slots)} len3={n3} "
            f"({100*n3/len(slots):.0f}%) max_len={max_len} "
            f"fill_ok={ok}/2",
            flush=True,
        )
        if len(kept) >= args.keep:
            break

    # Rank: prefer fewer len-3 + balanced entry count + better fillability
    kept.sort(key=lambda k: (-k["fillability"], k["len3"], k["entries"]))
    for rank, k in enumerate(kept[:args.keep], 1):
        path = OUT_DIR / f"template_{rank:02d}.json"
        path.write_text(json.dumps(k["grid"]))

    # Write a small report
    lines = [
        f"# 11x11 low-3 templates",
        f"",
        f"Filter: ≤{args.max_len3} three-letter slots, "
        f"{args.min_entries}-{args.max_entries} total entries, "
        f"fillable with the tier-1+2 pool.",
        f"",
        f"| # | entries | len-3 | len-3 % | max len | fill ok |",
        f"|---|---|---|---|---|---|",
    ]
    for rank, k in enumerate(kept[:args.keep], 1):
        lines.append(
            f"| {rank} | {k['entries']} | {k['len3']} | "
            f"{k['len3_pct']:.0f}% | {k['max_len']} | {k['fillability']}/2 |"
        )
    (OUT_DIR / "README.md").write_text("\n".join(lines))
    print(f"\nsaved {min(len(kept), args.keep)} templates -> "
          f"{OUT_DIR.relative_to(HERE)}/")


if __name__ == "__main__":
    main()
