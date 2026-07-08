"""
Direct NYT-style grid construction. build_grid's row-enumeration search
is biased toward black-heavy rows and almost never emits low-clump
15x15 patterns, so this builds them the way constructors do: place
small black units (dominoes/triominoes/stair-steps/singles) onto an
empty grid with 180° symmetry, checking word-length and connectivity
constraints as it goes.

  make_nyt_grid(size, rng, target_blacks, max_clump=3) -> grid | None
"""
from __future__ import annotations

import random

MIN_RUN = 3

# Black units to stamp (dr, dc offsets). Mirrored copies land at the
# 180°-symmetric position automatically.
UNITS = [
    [(0, 0)],                             # single
    [(0, 0), (0, 1)],                     # horizontal domino
    [(0, 0), (1, 0)],                     # vertical domino
    [(0, 0), (0, 1), (0, 2)],             # horizontal triomino (edge block)
    [(0, 0), (1, 0), (2, 0)],             # vertical triomino
    [(0, 0), (1, 1)],                     # stair-step (diagonal, 2 clumps of 1)
    [(0, 0), (1, 1), (2, 2)],             # 3-long staircase
    [(0, 0), (1, 0), (1, 1)],             # L triomino
    [(0, 0), (0, 1), (1, 1)],             # L triomino
]


def _runs_ok_line(line: list[str]) -> bool:
    run = 0
    for ch in line + ["#"]:
        if ch == "#":
            if 0 < run < MIN_RUN:
                return False
            run = 0
        else:
            run += 1
    return True


def _all_runs_ok(grid: list[list[str]], size: int) -> bool:
    for r in range(size):
        if not _runs_ok_line(grid[r][:]):
            return False
    for c in range(size):
        if not _runs_ok_line([grid[r][c] for r in range(size)]):
            return False
    return True


def _connected(grid: list[list[str]], size: int) -> bool:
    start = None
    whites = 0
    for r in range(size):
        for c in range(size):
            if grid[r][c] != "#":
                whites += 1
                if start is None:
                    start = (r, c)
    if start is None:
        return False
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and \
                    grid[nr][nc] != "#" and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return len(seen) == whites


def _clump_ok(grid: list[list[str]], size: int, max_clump: int) -> bool:
    blacks = {(r, c) for r in range(size) for c in range(size)
              if grid[r][c] == "#"}
    seen: set[tuple[int, int]] = set()
    for b in blacks:
        if b in seen:
            continue
        stack, n = [b], 0
        seen.add(b)
        while stack:
            r, c = stack.pop()
            n += 1
            if n > max_clump:
                return False
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in blacks and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
    return True


def make_nyt_grid(size: int, rng: random.Random, target_blacks: int,
                  max_clump: int = 3, tries: int = 400) -> list[list[str]] | None:
    """One attempt: stamp symmetric black units until target reached.
    Returns None if the attempt stalls before reaching a valid pattern."""
    grid = [["." for _ in range(size)] for _ in range(size)]
    blacks = 0
    stall = 0
    while blacks < target_blacks and stall < tries:
        stall += 1
        unit = rng.choice(UNITS)
        r0 = rng.randrange(size)
        c0 = rng.randrange(size)
        cells: set[tuple[int, int]] = set()
        ok = True
        for dr, dc in unit:
            r, c = r0 + dr, c0 + dc
            if not (0 <= r < size and 0 <= c < size):
                ok = False
                break
            cells.add((r, c))
            cells.add((size - 1 - r, size - 1 - c))
        if not ok:
            continue
        add = [c for c in cells if grid[c[0]][c[1]] == "."]
        if not add:
            continue
        if blacks + len(add) > target_blacks + 1:
            continue
        for r, c in add:
            grid[r][c] = "#"
        if (_all_runs_ok(grid, size)
                and _clump_ok(grid, size, max_clump)
                and _connected(grid, size)):
            blacks += len(add)
            stall = 0
        else:
            for r, c in add:
                grid[r][c] = "."
    if blacks < target_blacks:
        return None
    return grid
