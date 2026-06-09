"""
Post-solve quality improver — reduces tier-3 entries via local search.

The solver in generator.py backtracks on INFEASIBILITY only, never on
QUALITY: once it finds a valid full assignment, it returns even if many
slots ended up filled with tier-3 entries (LAIKA, RAFIKI, UCANT-class).
The picker in seed_15.py works around this by sampling K candidates and
keeping the best, but each individual candidate's tier-3 count is fixed.

This module does a cheap iterative-improvement pass on a completed
assignment:

  for each tier-3 entry W at slot S, in some order:
      for each tier-<=2 candidate W' that fits S's length:
          - 0-cascade: if W' matches the current letters at every
            crossing of S, swap W -> W' directly.
          - 1-cascade: otherwise compute which crossing slots would
            need to change (positions where W' differs from W). For
            each such crossing Sc, search for a replacement Wc' with
            the required letter at the cross point AND matching every
            OTHER crossing of Sc that's still fixed, AND of tier no
            worse than the current Wc. If one is found at every
            affected crossing, apply the multi-swap.

We stop when a full pass finds no improvement, or after N iterations.

This is intentionally limited: depth-1 cascade only, no deeper backtrack.
Catches the easy cases where a single tier-3 entry stranded itself.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable

import generator as G


def _build_indices(slots: list[G.Slot], pool: list[str]):
    """Pre-compute pool indexes the post-improver needs (same shape as
    Filler's, recomputed here so we don't depend on Filler internals)."""
    length_ids: dict[int, list[int]] = defaultdict(list)
    pos_index: dict[tuple[int, int, str], set[int]] = defaultdict(set)
    for i, w in enumerate(pool):
        L = len(w)
        length_ids[L].append(i)
        for pos, ch in enumerate(w):
            pos_index[(L, pos, ch)].add(i)
    return length_ids, pos_index


def _slot_pos_index(slots: list[G.Slot]):
    """For each (slot_id, position) -> (crossing_slot_id, position_in_crossing)
    so we can quickly find the cell shared between a slot and any crossing."""
    out: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    for si, slot in enumerate(slots):
        for idx_here, sj, idx_there in slot.crossings:
            out[(si, idx_here)].append((sj, idx_there))
    return out


def post_improve(
    slots: list[G.Slot],
    pool: list[str],
    assign: list[str],
    tier_of: Callable[[str], int],
    max_iters: int = 20,
    verbose: bool = False,
) -> tuple[list[str], dict]:
    """Iteratively reduce tier-3 entries by 1-step cascade swaps.

    Returns (new_assign, stats) where stats is a dict with counts.
    """
    length_ids, pos_index = _build_indices(slots, pool)
    word_to_id = {w: i for i, w in enumerate(pool)}
    cross_lookup = _slot_pos_index(slots)
    assign = list(assign)
    iters = 0
    swaps_0 = 0
    swaps_1 = 0
    while iters < max_iters:
        iters += 1
        improved_this_pass = False
        # Find all tier-3 slots
        bad_slots = [
            (si, w) for si, w in enumerate(assign) if tier_of(w) == 3
        ]
        # Sort by slot length descending — longer slots have more crossings,
        # more leverage to reduce overall tier-3 count.
        bad_slots.sort(key=lambda p: -len(p[1]))

        for si, current_word in bad_slots:
            slot = slots[si]
            L = slot.length

            # Find all words that fit the slot's current letter pattern
            # (i.e., satisfy ALL crossings as currently assigned).
            pattern_domain = set(length_ids[L])
            for idx in range(L):
                # For each position, what letter is required by crossings?
                # Take it from the current assign of any crossing slot.
                fixed_letter: str | None = None
                for sj, idx_in_sj in cross_lookup.get((si, idx), []):
                    fixed_letter = assign[sj][idx_in_sj]
                    break
                if fixed_letter is None:
                    continue
                pattern_domain &= pos_index.get((L, idx, fixed_letter), set())

            # Used-IDs set so we don't pick a duplicate.
            used = {word_to_id[w] for j, w in enumerate(assign) if j != si}

            # 0-CASCADE: exact-pattern swap. Try tier <= 2 candidates that
            # match the current letter pattern exactly.
            zero_cand_id = None
            for wid in sorted(pattern_domain):
                if wid in used:
                    continue
                w = pool[wid]
                if w == current_word:
                    continue
                if tier_of(w) >= 3:
                    break  # pool is tier-ordered, no point continuing
                zero_cand_id = wid
                break
            if zero_cand_id is not None:
                new_w = pool[zero_cand_id]
                if verbose:
                    print(f"    0-cascade: slot {si} ({current_word} -> {new_w})")
                assign[si] = new_w
                swaps_0 += 1
                improved_this_pass = True
                break  # restart pass to recompute tier-3 set

            # 1-CASCADE: try W' that don't match current pattern; see if we
            # can also change the affected crossings.
            # Candidate set: all words of length L that are tier <= 2 and
            # match crossings that DON'T need changing.
            cands_for_W = []
            for wid in length_ids[L]:
                if wid in used:
                    continue
                w = pool[wid]
                if w == current_word:
                    continue
                if tier_of(w) >= 3:
                    continue
                cands_for_W.append(wid)
            # Sort: tier-1 candidates first.
            cands_for_W.sort(key=lambda wid: tier_of(pool[wid]))

            applied = False
            for wid_new in cands_for_W:
                w_new = pool[wid_new]
                # Find positions where w_new differs from current_word.
                # At those positions, the crossing slot must be replaced.
                replacements: dict[int, str] = {si: w_new}
                ok = True
                seen_used = set(used)
                seen_used.discard(word_to_id[current_word])
                seen_used.add(wid_new)
                for idx in range(L):
                    if w_new[idx] == current_word[idx]:
                        continue
                    # Find the crossing slot at this position.
                    cross_targets = cross_lookup.get((si, idx), [])
                    if not cross_targets:
                        # No crossing — this means slot has open edge, but
                        # since the grid is fully checked, every cell has
                        # a crossing. So this shouldn't happen.
                        ok = False
                        break
                    sj, idx_in_sj = cross_targets[0]
                    if sj in replacements:
                        # Already replacing this crossing in this attempt
                        # (shouldn't happen if slots are distinct).
                        if replacements[sj][idx_in_sj] != w_new[idx]:
                            ok = False
                            break
                        continue
                    current_Wc = assign[sj]
                    target_tier = tier_of(current_Wc)
                    # Build the required letter pattern for Wc'
                    Lc = slots[sj].length
                    # Wc' must have w_new[idx] at position idx_in_sj
                    domain_c = set(
                        pos_index.get((Lc, idx_in_sj, w_new[idx]), set())
                    )
                    # AND match every OTHER crossing of Sc that's currently
                    # fixed by an unchanged assign.
                    for idxc in range(Lc):
                        if idxc == idx_in_sj:
                            continue
                        # What's the current letter at this cell? It's
                        # whatever the crossing slot at that position says
                        # (or current_Wc itself if no further crossings).
                        cross_other = cross_lookup.get((sj, idxc), [])
                        fixed = None
                        for sk, idxk_in_sk in cross_other:
                            if sk in replacements:
                                fixed = replacements[sk][idxk_in_sk]
                            else:
                                fixed = assign[sk][idxk_in_sk]
                            break
                        if fixed is not None:
                            domain_c &= pos_index.get(
                                (Lc, idxc, fixed), set()
                            )
                            if not domain_c:
                                break
                    # Pick the best (lowest-ID) candidate of tier <= target.
                    Wc_new_id = None
                    for wid_c in sorted(domain_c):
                        if wid_c in seen_used:
                            continue
                        wc = pool[wid_c]
                        if wc == current_Wc:
                            continue
                        if tier_of(wc) > target_tier:
                            break  # pool tier-ordered
                        Wc_new_id = wid_c
                        break
                    if Wc_new_id is None:
                        ok = False
                        break
                    replacements[sj] = pool[Wc_new_id]
                    seen_used.add(Wc_new_id)
                if ok and len(replacements) >= 2:
                    # Apply if at least one crossing actually changed and
                    # the global tier-3 count strictly decreased.
                    old_tier3 = sum(
                        1 for j, w in enumerate(assign) if tier_of(w) == 3
                    )
                    new_tier3 = sum(
                        1
                        for j, w in enumerate(assign)
                        if (j not in replacements and tier_of(w) == 3)
                        or (j in replacements and tier_of(replacements[j]) == 3)
                    )
                    if new_tier3 < old_tier3:
                        if verbose:
                            print(
                                f"    1-cascade: slot {si} ({current_word} "
                                f"-> {w_new}) +{len(replacements)-1} crossings "
                                f"changed, tier3 {old_tier3} -> {new_tier3}"
                            )
                        for sj, w_new_sj in replacements.items():
                            assign[sj] = w_new_sj
                        swaps_1 += 1
                        applied = True
                        break
            if applied:
                improved_this_pass = True
                break  # restart pass

        if not improved_this_pass:
            break

    stats = {
        "iterations": iters,
        "swaps_0_cascade": swaps_0,
        "swaps_1_cascade": swaps_1,
    }
    return assign, stats
