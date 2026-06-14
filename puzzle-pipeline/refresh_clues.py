"""
Re-clue existing puzzle JSON files in place from the current clue sources
(definitions.json, sat_alt_clues.json, sat_synonym_index.json) WITHOUT
re-solving. Reconstructs each puzzle's grid + answers and re-runs
generator.to_puzzle, which applies the latest clue logic.

Use after regenerating clue data so already-shipped grids pick up improved
clues (e.g. the inflection-of-definition rewrite) without a fresh factory
sweep.

Run:  python3 refresh_clues.py output/factory/*.json
      python3 refresh_clues.py            # default: all of output/factory
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import generator as G


def grid_from_solution(solution: list[list[str]]) -> list[list[str]]:
    """Solution cells are letters or '#'. extract_slots only needs to know
    which cells are black, and to_puzzle reads letters from this grid for
    each slot — so the solution grid IS a valid grid input."""
    return [list(row) for row in solution]


def refresh(path: Path, sat_lookup: dict) -> dict:
    puzzle = json.loads(path.read_text())
    grid = grid_from_solution(puzzle["solution"])
    slots = G.extract_slots(grid)
    # assign = answer per slot, in extract_slots order
    assign = []
    for slot in slots:
        assign.append("".join(grid[r][c] for r, c in slot.cells))
    rebuilt = G.to_puzzle(
        grid, slots, assign, sat_lookup,
        puzzle.get("date", ""), puzzle.get("number", 0),
    )
    # Preserve any top-level metadata the factory added beyond to_puzzle's
    # output (none currently, but future-proof).
    path.write_text(json.dumps(rebuilt, indent=2))
    clued = sum(1 for w in rebuilt["words"] if w["clue"])
    return {"file": path.name, "entries": len(rebuilt["words"]), "clued": clued}


def main() -> None:
    args = sys.argv[1:]
    if args:
        paths = [Path(a) for a in args]
    else:
        paths = sorted((G.HERE / "output" / "factory").glob("[0-9]*.json"))

    # Clear caches so we read the freshly-rebuilt clue data, not a stale
    # lru_cache from import time.
    for fn in (
        G.load_definitions, G.load_sat_alt_clues,
        G.load_sat_synonym_index, G.load_fill_clues,
    ):
        fn.cache_clear()

    sat_lookup = {w["word"]: w for w in G.load_sat()}
    total_clued = total_entries = 0
    for p in paths:
        if not p.exists():
            print(f"  skip (missing): {p}")
            continue
        r = refresh(p, sat_lookup)
        total_clued += r["clued"]
        total_entries += r["entries"]
    pct = 100 * total_clued / max(total_entries, 1)
    print(f"refreshed {len(paths)} puzzles: "
          f"{total_clued}/{total_entries} entries clued ({pct:.0f}%)")


if __name__ == "__main__":
    main()
