"""
LEXICON puzzle generator.

Proves a complete, valid daily crossword can be built from SAT vocabulary plus
a clean common-word fill, with NO pop-culture words — no proper nouns, brands,
titles, or crosswordese (the design's own sample leans on "ODEA", exactly the
kind of word this avoids).

The layout is freeform interlocking (the style of the design handoff's puzzle,
not a fully-checked American grid): theme answers and fill words are woven
together so every word crosses at least one other and the whole puzzle is one
connected component inside a 10x10 box.

Pipeline:
  1. word_selector — SAT theme words + the clean fill list (build_fill_list.py).
  2. layout        — backtracking-with-restarts placement of words so each new
                     entry crosses the existing structure with no illegal
                     adjacencies.
  3. serialize     — emit the app's Puzzle JSON.

Run:  python3 generator.py [--date YYYY-MM-DD] [--number N] [--seed S]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
SIZE = 10
THEME_TARGET = 6      # SAT words featured in the puzzle
MIN_WORDS = 14        # total entries (theme + fill)
MAX_WORDS = 18
FILL_POOL = 7000      # most-common fill words considered
# Fill stays >= 4 letters: it skips weak 3-letter crosswordese (PRE, ODEA-style
# entries) and keeps every answer a word a student would actually clue.
MIN_FILL_LEN = 4
MAX_FILL_LEN = 7


# ── 1. word selection ────────────────────────────────────────────────────────
def load_words() -> tuple[list[dict], list[str]]:
    sat = json.loads((HERE / "data" / "sat_words.json").read_text())
    fill = json.loads((HERE / "data" / "clean_fill.json").read_text())
    fill = [
        w for w in fill[:FILL_POOL] if MIN_FILL_LEN <= len(w) <= MAX_FILL_LEN
    ]
    return sat, fill


# ── 2. freeform layout ───────────────────────────────────────────────────────
class Placed:
    __slots__ = ("word", "row", "col", "horiz", "is_sat")

    def __init__(self, word: str, row: int, col: int, horiz: bool, is_sat: bool):
        self.word = word
        self.row = row
        self.col = col
        self.horiz = horiz
        self.is_sat = is_sat

    def cells(self) -> list[tuple[int, int]]:
        if self.horiz:
            return [(self.row, self.col + i) for i in range(len(self.word))]
        return [(self.row + i, self.col) for i in range(len(self.word))]


Grid = dict[tuple[int, int], str]


def fits(word: str, row: int, col: int, horiz: bool, grid: Grid) -> int | None:
    """
    Returns the number of crossings if `word` can be legally placed, else None.
    Legal means: inside the box, the cell before/after the word is empty, every
    new (non-crossing) letter has empty perpendicular neighbours, and the word
    crosses the existing structure at least once.
    """
    length = len(word)
    if horiz:
        if col < 0 or col + length > SIZE or not (0 <= row < SIZE):
            return None
        before, after = (row, col - 1), (row, col + length)
    else:
        if row < 0 or row + length > SIZE or not (0 <= col < SIZE):
            return None
        before, after = (row - 1, col), (row + length, col)
    if before in grid or after in grid:
        return None

    crossings = 0
    new_letters = 0
    for i in range(length):
        cell = (row, col + i) if horiz else (row + i, col)
        existing = grid.get(cell)
        if existing is not None:
            if existing != word[i]:
                return None
            crossings += 1
        else:
            new_letters += 1
            r, c = cell
            perp = [(r - 1, c), (r + 1, c)] if horiz else [(r, c - 1), (r, c + 1)]
            if any(p in grid for p in perp):
                return None
    if new_letters == 0:
        return None  # would duplicate an existing word
    return crossings


def all_placements(word: str, grid: Grid) -> list[tuple[int, int, bool, int]]:
    """Every legal (row, col, horiz, crossings) for `word` against the grid."""
    out: list[tuple[int, int, bool, int]] = []
    for (r, c), ch in grid.items():
        for j, wch in enumerate(word):
            if wch != ch:
                continue
            for horiz in (True, False):
                row, col = (r, c - j) if horiz else (r - j, c)
                cross = fits(word, row, col, horiz, grid)
                if cross:
                    out.append((row, col, horiz, cross))
    return out


def commit(word: str, row: int, col: int, horiz: bool, is_sat: bool,
           grid: Grid, placed: list[Placed]) -> None:
    p = Placed(word, row, col, horiz, is_sat)
    for i, cell in enumerate(p.cells()):
        grid[cell] = word[i]
    placed.append(p)


def attempt(
    sat_list: list[str],
    fill_index: dict[tuple[int, int, str], list[str]],
    rng: random.Random,
) -> list[Placed] | None:
    grid: Grid = {}
    placed: list[Placed] = []
    used: set[str] = set()

    theme = rng.sample(sat_list, len(sat_list))
    first = theme.pop(0)
    commit(first, 4, (SIZE - len(first)) // 2, True, True, grid, placed)
    used.add(first)
    remaining_theme = theme[: THEME_TARGET - 1]

    stalls = 0
    while True:
        if not remaining_theme and len(placed) >= MIN_WORDS:
            return placed
        if len(placed) >= MAX_WORDS:
            return placed if not remaining_theme else None

        progress = False

        # 1. seat a theme word if one fits now (prefer the most interlocked spot)
        for sw in list(remaining_theme):
            spots = all_placements(sw, grid)
            if spots:
                spots.sort(key=lambda s: s[3], reverse=True)
                top = [s for s in spots if s[3] == spots[0][3]]
                row, col, horiz, _ = rng.choice(top)
                commit(sw, row, col, horiz, True, grid, placed)
                used.add(sw)
                remaining_theme.remove(sw)
                progress = True
                break

        # 2. otherwise weave in a fill word (also opens crossings for theme)
        if not progress and place_fill(grid, placed, used, fill_index, rng):
            progress = True

        if not progress:
            stalls += 1
            if stalls > 1:
                return None


def place_fill(
    grid: Grid,
    placed: list[Placed],
    used: set[str],
    fill_index: dict[tuple[int, int, str], list[str]],
    rng: random.Random,
) -> bool:
    cells = list(grid.items())
    rng.shuffle(cells)
    for (r, c), ch in cells:
        for horiz in rng.sample([True, False], 2):
            # longer fill first — denser interlock, fewer choppy short entries
            for length in range(MAX_FILL_LEN, MIN_FILL_LEN - 1, -1):
                for j in range(length):
                    cands = fill_index.get((length, j, ch))
                    if not cands:
                        continue
                    for word in rng.sample(cands, min(len(cands), 24)):
                        if word in used:
                            continue
                        row, col = (r, c - j) if horiz else (r - j, c)
                        if fits(word, row, col, horiz, grid):
                            commit(word, row, col, horiz, False, grid, placed)
                            used.add(word)
                            return True
    return False


# ── 3. serialization ─────────────────────────────────────────────────────────
def load_fill_clues() -> dict[str, str]:
    """
    Clues for fill words. In production this step is `clue_writer.py`, which
    asks Claude for clues (see the handoff); for this offline feasibility run a
    curated local dictionary is used. Unknown words are left to be clued later.
    """
    path = HERE / "data" / "fill_clues.json"
    return json.loads(path.read_text()) if path.exists() else {}


def to_puzzle(placed: list[Placed], sat_lookup: dict[str, dict],
              date: str, number: int) -> dict:
    fill_clues = load_fill_clues()
    cells_used = {cell for p in placed for cell in p.cells()}
    min_r = min(r for r, _ in cells_used)
    max_r = max(r for r, _ in cells_used)
    min_c = min(c for _, c in cells_used)
    max_c = max(c for _, c in cells_used)
    off_r = (SIZE - (max_r - min_r + 1)) // 2 - min_r
    off_c = (SIZE - (max_c - min_c + 1)) // 2 - min_c

    grid: list[list[str]] = [["#"] * SIZE for _ in range(SIZE)]
    for p in placed:
        for i, (r, c) in enumerate(p.cells()):
            grid[r + off_r][c + off_c] = p.word[i]

    # standard crossword numbering
    numbers: dict[tuple[int, int], int] = {}
    n = 0
    for r in range(SIZE):
        for c in range(SIZE):
            if grid[r][c] == "#":
                continue
            starts_across = (c == 0 or grid[r][c - 1] == "#") and (
                c + 1 < SIZE and grid[r][c + 1] != "#"
            )
            starts_down = (r == 0 or grid[r - 1][c] == "#") and (
                r + 1 < SIZE and grid[r + 1][c] != "#"
            )
            if starts_across or starts_down:
                n += 1
                numbers[(r, c)] = n

    words = []
    for p in placed:
        r, c = p.row + off_r, p.col + off_c
        sat = sat_lookup.get(p.word)
        words.append(
            {
                "id": f"{numbers[(r, c)]}{'A' if p.horiz else 'D'}",
                "number": numbers[(r, c)],
                "direction": "across" if p.horiz else "down",
                "row": r,
                "col": c,
                "length": len(p.word),
                "answer": p.word,
                "clue": sat["clue"] if sat else fill_clues.get(p.word, ""),
                "isSATVocab": bool(sat),
                **({"definition": sat["definition"]} if sat else {}),
            }
        )
    words.sort(key=lambda w: (w["number"], w["direction"]))

    return {
        "date": date,
        "number": number,
        "size": {"rows": SIZE, "cols": SIZE},
        "solution": grid,
        "cells": {f"{r},{c}": {"number": numbers[(r, c)]} for (r, c) in numbers},
        "words": words,
    }


# ── orchestration ────────────────────────────────────────────────────────────
def generate(date: str, number: int, seed: int) -> dict:
    sat, fill = load_words()
    sat_lookup = {w["word"]: w for w in sat}
    sat_list = [w["word"] for w in sat]
    rng = random.Random(seed)

    fill_index: dict[tuple[int, int, str], list[str]] = defaultdict(list)
    for word in fill:
        for j, ch in enumerate(word):
            fill_index[(len(word), j, ch)].append(word)

    for restart in range(1, 30001):
        placed = attempt(sat_list, fill_index, rng)
        if placed is None:
            continue
        theme = sum(1 for p in placed if p.is_sat)
        if theme >= THEME_TARGET and MIN_WORDS <= len(placed) <= MAX_WORDS:
            print(
                f"built on restart {restart}: {len(placed)} entries, "
                f"{theme} SAT words, "
                f"{sum(len(p.word) for p in placed)} letters placed",
                file=sys.stderr,
            )
            return to_puzzle(placed, sat_lookup, date, number)

    raise SystemExit("no puzzle found — loosen constraints")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-05-22")
    ap.add_argument("--number", type=int, default=48)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    puzzle = generate(args.date, args.number, args.seed)
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
