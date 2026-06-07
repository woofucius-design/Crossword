"""
Surveys 11x11 grid templates to find ones that fill cleanly with the
seed-and-discover SAT generator. Builds a library of varied, high-quality
templates so the puzzle series doesn't all share one layout.

For each candidate template:
  1. Build a symmetric black-square pattern (generator.build_grid).
  2. Run K seed solves with different SAT seeds + random slot positions.
  3. Record: solve rate, avg SAT density, avg tier-3 fill count, avg score.
  4. Capture structural features: black %, word count, length distribution.

Top performers are saved to data/templates_11/template_<rank>.json and a
markdown report data/templates_11/README.md summarizes the patterns we see
in the winners.
"""
from __future__ import annotations

import json
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

import generator as G
from pick_15 import load_scores
from seed_15 import seed_solve


HERE = Path(__file__).parent
OUT_DIR = HERE / "data" / "templates_11"
SIZE = 11
N_CANDIDATES = 60       # templates to generate
SEEDS_PER_TEMPLATE = 4  # SAT-word seeds to test per template
SOLVE_TIME_BUDGET = 6.0 # seconds per individual solve attempt


def template_stats(grid: list[list[str]]) -> dict:
    size = len(grid)
    black = sum(1 for row in grid for c in row if c == "#")
    white = size * size - black
    slots = G.extract_slots(grid)
    by_len = Counter(s.length for s in slots)
    return {
        "size": size,
        "black": black,
        "white": white,
        "black_pct": 100 * black / (size * size),
        "entries": len(slots),
        "length_counts": dict(by_len),
        "max_length": max(by_len),
        "len3_share": by_len.get(3, 0) / len(slots) if slots else 0,
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
) -> dict:
    """Run a few seed solves on this template, return aggregated metrics."""
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
        if assign is None or dt > SOLVE_TIME_BUDGET:
            continue
        solves += 1
        sat_n = sum(1 for w in assign if w in sat_set)
        tier3_n = sum(
            1 for w in assign
            if w not in sat_set and w not in acceptable_fill
        )
        ws = [scores.get(w, 30) for w in assign]
        sat_counts.append(sat_n)
        tier3_counts.append(tier3_n)
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
    G.NODE_LIMIT = 80_000  # quick test, not full solve budget
    OUT_DIR.mkdir(exist_ok=True)
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

    # Curated SAT seeds for testing — well-distributed lengths
    test_seeds = ["LUCID", "OPULENT", "DEFT", "EPHEMERAL", "BENEVOLENT"]
    # Filter to those that exist in pool
    test_seeds = [w for w in test_seeds if w in word_to_id]

    print(f"surveying {N_CANDIDATES} {SIZE}x{SIZE} templates "
          f"× {SEEDS_PER_TEMPLATE} seed solves each", flush=True)
    rng = random.Random(2026)
    candidates: list[dict] = []

    for i in range(N_CANDIDATES):
        # Vary black-square ratio to get structural diversity
        min_black = rng.uniform(0.16, 0.22)
        max_black = min_black + rng.uniform(0.04, 0.08)
        t0 = time.time()
        grid = G.build_grid(SIZE, rng, min_black, max_black)
        if grid is None:
            continue
        stats = template_stats(grid)
        ascii_grid = render_ascii(grid)
        # Skip duplicates
        if any(c["ascii"] == ascii_grid for c in candidates):
            continue
        seeds_to_test = (
            test_seeds[: SEEDS_PER_TEMPLATE]
            if len(test_seeds) >= SEEDS_PER_TEMPLATE
            else test_seeds
        )
        metrics = test_template(
            grid, pool, sat_list, sat_set, word_to_id,
            acceptable_fill, scores, seeds_to_test, rng,
        )
        elapsed = time.time() - t0
        candidates.append({
            "idx": i,
            "grid": grid,
            "ascii": ascii_grid,
            **stats,
            **metrics,
            "build_test_s": elapsed,
        })
        print(
            f"  {len(candidates):>2}. black={stats['black_pct']:.0f}% "
            f"entries={stats['entries']} max_len={stats['max_length']} "
            f"len3={stats['length_counts'].get(3, 0)}  "
            f"solves={metrics['solves']}/{len(seeds_to_test)} "
            f"sat={metrics['avg_sat']:.1f} tier3={metrics['avg_tier3']:.1f} "
            f"avg-score={metrics['avg_score']:.0f}  "
            f"({elapsed:.0f}s)",
            flush=True,
        )

    print(f"\ngenerated {len(candidates)} unique templates", flush=True)
    # Rank: solve rate, then SAT density, then minimize tier3, then high score
    candidates.sort(
        key=lambda c: (
            -c["solve_rate"],
            -c["avg_sat"],
            c["avg_tier3"],
            -c["avg_score"],
        )
    )

    # Save top 10
    keep = candidates[:10]
    for rank, c in enumerate(keep, 1):
        path = OUT_DIR / f"template_{rank:02d}.json"
        path.write_text(json.dumps(c["grid"]))

    # Write a markdown report
    report_lines = [
        f"# 11x11 Template Library — top {len(keep)} by fillability\n",
        f"_Survey of {len(candidates)} unique random templates, each tested ",
        f"with {SEEDS_PER_TEMPLATE} different SAT seeds._\n",
        "## Ranking criteria\n",
        "1. Solve rate (did the seed solver land any valid fill?)",
        "2. Average SAT density across solves",
        "3. Minimum tier-3 fill (random acronyms)",
        "4. Highest average Broda fill score\n",
        "## Top templates\n",
        "| Rank | Black % | Entries | Max len | Len-3 slots | Solve rate | "
        "Avg SAT | Avg tier 3 | Avg score |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for rank, c in enumerate(keep, 1):
        report_lines.append(
            f"| {rank} | {c['black_pct']:.0f}% | {c['entries']} | "
            f"{c['max_length']} | {c['length_counts'].get(3, 0)} | "
            f"{c['solve_rate']*100:.0f}% | {c['avg_sat']:.1f} | "
            f"{c['avg_tier3']:.1f} | {c['avg_score']:.0f} |"
        )
    report_lines.append("\n## Grids\n")
    for rank, c in enumerate(keep, 1):
        report_lines.append(f"### Template {rank:02d}  "
                            f"(template_{rank:02d}.json)\n")
        report_lines.append("```")
        report_lines.append(c["ascii"])
        report_lines.append("```\n")

    # Pattern analysis: compare top half to bottom half
    if len(candidates) >= 6:
        top = candidates[: len(candidates) // 3]
        bot = candidates[-len(candidates) // 3 :]
        def avg(seq: list[dict], key: str) -> float:
            return sum(s[key] for s in seq) / max(len(seq), 1)
        report_lines.append("## Pattern analysis (top third vs bottom third)\n")
        report_lines.append("| Metric | Top | Bottom | Delta |")
        report_lines.append("|---|---|---|---|")
        for key, label in [
            ("black_pct", "Black square %"),
            ("entries", "Word count"),
            ("max_length", "Max entry length"),
            ("len3_share", "Length-3 slot share"),
        ]:
            t = avg(top, key)
            b = avg(bot, key)
            report_lines.append(f"| {label} | {t:.2f} | {b:.2f} | {t - b:+.2f} |")

    (OUT_DIR / "README.md").write_text("\n".join(report_lines))
    print(f"\nsaved {len(keep)} templates -> {OUT_DIR.relative_to(HERE)}/")
    print(f"report -> {(OUT_DIR / 'README.md').relative_to(HERE)}")


if __name__ == "__main__":
    main()
