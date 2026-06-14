"""
Puzzle factory — sweeps {grid templates} × {SAT seed words}, scores each
generated puzzle on quality + variety, keeps the best K overall.

The pipeline so far has been "tune the generator, run it once, look at
one puzzle." This script is the production form: blast through the
combinatorial space, rank, and ship the top.

Quality score (higher better):
   + 1.0 * SAT-vocab count           (theme density)
   + 0.8 * teaching-fill count       (synonym / short-def hits = vocab review)
   + 0.5 * tier-1 fill count         (school-vocab cleanliness)
   - 3.0 * tier-3 fill count         (the thing we most want to avoid)
   - 0.4 * unclued count             (missing definition is bad UX)
   + 0.2 * avg fill score / 10       (general crossword polish)

Variety: when picking top K, prefer puzzles that feature DIFFERENT seed
SAT words. Within the same seed word, we keep at most --per-seed N.

Inputs:
  data/templates_11/template_*.json  — grid library (from survey_templates_11)
  curated SAT seeds (the 30 headliners by default; expand via --seeds N)

Outputs:
  output/factory/<rank>-<seed>-<template>.json    — kept puzzles
  output/factory/_index.json                       — ranking + scores
  output/factory/_report.md                        — human-readable summary
"""
from __future__ import annotations

import argparse
import json
import random
import time
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import generator as G
from pick_15 import load_scores
from seed_15 import seed_solve
from post_improve import post_improve


HERE = Path(__file__).parent
OUT_DIR = HERE / "output" / "factory"


def score_puzzle(
    assign: list[str],
    sat_set: set[str],
    teaching_set: set[str],
    acceptable_fill: set[str],
    scores: dict[str, int],
    definitions: dict,
) -> dict:
    sat_n = sum(1 for w in assign if w in sat_set)
    teach_n = sum(1 for w in assign if w in teaching_set)
    tier3_n = sum(1 for w in assign if scores.get(w, 30) < 50)
    tier1_n = sum(1 for w in assign if scores.get(w, 30) >= 80) - sat_n
    unclued = sum(
        1 for w in assign
        if w not in sat_set
        and w not in teaching_set
        and w not in definitions
    )
    avg = sum(scores.get(w, 30) for w in assign) / max(len(assign), 1)
    score = (
        1.0 * sat_n
        + 0.8 * teach_n
        + 0.5 * tier1_n
        - 3.0 * tier3_n
        - 0.4 * unclued
        + 0.02 * avg
    )
    return {
        "score": round(score, 2),
        "sat": sat_n,
        "teach": teach_n,
        "tier1": tier1_n,
        "tier3": tier3_n,
        "unclued": unclued,
        "avg_fill": round(avg, 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--templates-dir", default="data/templates_11",
        help="directory containing template_*.json files",
    )
    ap.add_argument("--seeds", type=int, default=30,
                    help="number of SAT bank entries to use as seeds "
                         "(first N from sat_words.json; default 30 curated)")
    ap.add_argument("--candidates-per-pair", type=int, default=4,
                    help="solver candidates per (template, seed) pair")
    ap.add_argument("--time-budget-per-pair", type=float, default=20.0,
                    help="seconds per (template, seed) pair before giving up")
    ap.add_argument("--keep", type=int, default=0,
                    help="number of top puzzles to save (0 = save all)")
    ap.add_argument("--per-seed", type=int, default=0,
                    help="max puzzles to keep per seed SAT word "
                         "(0 = no cap, keep all)")
    ap.add_argument("--max-tier3", type=int, default=10,
                    help="hard reject puzzles with > this many tier-3 entries")
    ap.add_argument("--node-limit", type=int, default=500_000)
    ap.add_argument("--rng-seed", type=int, default=2026)
    ap.add_argument("--start-number", type=int, default=1000)
    ap.add_argument("--start-date", default="2027-01-01")
    args = ap.parse_args()

    G.NODE_LIMIT = args.node_limit
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Collect templates
    tmpl_dir = G.HERE / args.templates_dir
    templates = sorted(tmpl_dir.glob("template_*.json"))
    if not templates:
        raise SystemExit(f"no templates found in {tmpl_dir}")

    sat = G.load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    sat_list = [w["word"] for w in sat]
    sat_set = set(sat_list)
    # Filter out tier-3 from the fill pool entirely. The earlier
    # zero-tier-3 experiment showed 11x11 solves cleanly 6/6 against this
    # 95k-word pool, vs a ~33% solve rate on 15x15. With tier-3 absent the
    # solver CAN'T place an obscure acronym — zero tier-3 by construction.
    # --max-tier3 stays as a sanity cap (should always be 0 now).
    raw_fill = G.load_fill()
    raw_scores = load_scores()
    fill = [w for w in raw_fill if raw_scores.get(w, 30) >= 50]
    pool = sat_list + [w for w in fill if w not in sat_lookup]
    word_to_id = {w: i for i, w in enumerate(pool)}
    scores = raw_scores
    definitions = G.load_definitions()
    print(
        f"pool: {len(raw_fill):,} fill -> tier1+2 only: {len(fill):,} "
        f"(tier-3 excluded by construction)",
        flush=True,
    )

    teach_path = G.HERE / "data" / "sat_synonym_index.json"
    teaching_set: set[str] = (
        set(json.loads(teach_path.read_text())) if teach_path.exists() else set()
    )

    scowl = {
        w.strip().upper() for w in (G.HERE / "data" / "scowl.txt").open()
        if w.strip().isalpha()
    }
    dwyl = {
        w.strip().upper() for w in (G.HERE / "data" / "english_words.txt").open()
        if w.strip().isalpha()
    }
    t2_allow = {
        w.strip().upper() for w in (G.HERE / "data" / "tier2_allow.txt").open()
        if w.strip().isalpha()
    }
    acceptable_fill = scowl | dwyl | t2_allow | teaching_set

    seeds = [
        w for w in sat_list[: args.seeds]
        if w in word_to_id
    ]

    def _tier_of(w, _s=scores):
        s = _s.get(w, 30)
        return 0 if s >= 100 else (1 if s >= 80 else (2 if s >= 50 else 3))

    rng = random.Random(args.rng_seed)
    all_candidates: list[dict] = []
    print(
        f"factory sweep: {len(templates)} templates × {len(seeds)} seeds = "
        f"{len(templates) * len(seeds):,} pairs",
        flush=True,
    )
    n_pair = 0
    n_solves = 0
    n_rejects = 0
    t_global = time.time()
    for tmpl_path in templates:
        grid = json.loads(tmpl_path.read_text())
        slots = G.extract_slots(grid)
        size = len(grid)
        by_len: dict[int, list[int]] = defaultdict(list)
        for i, s in enumerate(slots):
            by_len[s.length].append(i)
        for seed_word in seeds:
            n_pair += 1
            if len(seed_word) not in by_len:
                continue
            seed_wid = word_to_id[seed_word]
            best_for_pair = None
            best_score = -1e18
            t_pair = time.time()
            for cand in range(args.candidates_per_pair):
                if time.time() - t_pair > args.time_budget_per_pair:
                    break
                seed_slot = rng.choice(by_len[len(seed_word)])
                assign = seed_solve(
                    slots, pool, len(sat_list), seed_slot, seed_wid, rng,
                    restarts=2,
                )
                if assign is None:
                    continue
                assign, _stats = post_improve(
                    slots, pool, assign, _tier_of,
                    max_iters=6, max_cascade_depth=1, verbose=False,
                )
                metrics = score_puzzle(
                    assign, sat_set, teaching_set,
                    acceptable_fill, scores, definitions,
                )
                if metrics["tier3"] > args.max_tier3:
                    n_rejects += 1
                    continue
                if metrics["score"] > best_score:
                    best_score = metrics["score"]
                    best_for_pair = {
                        "template": tmpl_path.name,
                        "size": size,
                        "seed": seed_word,
                        "assign": assign,
                        "grid_text": grid,
                        **metrics,
                    }
            if best_for_pair is not None:
                all_candidates.append(best_for_pair)
                n_solves += 1
            if n_pair % 25 == 0:
                elapsed = time.time() - t_global
                print(
                    f"  {n_pair}/{len(templates)*len(seeds)} pairs | "
                    f"{n_solves} kept, {n_rejects} rejected (tier3 cap) | "
                    f"{elapsed:.0f}s",
                    flush=True,
                )

    print(f"\nsweep complete: {n_solves:,} viable puzzles, {n_rejects:,} rejected",
          flush=True)

    # Keep EVERY viable puzzle, sorted by goodness. Since the pool is
    # tier-1+2 only, every viable puzzle already has zero tier-3, so
    # "save all zero-tier-3 sorted by score" == save all, ranked.
    # --keep / --per-seed are honored only when > 0 (0 = no cap).
    all_candidates.sort(key=lambda c: -c["score"])
    kept: list[dict] = []
    per_seed_count: dict[str, int] = defaultdict(int)
    for c in all_candidates:
        if c["tier3"] > 0:
            continue
        if args.per_seed and per_seed_count[c["seed"]] >= args.per_seed:
            continue
        kept.append(c)
        per_seed_count[c["seed"]] += 1
        if args.keep and len(kept) >= args.keep:
            break

    # Save each as a finished puzzle file.
    cur_date = date.fromisoformat(args.start_date)
    cur_num = args.start_number
    saved: list[dict] = []
    for rank, c in enumerate(kept, 1):
        grid = c["grid_text"]
        slots = G.extract_slots(grid)
        date_str = cur_date.isoformat()
        puzzle = G.to_puzzle(
            grid, slots, c["assign"], sat_lookup, date_str, cur_num,
        )
        fname = f"{rank:02d}-{c['seed']}-{c['template'].replace('.json','')}.json"
        out = OUT_DIR / fname
        out.write_text(json.dumps(puzzle, indent=2))
        saved.append({
            "rank": rank,
            "file": fname,
            "date": date_str,
            "number": cur_num,
            "size": c["size"],
            "seed": c["seed"],
            "score": c["score"],
            "sat": c["sat"],
            "teach": c["teach"],
            "tier1": c["tier1"],
            "tier3": c["tier3"],
            "unclued": c["unclued"],
            "avg_fill": c["avg_fill"],
        })
        cur_date += timedelta(days=1)
        cur_num += 1

    (OUT_DIR / "_index.json").write_text(json.dumps(saved, indent=2))

    # Human report
    lines = [
        f"# Puzzle factory — {len(saved)} zero-tier-3 puzzles "
        f"(of {len(all_candidates)} viable), ranked by score",
        f"",
        f"Sweep: {len(templates)} templates × {len(seeds)} seeds = "
        f"{n_pair:,} pairs.",
        f"Solved: {n_solves:,}.  Rejected (tier3 > {args.max_tier3}): "
        f"{n_rejects:,}.",
        f"",
        f"| # | seed | template | size | score | SAT | teach | tier1 | tier3 | unclued | avg fill |",
        f"|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in saved:
        lines.append(
            f"| {s['rank']} | {s['seed']} | {s['template']} | "
            f"{s['size']} | {s['score']} | "
            f"{s['sat']} | {s['teach']} | {s['tier1']} | "
            f"{s['tier3']} | {s['unclued']} | {s['avg_fill']} |"
        )
    (OUT_DIR / "_report.md").write_text("\n".join(lines))
    print(f"\nsaved {len(saved)} puzzles -> {OUT_DIR.relative_to(G.HERE)}/")
    print(f"report -> {(OUT_DIR / '_report.md').relative_to(G.HERE)}")


if __name__ == "__main__":
    main()
