"""
Themed crossword generator with a HARD theme-count cap.

The research synthesis (CrosswordGrids, PuzzCulture, CommuniCrossings) is
clear: a clean 15x15 holds 3-5 themed entries; pushing past that ratio
forces obscure fill. Our previous seed-and-discover approach was finding
8-16 SAT words per puzzle — well into "theme-dense" territory where junk
fill is unavoidable.

Here we:
  1. Pick K theme slots (mutually non-crossing, lengths matched to SAT bank).
  2. Restrict those slots' domain to SAT IDs ONLY.
  3. Restrict every OTHER slot's domain to FILL IDs ONLY (no SAT bubble-in).
  4. Solve. Pick the cleanest of N candidate runs.

This caps SAT vocab at exactly K and lets the solver focus its constraint
budget on clean fill instead of stuffing in more themers.

Works for any grid size — pass --template to swap in 11x11 (midi) or
15x15 (standard).
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


def pick_theme_slots(
    slots: list[G.Slot],
    sat_by_len: dict[int, int],
    target: int,
    rng: random.Random,
    attempts: int = 200,
) -> set[int]:
    """Pick `target` mutually non-crossing slots whose length has SAT words."""
    cross = [{sj for _i, sj, _j in s.crossings} for s in slots]
    eligible = [
        i for i, s in enumerate(slots)
        if sat_by_len.get(s.length, 0) > 0
    ]
    best: set[int] = set()
    for _ in range(attempts):
        rng.shuffle(eligible)
        chosen: list[int] = []
        per_len: dict[int, int] = defaultdict(int)
        for si in eligible:
            if len(chosen) >= target:
                break
            L = slots[si].length
            if per_len[L] >= sat_by_len[L]:
                continue
            if any(cj in cross[si] for cj in chosen):
                continue
            chosen.append(si)
            per_len[L] += 1
        if len(chosen) > len(best):
            best = set(chosen)
            if len(best) >= target:
                return best
    return best


def themed_solve(
    slots: list[G.Slot],
    pool: list[str],
    sat_count: int,
    theme_slots: set[int],
    rng: random.Random,
    curated_pool: frozenset[int] | None = None,
    restarts: int = 4,
) -> list[str] | None:
    """Pin theme_slots to (curated) SAT-only, others to fill-only, then solve."""
    filler = G.Filler(slots, pool, sat_count)
    sat_ids = filler.sat_ids
    theme_pool = curated_pool if curated_pool is not None else sat_ids
    base: list[set[int]] = []
    for si, slot in enumerate(filler.slots):
        dom = set(filler.length_ids.get(slot.length, ()))
        if si in theme_slots:
            dom &= theme_pool             # SAT only (curated subset)
        else:
            dom -= sat_ids                # fill only (excludes ALL SAT bank)
        if not dom:
            return None
        base.append(dom)
    for attempt in range(restarts):
        domains = [set(d) for d in base]
        assign: list[int | None] = [None] * len(filler.slots)
        filler.used_ids = set()
        filler.nodes = 0
        if filler._bt(domains, assign, rng, noisy=attempt > 0):
            return [pool[w] for w in assign]  # type: ignore[index]
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default="data/template_15.json",
                    help="grid template JSON (e.g. data/template_11.json)")
    ap.add_argument("--themers", type=int, default=4,
                    help="exact number of SAT themed entries per puzzle "
                         "(NYT clean-fill norm: 3-4 for 15x15, 2-3 for 11x11)")
    ap.add_argument("--curated-themes", type=int, default=30,
                    help="only place themers from the first N SAT bank entries "
                         "(default 30 = the hand-curated headliners). The bulk "
                         "of the 4,966-word bank is freevocabulary additions "
                         "like BASS, EARNEST, LAX, RUE — fine as bonus fill but "
                         "not real SAT vocab. Use 0 to allow any SAT-bank entry.")
    ap.add_argument("--candidates", type=int, default=10)
    ap.add_argument("--time-budget", type=float, default=120.0)
    ap.add_argument("--node-limit", type=int, default=400_000)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--puzzles", type=int, default=1,
                    help="how many puzzles to generate (each gets different "
                         "theme slot picks via rng)")
    ap.add_argument("--start-date", default="2026-12-01")
    ap.add_argument("--start-number", type=int, default=900)
    args = ap.parse_args()

    G.NODE_LIMIT = args.node_limit
    template_path = G.HERE / args.template
    grid = json.loads(template_path.read_text())
    slots = G.extract_slots(grid)
    size = len(grid)
    print(f"template: {template_path.name}  {size}x{size}  {len(slots)} entries",
          flush=True)

    sat = G.load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    sat_list = [w["word"] for w in sat]
    sat_set = set(sat_list)
    # Theme slot pool: only the first --curated-themes SAT entries qualify
    # for placement. The full bank is still tagged isSATVocab in serialization,
    # but we don't let BASS/RUE/LAX-style common words occupy theme positions.
    curated_themes = sat_list[: args.curated_themes] if args.curated_themes else sat_list
    curated_pool = frozenset(range(len(curated_themes)))
    sat_by_len: dict[int, int] = defaultdict(int)
    for w in curated_themes:
        sat_by_len[len(w)] += 1
    fill = G.load_fill()
    pool = sat_list + [w for w in fill if w not in sat_lookup]
    scores = load_scores()
    english_words = {
        w.strip().upper()
        for w in (G.HERE / "data" / "english_words.txt").open()
        if w.strip()
    }
    print(
        f"SAT bank: {len(sat_list):,}, fill pool: {len(fill):,}, "
        f"English dict: {len(english_words):,}",
        flush=True,
    )

    rng = random.Random(args.seed)
    cur_date = date.fromisoformat(args.start_date)
    cur_num = args.start_number
    summary: list[dict] = []

    for p in range(args.puzzles):
        print(f"\n=== puzzle {p + 1}/{args.puzzles} ===", flush=True)
        best_assign = None
        best_theme = None
        best_metrics: tuple[int, int, float, int, int] = (
            -(1 << 30), -1, 0.0, 0, 0
        )
        t_total = time.time()

        for cand in range(args.candidates):
            if time.time() - t_total > args.time_budget:
                print(f"  time budget reached after cand {cand}", flush=True)
                break
            theme_slots = pick_theme_slots(slots, sat_by_len, args.themers, rng)
            if len(theme_slots) < args.themers:
                print(
                    f"  cand {cand + 1}: only found {len(theme_slots)} non-crossing "
                    f"theme slots (need {args.themers}); skipping",
                    flush=True,
                )
                continue
            t0 = time.time()
            assign = themed_solve(
                slots, pool, len(sat_list), theme_slots, rng,
                curated_pool=curated_pool,
            )
            dt = time.time() - t0
            if assign is None:
                print(f"  cand {cand + 1}: fail in {dt:.1f}s", flush=True)
                continue
            ws = [scores.get(w, 30) for w in assign]
            avg = sum(ws) / len(ws)
            weak = sum(1 for s in ws if s < 50)
            sat_n = sum(1 for w in assign if w in sat_set)
            proper_n = sum(
                1 for w in assign
                if w not in sat_set and w not in english_words
            )
            metrics = (-proper_n, sat_n, avg, -weak, cand)
            print(
                f"  cand {cand + 1}: SOLVED {dt:.1f}s "
                f"SAT={sat_n} proper={proper_n} avg={avg:.1f} weak={weak}",
                flush=True,
            )
            if metrics > best_metrics:
                best_metrics = metrics
                best_assign = assign
                best_theme = theme_slots

        if best_assign is None:
            print(f"  ! no fill found, skipping puzzle {p + 1}")
            continue

        date_str = cur_date.isoformat()
        puzzle = G.to_puzzle(
            grid, slots, best_assign, sat_lookup, date_str, cur_num
        )
        out = G.HERE / "output" / f"{date_str}.json"
        out.write_text(json.dumps(puzzle, indent=2))

        sat_in_puzzle = sorted(
            w["answer"] for w in puzzle["words"] if w["isSATVocab"]
        )
        proper_n, sat_n, avg_score, neg_weak, _ = best_metrics
        print(
            f"  -> {out.relative_to(G.HERE)}  "
            f"SAT={sat_n} ({sat_in_puzzle})  "
            f"proper={-proper_n} avg={avg_score:.1f} weak={-neg_weak}"
        )
        summary.append({
            "date": date_str,
            "number": cur_num,
            "themers": args.themers,
            "sat_in_puzzle": sat_in_puzzle,
            "proper_nouns": -proper_n,
            "avg_score": avg_score,
            "weak_fill": -neg_weak,
        })
        cur_date += timedelta(days=1)
        cur_num += 1

    print("\n=== summary ===")
    for s in summary:
        print(
            f"{s['date']} #{s['number']:<3} themers={s['themers']} "
            f"proper={s['proper_nouns']:>2} avg={s['avg_score']:.1f} "
            f"weak={s['weak_fill']:>2}  ({', '.join(s['sat_in_puzzle'])})"
        )
    print(f"\n{len(summary)}/{args.puzzles} puzzles generated")


if __name__ == "__main__":
    main()
