"""
NYT-style template survey. Generates grids that satisfy the editorial
conventions the earlier template sets violated:

  - 180° rotational symmetry (build_grid enforces this)
  - Black squares <= 1/6 of the grid (15x15: <=37, 11x11: <=20), with a
    small --slack for daily-puzzle latitude (NYT hard cap ~38-42)
  - NO black clumps: largest 4-connected black region <= 3 cells.
    This permits stair-steps (diagonals don't connect) and 2-3 cell edge
    blocks, and bans 2x2+ chunks outright.
  - Marquee-ready: at least 2 symmetric long-slot pairs so themed
    placement has somewhere to live.
  - Fillable: a marquee-style multi-pin probe must solve with the
    tier-1+2 pool inside the time budget.

Run:  python3 survey_nyt_templates.py --size 15 --keep 12
      python3 survey_nyt_templates.py --size 11 --keep 12
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
from marquee_15 import symmetric_marquees, build_pins, multi_pin_solve

HERE = Path(__file__).parent


def max_black_clump(grid) -> int:
    n = len(grid)
    blacks = {(r, c) for r in range(n) for c in range(n) if grid[r][c] == "#"}
    seen: set[tuple[int, int]] = set()
    biggest = 0
    for b in blacks:
        if b in seen:
            continue
        stack, size = [b], 0
        seen.add(b)
        while stack:
            r, c = stack.pop()
            size += 1
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in blacks and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        biggest = max(biggest, size)
    return biggest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=15)
    ap.add_argument("--keep", type=int, default=12)
    ap.add_argument("--candidates", type=int, default=4000,
                    help="random grid attempts")
    ap.add_argument("--max-clump", type=int, default=3)
    ap.add_argument("--slack", type=int, default=0,
                    help="blacks allowed above the 1/6 cap (NYT daily "
                         "latitude is ~38-42 on 15x15; slack 4 = 41)")
    ap.add_argument("--min-marquee-len", type=int, default=0,
                    help="0 = auto (7 for 15x15, 6 for 11x11)")
    ap.add_argument("--min-pairs", type=int, default=2,
                    help="required symmetric long-slot pairs")
    ap.add_argument("--solve-timeout", type=float, default=25.0)
    ap.add_argument("--node-limit", type=int, default=400_000)
    ap.add_argument("--rng-seed", type=int, default=2028)
    ap.add_argument("--out-dir", default="",
                    help="default data/templates_<size>_nyt")
    args = ap.parse_args()

    size = args.size
    G.NODE_LIMIT = args.node_limit
    mml = args.min_marquee_len or (7 if size >= 13 else 6)
    cap = (size * size) // 6 + args.slack
    out_dir = HERE / (args.out_dir or f"data/templates_{size}_nyt")
    out_dir.mkdir(parents=True, exist_ok=True)

    sat = G.load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    sat_list = [w["word"] for w in sat]
    fill = G.load_fill()
    scores = load_scores()
    fill_clean = [w for w in fill if scores.get(w, 30) >= 50]
    pool = sat_list + [w for w in fill_clean if w not in sat_lookup]
    word_to_id = {w: i for i, w in enumerate(pool)}
    fresh_by_len: dict[int, list[str]] = {}
    for w in sat_list:
        fresh_by_len.setdefault(len(w), []).append(w)

    rng = random.Random(args.rng_seed)
    kept: list[dict] = []
    tried = rej_build = rej_black = rej_clump = rej_marquee = rej_fill = 0
    print(f"size={size} black cap={cap} ({100*cap/(size*size):.0f}%) "
          f"max clump={args.max_clump} marquee>={args.min_pairs} pairs "
          f"of len>={mml}", flush=True)

    for i in range(args.candidates):
        tried += 1
        # target the NYT band: ~13% up to the cap
        min_bk = rng.uniform(0.11, 0.14)
        max_bk = cap / (size * size)
        grid = G.build_grid(size, rng, min_bk, max_bk)
        if grid is None:
            rej_build += 1
            continue
        blacks = sum(row.count("#") for row in grid)
        if blacks > cap:
            rej_black += 1
            continue
        if max_black_clump(grid) > args.max_clump:
            rej_clump += 1
            continue
        slots = G.extract_slots(grid)
        pairs, singles = symmetric_marquees(grid, slots, mml)
        if len(pairs) < args.min_pairs:
            rej_marquee += 1
            continue
        ascii_grid = "\n".join(
            "".join("#" if c == "#" else "." for c in row) for row in grid
        )
        if any(k["ascii"] == ascii_grid for k in kept):
            continue

        # Fillability probe: one marquee-style multi-pin solve
        filler = G.Filler(slots, pool, len(sat_list))
        picks = build_pins(slots, pairs, singles, fresh_by_len, rng,
                           min_marquee=2, max_marquee=6, filler=filler)
        if picks is None:
            rej_fill += 1
            continue
        pins = {si: word_to_id[w] for si, w in picks.items()}
        t0 = time.time()
        assign = multi_pin_solve(slots, pool, len(sat_list), pins, rng,
                                 restarts=2, filler=filler)
        dt = time.time() - t0
        if assign is None or dt > args.solve_timeout:
            rej_fill += 1
            continue

        by_len = Counter(s.length for s in slots)
        kept.append({
            "grid": grid, "ascii": ascii_grid, "entries": len(slots),
            "blacks": blacks, "black_pct": 100 * blacks / (size * size),
            "len3": by_len[3], "pairs": len(pairs),
            "max_pair_len": pairs[0][0] if pairs else 0,
            "solve_s": dt,
        })
        print(f"  kept #{len(kept)}: blacks={blacks} "
              f"({100*blacks/(size*size):.0f}%) entries={len(slots)} "
              f"len3={by_len[3]} pairs={len(pairs)} solve={dt:.1f}s",
              flush=True)
        if len(kept) >= args.keep:
            break

    print(f"\ntried {tried}: build={rej_build} black={rej_black} "
          f"clump={rej_clump} marquee={rej_marquee} fill={rej_fill}",
          flush=True)

    kept.sort(key=lambda k: (k["len3"], -k["entries"]))
    for rank, k in enumerate(kept[: args.keep], 1):
        (out_dir / f"template_{rank:02d}.json").write_text(json.dumps(k["grid"]))

    lines = [
        f"# NYT-style {size}x{size} templates",
        "",
        f"180° symmetric; blacks <= {cap} (1/6 cap + slack {args.slack});",
        f"max black clump {args.max_clump} (no 2x2 chunks); >= "
        f"{args.min_pairs} symmetric marquee pairs; marquee-fill probed.",
        "",
        "| # | blacks | black % | entries | len-3 | marquee pairs |",
        "|---|---|---|---|---|---|",
    ]
    for rank, k in enumerate(kept[: args.keep], 1):
        lines.append(
            f"| {rank} | {k['blacks']} | {k['black_pct']:.0f}% "
            f"| {k['entries']} | {k['len3']} | {k['pairs']} |"
        )
    (out_dir / "README.md").write_text("\n".join(lines))
    print(f"saved {min(len(kept), args.keep)} -> {out_dir.relative_to(HERE)}/")


if __name__ == "__main__":
    main()
