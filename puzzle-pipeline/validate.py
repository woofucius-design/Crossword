"""
Validates a generated puzzle JSON. Confirms the puzzle is a real, consistent
crossword: answers match the grid, crossings agree, numbering is correct, the
white cells form one connected region, every word interlocks, and no
unintended words appear.

Run:  python3 validate.py output/2026-05-22.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def runs(grid: list[list[str]], size: int) -> list[list[tuple[int, int]]]:
    """Maximal horizontal and vertical runs of >= 2 white cells."""
    out: list[list[tuple[int, int]]] = []
    for r in range(size):
        c = 0
        while c < size:
            if grid[r][c] != "#":
                start = c
                while c < size and grid[r][c] != "#":
                    c += 1
                if c - start >= 2:
                    out.append([(r, x) for x in range(start, c)])
            else:
                c += 1
    for c in range(size):
        r = 0
        while r < size:
            if grid[r][c] != "#":
                start = r
                while r < size and grid[r][c] != "#":
                    r += 1
                if r - start >= 2:
                    out.append([(x, c) for x in range(start, r)])
            else:
                r += 1
    return out


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "output/2026-05-22.json")
    puzzle = json.loads(path.read_text())
    rows = puzzle["size"]["rows"]
    cols = puzzle["size"]["cols"]
    grid = puzzle["solution"]
    words = puzzle["words"]
    errors: list[str] = []

    # 1. answers match the grid
    for w in words:
        cells = (
            [(w["row"], w["col"] + i) for i in range(w["length"])]
            if w["direction"] == "across"
            else [(w["row"] + i, w["col"]) for i in range(w["length"])]
        )
        letters = "".join(grid[r][c] for r, c in cells)
        if letters != w["answer"]:
            errors.append(f"{w['id']}: grid spells {letters!r}, answer is {w['answer']!r}")
        if "#" in letters:
            errors.append(f"{w['id']}: runs through a black square")

    # 2. every >=2 run is exactly one listed word (no unintended words)
    listed = set()
    for w in words:
        cells = (
            tuple((w["row"], w["col"] + i) for i in range(w["length"]))
            if w["direction"] == "across"
            else tuple((w["row"] + i, w["col"]) for i in range(w["length"]))
        )
        listed.add(cells)
    for run in runs(grid, rows):
        if tuple(run) not in listed:
            spelled = "".join(grid[r][c] for r, c in run)
            errors.append(f"unintended word {spelled!r} at {run[0]}")

    # 3. numbering matches recomputed standard numbering
    expected: dict[str, int] = {}
    n = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "#":
                continue
            sa = (c == 0 or grid[r][c - 1] == "#") and (
                c + 1 < cols and grid[r][c + 1] != "#"
            )
            sd = (r == 0 or grid[r - 1][c] == "#") and (
                r + 1 < rows and grid[r + 1][c] != "#"
            )
            if sa or sd:
                n += 1
                expected[f"{r},{c}"] = n
    for w in words:
        key = f"{w['row']},{w['col']}"
        if expected.get(key) != w["number"]:
            errors.append(f"{w['id']}: number {w['number']} != expected {expected.get(key)}")

    # 4. white cells form one connected component
    whites = {(r, c) for r in range(rows) for c in range(cols) if grid[r][c] != "#"}
    if whites:
        seen = {next(iter(whites))}
        stack = list(seen)
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (r + dr, c + dc) in whites and (r + dr, c + dc) not in seen:
                    seen.add((r + dr, c + dc))
                    stack.append((r + dr, c + dc))
        if len(seen) != len(whites):
            errors.append(f"grid not connected: {len(seen)}/{len(whites)} cells reachable")

    # 5. every word interlocks with another
    cell_count: dict[tuple[int, int], int] = {}
    for w in words:
        cells = (
            [(w["row"], w["col"] + i) for i in range(w["length"])]
            if w["direction"] == "across"
            else [(w["row"] + i, w["col"]) for i in range(w["length"])]
        )
        for cell in cells:
            cell_count[cell] = cell_count.get(cell, 0) + 1
    for w in words:
        cells = (
            [(w["row"], w["col"] + i) for i in range(w["length"])]
            if w["direction"] == "across"
            else [(w["row"] + i, w["col"]) for i in range(w["length"])]
        )
        if not any(cell_count[cell] > 1 for cell in cells):
            errors.append(f"{w['id']} ({w['answer']}) crosses nothing")

    sat = [w for w in words if w["isSATVocab"]]
    print(f"puzzle #{puzzle['number']}  {puzzle['date']}")
    print(f"  {len(words)} entries · {len(sat)} SAT vocab · {len(whites)} white cells")
    if errors:
        print(f"  FAILED ({len(errors)} issue(s)):")
        for e in errors:
            print(f"    - {e}")
        return 1
    print("  VALID — consistent, connected, fully interlocked, no stray words.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
