"""
Survey 15x15 templates with 180° rotational symmetry, optimized for higher
SAT% by capping the 3-letter slot count.

Constraints:
  - Symmetric (180° rotational — enforced by generator.build_grid)
  - Word count in [args.min_entries, args.max_entries] (NYT std: 70-78)
  - At most args.max_len3 three-letter slots
  - Fillable with the tier-1+2 pool (2 of 4 seed solves succeed)

Run:  python3 survey_15x15_templates.py
"""
from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

import generator as G
from pick_15 import load_scores
from seed_15 import seed_solve


HERE = Path(__file__).parent
OUT_DIR = HERE / "data" / "templates_15"
SIZE = 15
SOLVE_TIMEOUT = 20.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-len3", type=int, default=14,
                    help="reject templates with more len-3 slots")
    ap.add_argument("--min-entries", type=int, default=70,
                    help="reject templates with fewer entries")
    ap.add_argument("--max-entries", type=int, default=78,
                    help="reject templates with more entries")
    ap.add_argument("--candidates", type=int, default=500,
                    help="random grid attempts to make")
    ap.add_argument("--keep", type=int, default=10,
                    help="how many fillable templates to save")
    ap.add_argument("--node-limit", type=int, default=300_000)
    args = ap.parse_args()

    G.NODE_LIMIT = args.node_limit
    OUT_DIR.mkdir(exist_ok=True)

    sat = G.load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    sat_list = [w["word"] for w in sat]
    fill = G.load_fill()
    scores = load_scores()
    fill_clean = [w for w in fill if scores.get(w, 30) >= 50]
    pool = sat_list + [w for w in fill_clean if w not in sat_lookup]
    word_to_id = {w: i for i, w in enumerate(pool)}

    rng = random.Random(2026)
    kept: list[dict] = []
    print(f"target: entries [{args.min_entries},{args.max_entries}], "
          f"max len-3={args.max_len3}", flush=True)
    print(f"trying {args.candidates} grids...", flush=True)

    seeds_to_try = ["LUCID", "ASTUTE", "NOVICE", "EPHEMERAL"]

    for i in range(args.candidates):
        # NYT 15x15 conventions: 15-22% black squares
        min_bk = rng.uniform(0.15, 0.20)
        max_bk = min_bk + rng.uniform(0.03, 0.06)
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

        # Fillability — try 2 seeds with the clean pool
        by_lens: dict[int, list[int]] = defaultdict(list)
        for j, s in enumerate(slots):
            by_lens[s.length].append(j)
        ok = 0
        for seed_w in seeds_to_try[:2]:
            if len(seed_w) not in by_lens or seed_w not in word_to_id:
                continue
            seed_wid = word_to_id[seed_w]
            seed_slot = rng.choice(by_lens[len(seed_w)])
            t0 = time.time()
            assign = seed_solve(
                slots, pool, len(sat_list), seed_slot, seed_wid, rng,
                restarts=2,
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
            f"({100*n3/len(slots):.0f}%) max_len={max_len} fill_ok={ok}/2",
            flush=True,
        )
        if len(kept) >= args.keep:
            break

    kept.sort(key=lambda k: (-k["fillability"], k["len3"], -k["entries"]))
    for rank, k in enumerate(kept[:args.keep], 1):
        path = OUT_DIR / f"template_{rank:02d}.json"
        path.write_text(json.dumps(k["grid"]))

    lines = [
        f"# 15x15 templates with rotational symmetry, lower len-3 share",
        f"",
        f"Constraints: 180° rotationally symmetric, "
        f"{args.min_entries}-{args.max_entries} entries, "
        f"≤{args.max_len3} three-letter slots, fillable with the "
        f"tier-1+2 pool.",
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
