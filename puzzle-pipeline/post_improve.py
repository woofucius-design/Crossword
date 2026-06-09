"""
Post-solve quality improver — reduces tier-3 entries via local search.

The CSP solver in generator.py backtracks on INFEASIBILITY only, never on
QUALITY: it returns the first valid full assignment, even if it stranded
tier-3 entries in spots a deeper search would have found cleaner. This
module runs after the solver and tries local swaps to reduce tier-3
count without invalidating any crossing.

Cascade depth:
  depth 0 — only swap the tier-3 entry, all crossing letters must stay.
            Almost never fires: if a tier-≤2 word matched the current
            pattern exactly, the solver would have picked it.
  depth 1 — swap the tier-3 entry W for W', and for each crossing where
            W' differs from W, swap the crossing slot too. The crossing
            replacement must match every OTHER fixed crossing exactly.
  depth 2 — same as 1, but the crossing replacement may itself propagate
            to one of ITS crossings, recursing one more level.
  ...

Cost grows with depth: per top-level candidate, we may try O(N_cands^d)
sub-recursions. We bound depth at MAX_CASCADE_DEPTH (default 2) and limit
candidates per slot.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable

import generator as G


def _build_indices(slots: list[G.Slot], pool: list[str]):
    length_ids: dict[int, list[int]] = defaultdict(list)
    pos_index: dict[tuple[int, int, str], set[int]] = defaultdict(set)
    for i, w in enumerate(pool):
        L = len(w)
        length_ids[L].append(i)
        for pos, ch in enumerate(w):
            pos_index[(L, pos, ch)].add(i)
    return length_ids, pos_index


def _slot_pos_index(slots: list[G.Slot]):
    out: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    for si, slot in enumerate(slots):
        for idx_here, sj, idx_there in slot.crossings:
            out[(si, idx_here)].append((sj, idx_there))
    return out


def _find_swap(
    slot_id: int,
    pinned_letters: dict[int, str],
    depth_budget: int,
    changes: dict[int, int],
    target_tier: int,
    *,
    slots: list[G.Slot],
    pool: list[str],
    assign: list[str],
    tier_of: Callable[[str], int],
    length_ids: dict[int, list[int]],
    pos_index: dict[tuple[int, int, str], set[int]],
    cross_lookup: dict[tuple[int, int], list[tuple[int, int]]],
    word_to_id: dict[str, int],
    cand_limit: int = 200,
    budget: list[int] | None = None,
) -> dict[int, int] | None:
    """Find a word for slot_id that satisfies pinned_letters at the given
    positions, plus any cross letters currently in `assign` at positions
    that won't propagate (depth_budget controls how many more cross slots
    we'll let change), AND has tier <= target_tier.

    Returns updated `changes` ({slot_id: word_id}), or None if no swap works.
    """
    Lj = slots[slot_id].length
    current_word = assign[slot_id]
    cur_wid = word_to_id.get(current_word, -1)

    # Build the domain: words of correct length matching pinned letters.
    domain = set(length_ids[Lj])
    for pos, letter in pinned_letters.items():
        domain &= pos_index.get((Lj, pos, letter), set())
    if not domain:
        return None

    in_use = set(changes.values())
    cands = sorted(domain)[:cand_limit]
    for wid in cands:
        if budget is not None:
            if budget[0] <= 0:
                return None
            budget[0] -= 1
        if wid in in_use:
            continue
        if wid == cur_wid:
            continue
        word = pool[wid]
        if tier_of(word) > target_tier:
            # pool ordered tier 1 -> tier 2 -> tier 3; once we cross over,
            # no point continuing through this domain.
            break
        # Propose this swap; verify / propagate at every position.
        new_changes = dict(changes)
        new_changes[slot_id] = wid
        new_in_use = set(new_changes.values())
        ok = True
        for idx in range(Lj):
            if idx in pinned_letters:
                continue
            crosses = cross_lookup.get((slot_id, idx), [])
            if not crosses:
                continue
            sk, idx_in_sk = crosses[0]
            # If sk is in changes already, ensure the new word's letter at
            # idx_in_sk matches what we already committed for sk.
            if sk in new_changes:
                cross_word = pool[new_changes[sk]]
                if cross_word[idx_in_sk] != word[idx]:
                    ok = False
                    break
                continue
            current_cross = assign[sk]
            if current_cross[idx_in_sk] == word[idx]:
                continue  # crossing already satisfies, no change needed
            # Crossing slot must change. Allowed?
            if depth_budget <= 0:
                ok = False
                break
            # Recurse to find a replacement for sk with letter word[idx]
            # at idx_in_sk. The replacement must be no worse than the
            # crossing's current tier.
            sk_target_tier = tier_of(current_cross)
            sub = _find_swap(
                sk,
                pinned_letters={idx_in_sk: word[idx]},
                depth_budget=depth_budget - 1,
                changes=new_changes,
                target_tier=sk_target_tier,
                slots=slots,
                pool=pool,
                assign=assign,
                tier_of=tier_of,
                length_ids=length_ids,
                pos_index=pos_index,
                cross_lookup=cross_lookup,
                word_to_id=word_to_id,
                cand_limit=cand_limit,
                budget=budget,
            )
            if sub is None:
                ok = False
                break
            new_changes = sub
            new_in_use = set(new_changes.values())
        if ok:
            return new_changes
    return None


def post_improve(
    slots: list[G.Slot],
    pool: list[str],
    assign: list[str],
    tier_of: Callable[[str], int],
    max_iters: int = 20,
    max_cascade_depth: int = 2,
    cand_limit: int = 60,
    per_slot_node_budget: int = 50_000,
    verbose: bool = False,
) -> tuple[list[str], dict]:
    """Iteratively reduce tier-3 entries using cascading swaps of depth
    up to `max_cascade_depth`. Each iteration tries to find one improvement;
    if found, applies it and loops. Stops when no improvement or max_iters
    hit."""
    length_ids, pos_index = _build_indices(slots, pool)
    word_to_id = {w: i for i, w in enumerate(pool)}
    cross_lookup = _slot_pos_index(slots)
    assign = list(assign)
    iters = 0
    swaps_by_depth: dict[int, int] = defaultdict(int)

    while iters < max_iters:
        iters += 1
        improved = False
        bad_slots = [
            (si, w) for si, w in enumerate(assign) if tier_of(w) == 3
        ]
        bad_slots.sort(key=lambda p: -len(p[1]))  # longer first

        for si, current_word in bad_slots:
            current_wid = word_to_id.get(current_word, -1)
            base_changes = {si: current_wid} if current_wid >= 0 else {}
            # Try increasing cascade depths so we accept a shallower fix
            # if one exists.
            applied = False
            for depth in range(max_cascade_depth + 1):
                budget = [per_slot_node_budget]
                changes = _find_swap(
                    si,
                    pinned_letters={},
                    depth_budget=depth,
                    changes={},
                    target_tier=2,
                    slots=slots,
                    pool=pool,
                    assign=assign,
                    tier_of=tier_of,
                    length_ids=length_ids,
                    pos_index=pos_index,
                    cross_lookup=cross_lookup,
                    word_to_id=word_to_id,
                    cand_limit=cand_limit,
                    budget=budget,
                )
                if changes is None:
                    continue
                # Verify the swap strictly decreases tier-3 count.
                old_tier3 = sum(
                    1 for j, w in enumerate(assign) if tier_of(w) == 3
                )
                new_tier3 = sum(
                    1 for j, w in enumerate(assign)
                    if (j not in changes and tier_of(w) == 3)
                    or (j in changes and tier_of(pool[changes[j]]) == 3)
                )
                if new_tier3 >= old_tier3:
                    continue
                # Apply.
                for sj, new_wid in changes.items():
                    assign[sj] = pool[new_wid]
                swaps_by_depth[depth] += 1
                if verbose:
                    print(
                        f"    depth-{depth}: slot {si} +{len(changes)-1} "
                        f"crossings, tier3 {old_tier3} -> {new_tier3}"
                    )
                applied = True
                break  # restart with shallower depths next iteration
            if applied:
                improved = True
                break
        if not improved:
            break

    stats = {
        "iterations": iters,
        "swaps_by_depth": dict(swaps_by_depth),
        "total_swaps": sum(swaps_by_depth.values()),
    }
    return assign, stats
