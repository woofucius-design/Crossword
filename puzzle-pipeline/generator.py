"""
LEXICON puzzle generator — fully-checked (proper interlocking) crosswords.

Every white cell belongs to BOTH an across word and a down word, so every row
and column is packed with real words. The grid is 180°-rotationally symmetric
(NYT convention) and every entry is >= 3 letters.

Pipeline:
  1. build_grid    — backtracking search for a symmetric black-square pattern.
  2. extract_slots — across/down entries and their crossings.
  3. Filler        — constraint solver (maintained domains + forward checking +
                     MRV) that fills the grid; theme slots are restricted to
                     SAT vocabulary so the puzzle features it.

Words come from the full ~270k English dictionary (clean_fill.json) — lowercase
common words only, so proper nouns / pop-culture words cannot appear. The list
is frequency-ordered, so the solver prefers familiar words.

Run:  python3 generator.py --size 9 [--number N] [--date YYYY-MM-DD] [--seed S]
"""
from __future__ import annotations

import argparse
import functools
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from morphology import clue_leaks as _clue_leaks

HERE = Path(__file__).parent
MIN_RUN = 3
NODE_LIMIT = 80_000     # backtracking nodes per restart
RESTARTS = 20           # randomized restarts — escape bad subtrees
EMPTY: frozenset[int] = frozenset()


# ── word lists ───────────────────────────────────────────────────────────────
@functools.lru_cache(maxsize=1)
def load_fill() -> list[str]:
    return json.loads((HERE / "data" / "clean_fill.json").read_text())


@functools.lru_cache(maxsize=1)
def load_sat() -> list[dict]:
    return json.loads((HERE / "data" / "sat_words.json").read_text())


@functools.lru_cache(maxsize=1)
def load_fill_clues() -> dict:
    """Hand-authored fill clues. Merges two files:
      data/fill_clues.json     — original small hand set
      data/fill_clues_ai.json  — AI-authored clues for pool words that no
                                 dictionary source covered (Latin plurals,
                                 abbreviations, proper nouns, irregular
                                 verb forms: ILEA, UTERI, NCO, ELSA, KNELT).
    fill_clues.json wins on conflict (treated as the manual override)."""
    out: dict = {}
    ai_path = HERE / "data" / "fill_clues_ai.json"
    if ai_path.exists():
        out.update(json.loads(ai_path.read_text()))
    path = HERE / "data" / "fill_clues.json"
    if path.exists():
        out.update(json.loads(path.read_text()))
    return out


@functools.lru_cache(maxsize=1)
def load_definitions() -> dict:
    """Word -> {definition, source, pos, ...}. Used to populate the `clue`
    field for fill entries that aren't SAT vocab and don't have a hand
    fill_clue. Source data is built by build_definitions.py +
    enrich_definitions.py."""
    path = HERE / "data" / "definitions.json"
    return json.loads(path.read_text()) if path.exists() else {}


@functools.lru_cache(maxsize=1)
def load_sat_alt_clues() -> dict:
    """SAT word -> list of {text, source} clue candidates. The puzzle
    generator picks one based on the puzzle number so successive runs
    don't all show the same wording."""
    path = HERE / "data" / "sat_alt_clues.json"
    return json.loads(path.read_text()) if path.exists() else {}


@functools.lru_cache(maxsize=1)
def load_sat_synonym_index() -> dict:
    """Fill answer -> {satWords: [...], kind: "synonym"|"short_def",
    display?: "..."}. When a curated SAT-synonym (SHREWD) or squashed
    short-definition phrase (EASYTOGRASP) appears as fill, the puzzle
    clue becomes the SAT word itself, turning fill into vocab review."""
    path = HERE / "data" / "sat_synonym_index.json"
    return json.loads(path.read_text()) if path.exists() else {}


# ── 1. grid construction ─────────────────────────────────────────────────────
def _runs_ok(line: tuple[str, ...]) -> bool:
    run = 0
    for ch in line:
        if ch == "#":
            if 0 < run < MIN_RUN:
                return False
            run = 0
        else:
            run += 1
    return not 0 < run < MIN_RUN


@functools.lru_cache(maxsize=None)
def gap_rows(size: int) -> tuple[tuple[str, ...], ...]:
    """Every row whose white runs are each 0 or >= MIN_RUN."""
    out = []
    for mask in range(1 << size):
        line = tuple("#" if mask & (1 << c) else "." for c in range(size))
        if _runs_ok(line):
            out.append(line)
    return tuple(out)


def _connected(grid: list[list[str]], size: int) -> bool:
    whites = [(r, c) for r in range(size) for c in range(size) if grid[r][c] != "#"]
    if not whites:
        return False
    seen = {whites[0]}
    stack = [whites[0]]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < size
                and 0 <= nc < size
                and grid[nr][nc] != "#"
                and (nr, nc) not in seen
            ):
                seen.add((nr, nc))
                stack.append((nr, nc))
    return len(seen) == len(whites)


def build_grid(
    size: int,
    rng: random.Random,
    min_black_ratio: float = 0.12,
    max_black_ratio: float = 0.30,
) -> list[list[str]] | None:
    """
    A symmetric, fully-checked, connected black-square pattern, or None.
    The row search is biased toward black-heavy rows, which yields choppier
    grids (shorter words) — far easier and cleaner to fill.
    """
    half = size // 2
    odd = size % 2 == 1
    rows: list[tuple[str, ...] | None] = [None] * size
    order = list(gap_rows(size))
    palindromes = [r for r in order if r == r[::-1]]
    budget = [40_000]

    def cols_partial_ok(upto: int) -> bool:
        for c in range(size):
            run = 0
            for r in range(upto + 1):  # known top block
                if rows[r][c] == "#":  # type: ignore[index]
                    if 0 < run < MIN_RUN:
                        return False
                    run = 0
                else:
                    run += 1
            run = 0
            for r in range(size - 1, size - 2 - upto, -1):  # known bottom block
                if rows[r][c] == "#":  # type: ignore[index]
                    if 0 < run < MIN_RUN:
                        return False
                    run = 0
                else:
                    run += 1
        return True

    def finalize() -> list[list[str]] | None:
        grid = [list(rows[r]) for r in range(size)]  # type: ignore[arg-type]
        for c in range(size):
            if not _runs_ok(tuple(grid[r][c] for r in range(size))):
                return None
        black = sum(row.count("#") for row in grid)
        cells = size * size
        if not (min_black_ratio * cells <= black <= max_black_ratio * cells):
            return None
        if not _connected(grid, size):
            return None
        return grid

    def place(r: int) -> list[list[str]] | None:
        budget[0] -= 1
        if budget[0] <= 0:
            return None
        if r == half:
            if odd:
                for mid in palindromes:
                    rows[half] = mid
                    grid = finalize()
                    if grid is not None:
                        return grid
                rows[half] = None
                return None
            return finalize()
        local = order[:]
        rng.shuffle(local)  # diversify each subtree
        for row in local:
            rows[r] = row
            rows[size - 1 - r] = row[::-1]
            if cols_partial_ok(r):
                grid = place(r + 1)
                if grid is not None:
                    return grid
        rows[r] = None
        rows[size - 1 - r] = None
        return None

    return place(0)


# ── 2. slots ─────────────────────────────────────────────────────────────────
class Slot:
    __slots__ = ("cells", "direction", "length", "crossings")

    def __init__(self, cells: list[tuple[int, int]], direction: str):
        self.cells = cells
        self.direction = direction
        self.length = len(cells)
        self.crossings: list[tuple[int, int, int]] = []  # (idx here, slot, idx there)


def extract_slots(grid: list[list[str]]) -> list[Slot]:
    size = len(grid)
    slots: list[Slot] = []
    for r in range(size):
        c = 0
        while c < size:
            if grid[r][c] != "#":
                start = c
                while c < size and grid[r][c] != "#":
                    c += 1
                if c - start >= MIN_RUN:
                    slots.append(Slot([(r, x) for x in range(start, c)], "across"))
            else:
                c += 1
    for c in range(size):
        r = 0
        while r < size:
            if grid[r][c] != "#":
                start = r
                while r < size and grid[r][c] != "#":
                    r += 1
                if r - start >= MIN_RUN:
                    slots.append(Slot([(x, c) for x in range(start, r)], "down"))
            else:
                r += 1

    owner: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    for i, slot in enumerate(slots):
        for idx, cell in enumerate(slot.cells):
            owner[cell].append((i, idx))
    for i, slot in enumerate(slots):
        for idx, cell in enumerate(slot.cells):
            for j, jdx in owner[cell]:
                if j != i:
                    slot.crossings.append((idx, j, jdx))
    return slots


# ── 3. constraint solver ─────────────────────────────────────────────────────
class Filler:
    """Maintained-domain forward checking with MRV ordering."""

    def __init__(self, slots: list[Slot], pool: list[str], theme_count: int):
        self.slots = slots
        self.pool = pool
        length_ids: dict[int, set[int]] = defaultdict(set)
        self.pos_index: dict[tuple[int, int, str], set[int]] = defaultdict(set)
        for i, word in enumerate(pool):
            L = len(word)
            length_ids[L].add(i)
            for pos, ch in enumerate(word):
                self.pos_index[(L, pos, ch)].add(i)
        self.length_ids = length_ids
        self.sat_ids = frozenset(range(theme_count))
        self.theme_slots: set[int] = set()
        self.nodes = 0

    def solve(self, rng: random.Random | None = None,
              restarts: int = RESTARTS) -> list[str] | None:
        rng = rng or random.Random(0)
        base: list[set[int]] = []
        for si, slot in enumerate(self.slots):
            dom = set(self.length_ids.get(slot.length, ()))
            if si in self.theme_slots:
                dom &= self.sat_ids
            if not dom:
                return None
            base.append(dom)

        self.nodes = 0
        self.used_ids: set[int] = set()
        for attempt in range(restarts):
            domains = [set(d) for d in base]
            assign: list[int | None] = [None] * len(self.slots)
            self.used_ids.clear()
            self.nodes = 0
            # restart 0 = pure frequency order (cleanest fill); later restarts
            # randomize value order to break out of unsolvable subtrees.
            if self._bt(domains, assign, rng, noisy=attempt > 0):
                return [self.pool[w] for w in assign]  # type: ignore[index]
        return None

    def _bt(self, domains: list[set[int]], assign: list[int | None],
            rng: random.Random, noisy: bool) -> bool:
        target, best = -1, 1 << 30
        for si in range(len(self.slots)):
            if assign[si] is None and len(domains[si]) < best:
                best, target = len(domains[si]), si
        if target == -1:
            return True

        cands = list(domains[target])
        if noisy:
            rng.shuffle(cands)
        else:
            cands.sort()  # pool id == frequency order
        for wid in cands:
            if wid in self.used_ids:  # cheap dedup — no domain mutation needed
                continue
            self.nodes += 1
            if self.nodes > NODE_LIMIT:
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
                    (self.slots[sj].length, idx_j, word[idx_i]), EMPTY
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


def choose_theme_slots(
    slots: list[Slot], sat_by_len: dict[int, int], target: int, rng: random.Random
) -> set[int]:
    """Pick up to `target` mutually non-crossing slots whose length has SAT words."""
    cross = [{sj for _i, sj, _j in s.crossings} for s in slots]
    eligible = [i for i, s in enumerate(slots) if sat_by_len.get(s.length)]
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
    return set(chosen)


# ── serialization ────────────────────────────────────────────────────────────
def number_grid(grid: list[list[str]]) -> dict[tuple[int, int], int]:
    size = len(grid)
    numbers: dict[tuple[int, int], int] = {}
    n = 0
    for r in range(size):
        for c in range(size):
            if grid[r][c] == "#":
                continue
            sa = (c == 0 or grid[r][c - 1] == "#") and (
                c + 1 < size and grid[r][c + 1] != "#"
            )
            sd = (r == 0 or grid[r - 1][c] == "#") and (
                r + 1 < size and grid[r + 1][c] != "#"
            )
            if sa or sd:
                n += 1
                numbers[(r, c)] = n
    return numbers


def to_puzzle(grid, slots, assign, sat_lookup, date, number):
    size = len(grid)
    numbers = number_grid(grid)
    solution = [
        [grid[r][c] if grid[r][c] == "#" else "" for c in range(size)]
        for r in range(size)
    ]
    fill_clues = load_fill_clues()
    definitions = load_definitions()
    alt_clues = load_sat_alt_clues()
    syn_index = load_sat_synonym_index()
    words = []
    for si, slot in enumerate(slots):
        answer = assign[si]
        for idx, (r, c) in enumerate(slot.cells):
            solution[r][c] = answer[idx]
        r0, c0 = slot.cells[0]
        sat = sat_lookup.get(answer)
        # Clue priority for fill answers:
        #   SAT vocab          -> rotate among alt clues by puzzle number
        #   SAT synonym        -> "Sat-word" so the fill teaches vocab too
        #   hand fill_clue     -> editor override (data/fill_clues.json)
        #   sourced definition -> Webster/WordNet/inflection/abbrev/Roman
        #   none               -> empty
        alt_texts: list[str] = []
        if sat:
            # Featured vocab teaches the tested meaning: the curated bank
            # clue leads the rotation, then modern (non-Webster) alts —
            # Webster's archaic senses (RUE the plant, QUALM 'Sickness')
            # go last so they only appear as variety, never the default.
            pool_clues = [{"text": sat["clue"], "source": "sat"}]
            alts = alt_clues.get(answer, [])
            ranked = [a for a in alts if a.get("source") != "webster"] + [
                a for a in alts if a.get("source") == "webster"
            ]
            for a in ranked:
                if a["text"] != sat["clue"]:
                    pool_clues.append(a)
            usable = [
                p for p in pool_clues if not _clue_leaks(answer, p["text"])
            ] or pool_clues[:1]
            # Rotate by puzzle number for cross-puzzle variety, but only
            # within the curated clue + first two modern alts.
            head = usable[: min(3, len(usable))]
            chosen = head[number % len(head)]
            clue = chosen["text"]
            source = "sat" if chosen["source"] == "sat" else f"sat:{chosen['source']}"
            # Remaining usable clues ride along for the app: variety on
            # replay, or a hint mechanic (reveal another clue instead of
            # revealing letters).
            alt_texts = [p["text"] for p in usable if p is not chosen][:4]
            definition = sat["definition"]
        elif answer in syn_index:
            tie = syn_index[answer]
            sat_word_for_clue = tie["satWords"][0]
            if tie["kind"] == "short_def":
                # Answer is a phrase that defines the headword — exact
                # meaning, no qualifier needed.
                clue = sat_word_for_clue.title()
                shown = tie.get("display", answer)
                definition = f"“{shown}” defines {sat_word_for_clue.lower()}"
            else:
                # Loose one-word synonym: crossword convention marks a
                # not-quite-exact clue with '?'.
                clue = sat_word_for_clue.title() + "?"
                definition = f"Synonym of {sat_word_for_clue.lower()}"
            source = f"sat_{tie['kind']}"
        elif answer in fill_clues:
            clue = fill_clues[answer]
            definition = ""
            source = "hand"
        elif answer in definitions:
            d = definitions[answer]
            # Try primary, then every alternate, picking the first that
            # doesn't leak the answer's root. build_definitions promotes
            # non-leaking sources to primary at build time, so this loop
            # only walks more when ALL stored sources leak for this word
            # (rare — onomatopoeia, very self-referential dictionary
            # entries like AAHED). In that case we blank rather than
            # ship a giveaway.
            chosen = None
            for cand_dict in [d] + d.get("alternates", []):
                cand = cand_dict.get("definition", "")
                if cand and not _clue_leaks(answer, cand):
                    chosen = cand_dict
                    break
            if chosen:
                clue = chosen["definition"]
                definition = chosen["definition"]
                source = chosen.get("source", "definition")
            else:
                clue = ""
                definition = ""
                source = ""
        else:
            clue = ""
            definition = ""
            source = ""
        entry = {
            "id": f"{numbers[(r0, c0)]}{'A' if slot.direction == 'across' else 'D'}",
            "number": numbers[(r0, c0)],
            "direction": slot.direction,
            "row": r0,
            "col": c0,
            "length": slot.length,
            "answer": answer,
            "clue": clue,
            "isSATVocab": bool(sat),
            "isSATSynonym": (not sat) and answer in syn_index,
        }
        if alt_texts:
            entry["altClues"] = alt_texts
        if entry["isSATSynonym"]:
            entry["satSynonymOf"] = syn_index[answer]["satWords"]
            entry["satTeachingKind"] = syn_index[answer]["kind"]
        if definition:
            entry["definition"] = definition
        if source:
            entry["clueSource"] = source
        words.append(entry)
    words.sort(key=lambda w: (w["number"], w["direction"]))
    return {
        "date": date,
        "number": number,
        "size": {"rows": size, "cols": size},
        "solution": solution,
        "cells": {f"{r},{c}": {"number": numbers[(r, c)]} for (r, c) in numbers},
        "words": words,
    }


# ── orchestration ────────────────────────────────────────────────────────────
def generate(
    size: int, date: str, number: int, seed: int, theme_target: int
) -> dict:
    sat = load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    sat_list = [w["word"] for w in sat if len(w["word"]) <= size]
    sat_by_len: dict[int, int] = defaultdict(int)
    for w in sat_list:
        sat_by_len[len(w)] += 1
    fill = load_fill()
    pool = sat_list + [w for w in fill if w not in sat_lookup]
    rng = random.Random(seed)

    for attempt in range(1, 4001):
        grid = build_grid(size, rng)
        if grid is None:
            continue
        slots = extract_slots(grid)
        filler = Filler(slots, pool, len(sat_list))
        for _try in range(8):
            filler.theme_slots = choose_theme_slots(
                slots, sat_by_len, theme_target, rng
            )
            if len(filler.theme_slots) < theme_target:
                break
            assign = filler.solve(rng)
            if assign is not None:
                theme = sum(1 for w in assign if w in sat_lookup)
                print(
                    f"solved: {size}x{size}, grid attempt {attempt}, "
                    f"{len(slots)} entries, {theme} SAT words, "
                    f"{filler.nodes} nodes",
                    file=sys.stderr,
                )
                return to_puzzle(grid, slots, assign, sat_lookup, date, number)
    raise SystemExit("no puzzle found — loosen constraints")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=9)
    ap.add_argument("--date", default="2026-05-22")
    ap.add_argument("--number", type=int, default=48)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--theme", type=int, default=5)
    args = ap.parse_args()

    puzzle = generate(args.size, args.date, args.number, args.seed, args.theme)
    out = HERE / "output" / f"{args.date}.json"
    out.write_text(json.dumps(puzzle, indent=2))

    print(file=sys.stderr)
    for row in puzzle["solution"]:
        print(" ".join("." if ch == "#" else ch for ch in row), file=sys.stderr)
    print(file=sys.stderr)
    sat = [w for w in puzzle["words"] if w["isSATVocab"]]
    fill = [w for w in puzzle["words"] if not w["isSATVocab"]]
    print(f"SAT vocab ({len(sat)}): {', '.join(w['answer'] for w in sat)}", file=sys.stderr)
    print(f"Fill ({len(fill)}): {', '.join(w['answer'] for w in fill)}", file=sys.stderr)
    print(f"written -> {out.relative_to(HERE)}", file=sys.stderr)


if __name__ == "__main__":
    main()
