"""
Themed 15x15 generator: deliberately place 4-6 featured SAT words in the
long/symmetric marquee slots, the way constructed themed puzzles do —
instead of hoping SAT words land somewhere organically.

  - Marquee slots = the longest slots (>=7), grouped into 180°-symmetric
    pairs (plus self-symmetric central slots). Theme entries occupy
    symmetric pairs of equal length, per crossword convention.
  - Featured words are drawn ONLY from SAT bank words that have never
    appeared in any previously generated puzzle (fresh vocabulary), and
    each generated puzzle uses a disjoint featured set.
  - Fill pool is tier-1+2 only (zero tier-3 by construction), same as
    puzzle_factory.
  - Featured entries are marked isMarquee in the JSON and listed in a
    top-level "featured" array (word + clue + definition) so the app can
    show a post-solve vocab recap.

Run:  python3 marquee_15.py --puzzles 10
"""
from __future__ import annotations

import argparse
import glob
import json
import random
import time
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import generator as G
from pick_15 import load_scores
from post_improve import post_improve

HERE = Path(__file__).parent
# Output dir comes from --output-dir; module-level default kept for imports.
OUT_DIR = HERE / "output" / "marquee_15x15"


def used_words_in_outputs() -> set[str]:
    """Every answer that appears in any previously generated puzzle."""
    used: set[str] = set()
    for path in glob.glob(str(HERE / "output" / "**" / "*.json"), recursive=True):
        name = Path(path).name
        if name.startswith("_"):
            continue
        try:
            d = json.loads(Path(path).read_text())
        except Exception:
            continue
        words = d.get("words") if isinstance(d, dict) else None
        if not words:
            continue
        for w in words:
            if isinstance(w, dict) and w.get("answer"):
                used.add(w["answer"])
    return used


def symmetric_marquees(grid, slots, min_len: int = 7):
    """(pairs, singles): symmetric slot-index pairs and self-symmetric
    slot indexes among slots of length >= min_len, longest first."""
    n = len(grid)
    by_cells = {tuple(s.cells): i for i, s in enumerate(slots)}
    pairs: list[tuple[int, int, int]] = []  # (length, i, j)
    singles: list[tuple[int, int]] = []     # (length, i)
    seen: set[int] = set()
    for i, s in enumerate(slots):
        if s.length < min_len or i in seen:
            continue
        twin = tuple((n - 1 - r, n - 1 - c) for (r, c) in reversed(s.cells))
        j = by_cells.get(twin)
        if j == i:
            singles.append((s.length, i))
            seen.add(i)
        elif j is not None and slots[j].length == s.length:
            pairs.append((s.length, i, j))
            seen.add(i)
            seen.add(j)
    pairs.sort(reverse=True)
    singles.sort(reverse=True)
    return pairs, singles


def pins_consistent(slots, pins: dict[int, str]) -> bool:
    """Where two pinned slots cross, their letters must agree."""
    for si, word_i in pins.items():
        for idx_i, sj, idx_j in slots[si].crossings:
            if sj in pins and pins[sj][idx_j] != word_i[idx_i]:
                return False
    return True


def build_pins(slots, pairs, singles, fresh_by_len, rng,
               min_marquee: int, max_marquee: int,
               filler: G.Filler | None = None,
               probe: int = 40) -> dict[int, str] | None:
    """Choose a crossing-consistent set of fresh SAT words for the marquee
    slots. Long marquee slots cross each other (a 15-across runs through
    the 9-downs), so words are placed longest-first and each later
    candidate is filtered by the letters already fixed at its crossings.
    A pair whose slots can't both be satisfied is dropped whole, keeping
    180° symmetry intact.

    When a filler is provided, each candidate is also DOMAIN-CHECKED:
    every unpinned slot it crosses must retain at least one pool word
    compatible with all pinned letters — otherwise the fill is doomed
    before the solver starts (a marquee 'Z' with no ?Z? crossing word).
    Only the first `probe` shuffled candidates are domain-checked, to
    bound cost."""
    picks: dict[int, str] = {}
    taken: set[str] = set()

    def crossing_domains_ok(si: int, w: str) -> bool:
        if filler is None:
            return True
        for idx_i, sj, idx_j in slots[si].crossings:
            if sj in picks:
                continue
            dom = None
            for jdx, sk, kdx in slots[sj].crossings:
                if sk == si:
                    letter = w[kdx]
                elif sk in picks:
                    letter = picks[sk][kdx]
                else:
                    continue
                allowed = filler.pos_index.get(
                    (slots[sj].length, jdx, letter), G.EMPTY
                )
                dom = allowed if dom is None else dom & allowed
                if not dom:
                    return False
        return True

    # Crossing-friendliness: prefer marquee words made of common letters —
    # they leave crossing slots far more fill options than rare-letter
    # monsters like PLENIPOTENTIARY.
    _FREQ = {c: 12 - i for i, c in enumerate("EARIOTNSLCUDPM")}

    def _friendly(w: str) -> int:
        return sum(_FREQ.get(c, 0) for c in w)

    def fit(si: int) -> str | None:
        length = slots[si].length
        cands = fresh_by_len.get(length, [])
        if not cands:
            return None
        constraints = [
            (idx_i, picks[sj][idx_j])
            for idx_i, sj, idx_j in slots[si].crossings
            if sj in picks
        ]
        order = rng.sample(cands, len(cands))
        # keep exploration random but tilt toward friendly-letter words
        order.sort(key=_friendly, reverse=True)
        order = order[: max(probe * 3, 60)]
        rng.shuffle(order)
        checked = 0
        for w in order:
            if w in taken:
                continue
            if not all(w[a] == letter for a, letter in constraints):
                continue
            checked += 1
            if checked > probe:
                return None
            if crossing_domains_ok(si, w):
                return w
        return None

    for _L, i, j in pairs:
        if len(picks) + 2 > max_marquee:
            continue
        # Thin fresh supply at this length = rare-letter monsters only;
        # a forced 15-length pair from 7 candidates dooms the fill.
        if len(fresh_by_len.get(_L, [])) < 20:
            continue
        w_i = fit(i)
        if w_i is None:
            continue
        picks[i] = w_i
        taken.add(w_i)
        w_j = fit(j)
        if w_j is None:
            # drop the pair whole — symmetry demands both or neither
            del picks[i]
            taken.discard(w_i)
            continue
        picks[j] = w_j
        taken.add(w_j)
    for _L, i in singles:
        if len(picks) >= max_marquee:
            break
        w = fit(i)
        if w is not None:
            picks[i] = w
            taken.add(w)
    if len(picks) < min_marquee:
        return None
    return picks


def multi_pin_solve(slots, pool, sat_count, pins: dict[int, int],
                    rng: random.Random, restarts: int = 3,
                    filler: G.Filler | None = None):
    """Full solve with several words pinned (domains forced to singletons).
    Same machinery as seed_15.seed_solve, generalized to N pins."""
    if filler is None:
        filler = G.Filler(slots, pool, sat_count)
    base: list[set[int]] = []
    for si, slot in enumerate(filler.slots):
        dom = set(filler.length_ids.get(slot.length, ()))
        if si in pins:
            if pins[si] not in dom:
                return None
            dom = {pins[si]}
        if not dom:
            return None
        base.append(dom)
    for attempt in range(restarts):
        domains = [set(d) for d in base]
        assign: list[int | None] = [None] * len(filler.slots)
        filler.used_ids = set()
        filler.nodes = 0
        if filler._bt(domains, assign, rng, noisy=attempt > 0):
            return [pool[w] for w in assign]
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puzzles", type=int, default=10)
    ap.add_argument("--min-marquee", type=int, default=4,
                    help="minimum featured words per puzzle")
    ap.add_argument("--max-marquee", type=int, default=6)
    ap.add_argument("--attempts-per-puzzle", type=int, default=12,
                    help="pin-set attempts before moving to next template")
    ap.add_argument("--time-budget", type=float, default=240.0,
                    help="seconds per puzzle before giving up")
    ap.add_argument("--node-limit", type=int, default=400_000)
    ap.add_argument("--rng-seed", type=int, default=2027)
    ap.add_argument("--templates-dir", nargs="+",
                    default=["data/templates_15"],
                    help="one or more directories of template_*.json")
    ap.add_argument("--output-dir", default="output/marquee_15x15")
    ap.add_argument("--min-marquee-len", type=int, default=7,
                    help="slots at least this long count as marquee slots")
    ap.add_argument("--start-date", default="2027-07-01")
    ap.add_argument("--start-number", type=int, default=2000)
    args = ap.parse_args()

    G.NODE_LIMIT = args.node_limit
    out_dir = HERE / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    sat = G.load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    sat_list = [w["word"] for w in sat]
    fill = G.load_fill()
    scores = load_scores()
    fill_clean = [w for w in fill if scores.get(w, 30) >= 50]
    pool = sat_list + [w for w in fill_clean if w not in sat_lookup]
    word_to_id = {w: i for i, w in enumerate(pool)}
    sat_set = set(sat_list)

    used = used_words_in_outputs()
    fresh = [w for w in sat_list if w not in used]
    fresh_by_len: dict[int, list[str]] = defaultdict(list)
    for w in fresh:
        fresh_by_len[len(w)].append(w)
    print(f"SAT bank {len(sat_list):,}; used in prior puzzles "
          f"{len(sat_set & used):,}; fresh {len(fresh):,}")
    print("fresh by length:",
          {k: len(v) for k, v in sorted(fresh_by_len.items()) if k >= 7})

    templates = sorted(
        p for d in args.templates_dir
        for p in glob.glob(str(HERE / d / "template_*.json"))
    )
    print(f"{len(templates)} templates from {args.templates_dir}")
    rng = random.Random(args.rng_seed)
    teach_path = HERE / "data" / "sat_synonym_index.json"
    teaching_set: set[str] = (
        set(json.loads(teach_path.read_text())) if teach_path.exists() else set()
    )

    def tier_of(w: str) -> int:
        s = scores.get(w, 30)
        return 0 if s >= 100 else 1 if s >= 80 else 2 if s >= 50 else 3

    made: list[dict] = []
    cur_date = date.fromisoformat(args.start_date)
    cur_num = args.start_number
    t_idx = 0
    consecutive_fails = 0

    while len(made) < args.puzzles:
        if consecutive_fails >= 2 * len(templates):
            print("aborting: no template will host a fresh marquee set")
            break
        tmpl_path = templates[t_idx % len(templates)]
        t_idx += 1
        grid = json.loads(Path(tmpl_path).read_text())
        slots = G.extract_slots(grid)
        pairs, singles = symmetric_marquees(grid, slots, args.min_marquee_len)

        t0 = time.time()
        solved = None
        featured: list[str] = []
        pin_filler = G.Filler(slots, pool, len(sat_list))
        for attempt in range(args.attempts_per_puzzle):
            if time.time() - t0 > args.time_budget:
                break
            # Crossing-aware pin set: longest-first, each candidate filtered
            # by fixed letters AND by crossing-slot domain survival. Ease
            # theme density as attempts fail: 6 words, then 5, then 4.
            max_m = max(args.min_marquee, args.max_marquee - (attempt // 2))
            picks = build_pins(
                slots, pairs, singles, fresh_by_len, rng,
                args.min_marquee, max_m, filler=pin_filler,
            )
            if picks is None:
                continue
            assert pins_consistent(slots, picks)
            pins = {si: word_to_id[w] for si, w in picks.items()}
            assign = multi_pin_solve(
                slots, pool, len(sat_list), pins, rng, filler=pin_filler,
            )
            if assign is not None:
                solved = assign
                featured = [picks[si] for si in sorted(picks)]
                break

        if solved is None:
            consecutive_fails += 1
            print(f"{Path(tmpl_path).name}: no marquee fill "
                  f"({time.time()-t0:.0f}s), next template", flush=True)
            continue
        consecutive_fails = 0

        # Local-search cleanup, then verify no marquee word was swapped out
        improved, _stats = post_improve(
            slots, pool, solved, tier_of,
            max_iters=12, max_cascade_depth=2, verbose=False,
        )
        if all(w in improved for w in featured):
            solved = improved

        date_str = cur_date.isoformat()
        puzzle = G.to_puzzle(grid, slots, solved, sat_lookup, date_str, cur_num)
        feat_set = set(featured)
        featured_meta = []
        for w in puzzle["words"]:
            if w["answer"] in feat_set:
                w["isMarquee"] = True
                featured_meta.append({
                    "word": w["answer"],
                    "clue": w["clue"],
                    "definition": w.get("definition", ""),
                    "id": w["id"],
                })
        puzzle["featured"] = featured_meta

        sat_n = sum(1 for w in solved if w in sat_set)
        teach_n = sum(1 for w in solved if w in teaching_set)
        unclued = sum(1 for w in puzzle["words"] if not w["clue"])
        fname = f"{len(made)+1:02d}-{'-'.join(featured[:3])}.json"
        (out_dir / fname).write_text(json.dumps(puzzle, indent=2))
        made.append({
            "file": fname, "template": Path(tmpl_path).name,
            "featured": featured, "entries": len(slots),
            "sat": sat_n, "sat_pct": round(100 * sat_n / len(slots), 1),
            "teach": teach_n, "unclued": unclued,
            "date": date_str, "number": cur_num,
        })
        # Featured words now count as used — later puzzles must differ.
        for w in featured:
            fresh_by_len[len(w)].remove(w)
        print(f"puzzle {len(made)}/{args.puzzles} "
              f"[{Path(tmpl_path).name}] featured={featured} "
              f"SAT={sat_n} ({100*sat_n/len(slots):.0f}%) "
              f"unclued={unclued} {time.time()-t0:.0f}s", flush=True)
        cur_date += timedelta(days=1)
        cur_num += 1

    (out_dir / "_index.json").write_text(json.dumps(made, indent=2))
    lines = [
        "# Marquee-themed 15x15 puzzles",
        "",
        "Featured SAT words are pinned into the long symmetric slots",
        "(themed-puzzle convention); every featured word is fresh —",
        "never used in any previously generated puzzle.",
        "",
        "| # | featured | template | entries | SAT | SAT% | unclued |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, m in enumerate(made, 1):
        lines.append(
            f"| {i} | {', '.join(m['featured'])} | {m['template']} "
            f"| {m['entries']} | {m['sat']} | {m['sat_pct']}% "
            f"| {m['unclued']} |"
        )
    (out_dir / "_report.md").write_text("\n".join(lines))
    print(f"\n{len(made)} puzzles -> {out_dir.relative_to(HERE)}/")


if __name__ == "__main__":
    main()
