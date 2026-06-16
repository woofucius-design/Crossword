"""
Low-three 11x11 template survey.

Sister script to survey_templates_11.py, tuned for ONE goal: build a library
of 11x11 grid templates with as few length-3 slots as possible, so the puzzle
factory can land a HIGHER percentage of SAT vocabulary.

Why length-3 hurts SAT density: of the 4,966 SAT bank words, only 20 are
3 letters long (and 125 are 4 letters) — 97% are 5+. A length-3 slot is
therefore almost always pure fill that can never headline a vocab word. The
fewer of them a grid has, the more of its slots are SAT-eligible.

How we get there:
  * Generate from LOW black-square ratios (longer white runs => fewer short
    words). build_grid's row search still guarantees every run is >= MIN_RUN
    and the grid is symmetric + connected + fully checked.
  * Hard-reject any template whose length-3 share exceeds --max-len3-share.
  * Keep only templates the seed solver can actually fill, then rank by
    (fewest length-3, highest SAT density, lowest tier-3, highest fill score).

Outputs:
  data/templates_11_lowthree/template_<rank>.json   — grid library
  data/templates_11_lowthree/README.md              — report

Feed the result to the factory:
  python3 puzzle_factory.py --templates-dir data/templates_11_lowthree ...
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
SIZE = 11


def template_stats(grid: list[list[str]]) -> dict:
    size = len(grid)
    black = sum(1 for row in grid for c in row if c == "#")
    slots = G.extract_slots(grid)
    by_len = Counter(s.length for s in slots)
    return {
        "size": size,
        "black": black,
        "white": size * size - black,
        "black_pct": 100 * black / (size * size),
        "entries": len(slots),
        "length_counts": dict(sorted(by_len.items())),
        "len3": by_len.get(3, 0),
        "max_length": max(by_len),
        "len3_share": by_len.get(3, 0) / len(slots) if slots else 1.0,
    }


def test_template(
    grid: list[list[str]],
    pool: list[str],
    sat_list: list[str],
    sat_set: set[str],
    word_to_id: dict[str, int],
    acceptable_fill: set[str],
    scores: dict[str, int],
    seed_words: list[str],
    rng: random.Random,
    solve_budget: float,
) -> dict:
    slots = G.extract_slots(grid)
    by_len: dict[int, list[int]] = defaultdict(list)
    for i, s in enumerate(slots):
        by_len[s.length].append(i)
    solves = 0
    sat_counts: list[int] = []
    tier3_counts: list[int] = []
    avg_scores: list[float] = []
    times: list[float] = []
    for seed_word in seed_words:
        if len(seed_word) not in by_len:
            continue
        seed_wid = word_to_id[seed_word]
        seed_slot = rng.choice(by_len[len(seed_word)])
        t0 = time.time()
        assign = seed_solve(
            slots, pool, len(sat_list), seed_slot, seed_wid, rng, restarts=2,
        )
        dt = time.time() - t0
        times.append(dt)
        if assign is None or dt > solve_budget:
            continue
        solves += 1
        sat_counts.append(sum(1 for w in assign if w in sat_set))
        tier3_counts.append(sum(
            1 for w in assign if w not in sat_set and w not in acceptable_fill
        ))
        ws = [scores.get(w, 30) for w in assign]
        avg_scores.append(sum(ws) / len(ws))
    return {
        "solve_rate": solves / max(len(seed_words), 1),
        "avg_sat": sum(sat_counts) / len(sat_counts) if sat_counts else 0,
        "avg_tier3": sum(tier3_counts) / len(tier3_counts) if tier3_counts else 999,
        "avg_score": sum(avg_scores) / len(avg_scores) if avg_scores else 0,
        "avg_solve_s": sum(times) / len(times) if times else 0,
        "solves": solves,
    }


def render_ascii(grid: list[list[str]]) -> str:
    return "\n".join(
        "".join("#" if c == "#" else "." for c in row) for row in grid
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", type=int, default=400,
                    help="how many random grids to generate and test")
    ap.add_argument("--keep", type=int, default=12,
                    help="how many top templates to save")
    ap.add_argument("--max-len3-share", type=float, default=0.18,
                    help="reject templates whose length-3 share exceeds this")
    ap.add_argument("--min-black", type=float, default=0.10,
                    help="low black ratios make longer (fewer short) words")
    ap.add_argument("--max-black", type=float, default=0.17)
    ap.add_argument("--seeds-per-template", type=int, default=5)
    ap.add_argument("--solve-budget", type=float, default=6.0)
    ap.add_argument("--node-limit", type=int, default=80_000)
    ap.add_argument("--rng-seed", type=int, default=2027)
    ap.add_argument("--out-dir", default="data/templates_11_lowthree")
    args = ap.parse_args()

    G.NODE_LIMIT = args.node_limit
    out_dir = HERE / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    sat = G.load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    sat_list = [w["word"] for w in sat]
    sat_set = set(sat_list)
    fill = G.load_fill()
    pool = sat_list + [w for w in fill if w not in sat_lookup]
    word_to_id = {w: i for i, w in enumerate(pool)}
    scores = load_scores()
    scowl_all = {
        w.strip().upper() for w in (HERE / "data" / "scowl.txt").open()
        if w.strip().isalpha()
    }
    dwyl = {
        w.strip().upper() for w in (HERE / "data" / "english_words.txt").open()
        if w.strip().isalpha()
    }
    tier2_allow = {
        w.strip().upper() for w in (HERE / "data" / "tier2_allow.txt").open()
        if w.strip().isalpha()
    }
    acceptable_fill = scowl_all | dwyl | tier2_allow

    # Seeds chosen to span lengths so the solver is tested across slot sizes.
    test_seeds = [w for w in ["LUCID", "OPULENT", "DEFT", "EPHEMERAL",
                              "BENEVOLENT"] if w in word_to_id]

    print(
        f"low-three survey: up to {args.candidates} {SIZE}x{SIZE} grids, "
        f"black {args.min_black:.2f}-{args.max_black:.2f}, "
        f"reject len3-share > {args.max_len3_share:.0%}",
        flush=True,
    )
    rng = random.Random(args.rng_seed)
    candidates: list[dict] = []
    seen_ascii: set[str] = set()
    n_built = 0
    n_share_reject = 0
    t_global = time.time()

    for i in range(args.candidates):
        mb = rng.uniform(args.min_black, args.max_black)
        xb = mb + rng.uniform(0.03, 0.06)
        grid = G.build_grid(SIZE, rng, mb, xb)
        if grid is None:
            continue
        n_built += 1
        stats = template_stats(grid)
        ascii_grid = render_ascii(grid)
        if ascii_grid in seen_ascii:
            continue
        seen_ascii.add(ascii_grid)
        if stats["len3_share"] > args.max_len3_share:
            n_share_reject += 1
            continue
        metrics = test_template(
            grid, pool, sat_list, sat_set, word_to_id,
            acceptable_fill, scores, test_seeds, rng, args.solve_budget,
        )
        candidates.append({"grid": grid, "ascii": ascii_grid, **stats, **metrics})
        print(
            f"  kept {len(candidates):>2}. black={stats['black_pct']:.0f}% "
            f"entries={stats['entries']} len3={stats['len3']} "
            f"({stats['len3_share']*100:.0f}%) max_len={stats['max_length']}  "
            f"solves={metrics['solves']}/{len(test_seeds)} "
            f"sat={metrics['avg_sat']:.1f} tier3={metrics['avg_tier3']:.1f} "
            f"avg-score={metrics['avg_score']:.0f}",
            flush=True,
        )

    print(
        f"\nbuilt {n_built} grids, {n_share_reject} over len3-share cap, "
        f"{len(candidates)} kept for ranking ({time.time()-t_global:.0f}s)",
        flush=True,
    )

    # Only consider templates the solver could actually fill at least once.
    fillable = [c for c in candidates if c["solves"] > 0]
    # Rank: fewest length-3, then highest SAT density, then least tier-3,
    # then highest fill score, then more solves (robustness).
    fillable.sort(key=lambda c: (
        c["len3"],
        -c["avg_sat"],
        c["avg_tier3"],
        -c["avg_score"],
        -c["solves"],
    ))
    keep = fillable[: args.keep]

    for rank, c in enumerate(keep, 1):
        (out_dir / f"template_{rank:02d}.json").write_text(json.dumps(c["grid"]))

    lines = [
        f"# 11x11 Low-Three Template Library — top {len(keep)}\n",
        f"_Generated by `survey_templates_11_lowthree.py`. Goal: minimize "
        f"length-3 slots so the factory lands a higher SAT percentage._\n",
        f"Built {n_built} random grids (black {args.min_black:.0%}-"
        f"{args.max_black:.0%}); rejected {n_share_reject} over the "
        f"{args.max_len3_share:.0%} length-3 share cap; {len(fillable)} "
        f"were fillable.\n",
        "## Why this matters\n",
        "Only 20 of 4,966 SAT words are 3 letters (97% are 5+). Length-3 "
        "slots are dead weight for vocab — fewer of them means more "
        "SAT-eligible slots.\n",
        "| Rank | Black % | Entries | **Len-3** | Len-3 share | Max len | "
        "Solve rate | Avg SAT | Avg tier 3 | Avg score |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for rank, c in enumerate(keep, 1):
        lines.append(
            f"| {rank} | {c['black_pct']:.0f}% | {c['entries']} | "
            f"**{c['len3']}** | {c['len3_share']*100:.0f}% | {c['max_length']} | "
            f"{c['solve_rate']*100:.0f}% | {c['avg_sat']:.1f} | "
            f"{c['avg_tier3']:.1f} | {c['avg_score']:.0f} |"
        )
    lines.append("\n## Grids\n")
    for rank, c in enumerate(keep, 1):
        lines.append(f"### Template {rank:02d}  (template_{rank:02d}.json)  "
                     f"— {c['len3']} length-3 slots\n")
        lines.append("```")
        lines.append(c["ascii"])
        lines.append("```\n")

    (out_dir / "README.md").write_text("\n".join(lines))
    if keep:
        best, worst = keep[0]["len3"], keep[-1]["len3"]
        print(f"saved {len(keep)} templates (len3 range {best}-{worst}) "
              f"-> {out_dir.relative_to(HERE)}/")
    else:
        print("no fillable templates met the cap — loosen --max-len3-share")


if __name__ == "__main__":
    main()
