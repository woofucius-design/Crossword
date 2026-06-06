"""
Seed-and-discover SAT crossword generator.

Replaces the brittle "force 5 SAT words at fixed positions" approach. We seed
ONE chosen SAT word into the puzzle and let the solver discover the rest:

  - Pin the seed SAT word in a random slot of matching length.
  - The standard Filler iterates candidates in pool-ID order; since SAT word
    IDs are 0..29 (below all fill IDs), they're already tried first wherever
    they fit. We just need to TRY OFTEN — most slots' letter constraints
    don't admit any SAT word, but some do.
  - Generate many independent candidates per featured word (different random
    seeds + noisy value ordering on restarts) and keep the candidate that
    packs in the most SAT vocab with the cleanest fill.

Output: one puzzle per featured SAT word (~26 puzzles, given the template).
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


def seed_solve(
    slots: list[G.Slot],
    pool: list[str],
    sat_count: int,
    seed_slot: int,
    seed_word_id: int,
    rng: random.Random,
    restarts: int = 4,
) -> list[str] | None:
    """One full solve with a single SAT word pinned at seed_slot."""
    filler = SatBiasedFiller(slots, pool, sat_count)
    base: list[set[int]] = []
    for si, slot in enumerate(filler.slots):
        dom = set(filler.length_ids.get(slot.length, ()))
        if si == seed_slot:
            if seed_word_id not in dom:
                return None
            dom = {seed_word_id}
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


class SatBiasedFiller(G.Filler):
    """Forward-checking solver with SAT-biased variable ordering.

    Standard Filler uses pure MRV (smallest domain first). That picks slots
    purely by constraint tightness, with no regard for SAT-ness, so SAT words
    rarely get a chance to commit before MRV greedily fills constrained
    corners with fill words.

    Here we split the candidate-slot pool: slots whose domain still admits
    an UNUSED SAT word are explored first (MRV within that subset). Only
    when no SAT-eligible slot remains do we fall back to MRV on all slots.
    Combined with value ordering (SAT IDs 0..29 sort before fill IDs), this
    "weighs SAT heavily" — the search commits SAT words wherever they fit
    before chasing fill.
    """

    def _bt(self, domains, assign, rng, noisy):
        # MRV with SAT-eligibility as the tie-breaker: among slots with the
        # smallest domain, prefer one that still admits an unused SAT word.
        target, best, target_is_sat = -1, 1 << 30, False
        for si in range(len(self.slots)):
            if assign[si] is not None:
                continue
            d = domains[si]
            n = len(d)
            if n > best:
                continue
            sat_eligible = any(
                (wid in d and wid not in self.used_ids) for wid in self.sat_ids
            )
            if n < best or (sat_eligible and not target_is_sat):
                best, target, target_is_sat = n, si, sat_eligible
        if target == -1:
            return True

        cands = list(domains[target])
        if noisy:
            rng.shuffle(cands)
        else:
            cands.sort()  # SAT IDs (0..29) come before fill IDs
        for wid in cands:
            if wid in self.used_ids:
                continue
            self.nodes += 1
            if self.nodes > G.NODE_LIMIT:
                return False
            assign[target] = wid
            self.used_ids.add(wid)
            word = self.pool[wid]
            saved: list[tuple[int, set[int]]] = []
            ok = True
            for idx_i, sj, idx_j in self.slots[target].crossings:
                if assign[sj] is not None:
                    continue
                allowed = self.pos_index.get(
                    (self.slots[sj].length, idx_j, word[idx_i]), G.EMPTY
                )
                pruned = domains[sj] & allowed
                if len(pruned) != len(domains[sj]):
                    saved.append((sj, domains[sj]))
                    domains[sj] = pruned
                if not pruned:
                    ok = False
                    break
            if ok and self._bt(domains, assign, rng, noisy):
                return True
            for sj, dom in reversed(saved):
                domains[sj] = dom
            self.used_ids.discard(wid)
            assign[target] = None
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", type=int, default=10,
                    help="independent solves per featured SAT word")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--start-date", default="2026-05-23")
    ap.add_argument("--start-number", type=int, default=49)
    ap.add_argument("--time-budget", type=float, default=120.0,
                    help="seconds before we stop trying candidates for one word")
    ap.add_argument("--limit", type=int, default=0,
                    help="cap on number of featured-word puzzles (0 = no cap)")
    ap.add_argument("--curated", type=int, default=0,
                    help="only seed from the first N entries in sat_words.json "
                         "(the hand-curated headliners). 0 = use all seedable.")
    args = ap.parse_args()

    grid = json.loads((G.HERE / "data" / "template_15.json").read_text())
    slots = G.extract_slots(grid)
    available_lengths = {s.length for s in slots}
    sat = G.load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    sat_list = [w["word"] for w in sat]
    sat_set = set(sat_list)
    fill = G.load_fill()
    pool = sat_list + [w for w in fill if w not in sat_lookup]
    word_to_id = {w: i for i, w in enumerate(pool)}
    scores = load_scores()

    by_len: dict[int, list[int]] = defaultdict(list)
    for i, s in enumerate(slots):
        by_len[s.length].append(i)

    # SAT words we can actually seed (their length must exist as a slot)
    seed_pool = sat_list[: args.curated] if args.curated else sat_list
    seedable = [w for w in seed_pool if len(w) in available_lengths]
    skipped_n = len(seed_pool) - len(seedable)
    print(
        f"SAT bank: {len(sat_list):,} total, "
        f"seeding from {len(seed_pool):,} ({skipped_n} skipped for no-slot)",
        flush=True,
    )

    if args.limit:
        seedable = seedable[: args.limit]

    rng = random.Random(args.seed)
    cur_date = date.fromisoformat(args.start_date)
    cur_num = args.start_number
    summary: list[dict] = []

    for p, seed_word in enumerate(seedable):
        print(f"\n=== puzzle {p + 1}/{len(seedable)}  seed={seed_word} ===", flush=True)
        seed_wid = word_to_id[seed_word]
        best_assign = None
        best_metrics: tuple[int, float, int, int] = (-1, 0.0, 0, 0)
        # metrics tuple: (sat_count, avg_score, weak_count [neg], cand_idx)
        t_total = time.time()
        for cand in range(args.candidates):
            if time.time() - t_total > args.time_budget:
                print(f"  time budget reached after cand {cand}", flush=True)
                break
            seed_slot = rng.choice(by_len[len(seed_word)])
            t0 = time.time()
            assign = seed_solve(
                slots, pool, len(sat_list),
                seed_slot, seed_wid, rng,
                restarts=3,
            )
            dt = time.time() - t0
            if assign is None:
                print(f"  cand {cand + 1}: fail in {dt:.1f}s", flush=True)
                continue
            ws = [scores.get(w, 30) for w in assign]
            avg = sum(ws) / len(ws)
            weak = sum(1 for s in ws if s < 50)
            sat_n = sum(1 for w in assign if w in sat_set)
            metrics = (sat_n, avg, -weak, cand)
            print(
                f"  cand {cand + 1}: SOLVED {dt:.1f}s "
                f"SAT={sat_n} avg={avg:.1f} weak={weak}",
                flush=True,
            )
            if metrics > best_metrics:
                best_metrics = metrics
                best_assign = assign

        if best_assign is None:
            print(f"  ! no fill found for seed {seed_word}, skipping")
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
        print(
            f"  -> {out.relative_to(G.HERE)}  "
            f"SAT={best_metrics[0]} ({sat_in_puzzle})  "
            f"avg={best_metrics[1]:.1f} weak={-best_metrics[2]}"
        )
        summary.append({
            "date": date_str,
            "number": cur_num,
            "seed": seed_word,
            "sat_count": best_metrics[0],
            "sat_in_puzzle": sat_in_puzzle,
            "avg_score": best_metrics[1],
            "weak_fill": -best_metrics[2],
        })
        cur_date += timedelta(days=1)
        cur_num += 1

    print("\n=== summary ===")
    sat_totals: dict[str, int] = defaultdict(int)
    for s in summary:
        print(
            f"{s['date']} #{s['number']:<3} seed={s['seed']:<11} "
            f"SAT={s['sat_count']} avg={s['avg_score']:.1f} "
            f"weak={s['weak_fill']}  ({', '.join(s['sat_in_puzzle'])})"
        )
        for w in s["sat_in_puzzle"]:
            sat_totals[w] += 1
    print(f"\n{len(summary)}/{len(seedable)} puzzles generated")
    print(f"SAT word coverage (puzzles each word appears in):")
    for w in sat_list:
        print(f"  {w:<12} {sat_totals.get(w, 0)}")


if __name__ == "__main__":
    main()
