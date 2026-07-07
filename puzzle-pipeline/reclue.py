"""
Re-assemble the clues of already-generated puzzles through the CURRENT
generator.to_puzzle logic — grid and answers stay identical; every clue
is re-picked. Use after clue-quality upgrades (root-stem leak detection,
dictionary-walk fallback) so shipped puzzles benefit without re-solving.

Run:  python3 reclue.py output/marquee_15x15 [more dirs...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import generator as G
import morphology as M

HERE = Path(__file__).parent


def reclue_file(path: Path, sat_lookup: dict) -> tuple[int, int]:
    """Returns (clues_changed, leaks_fixed)."""
    d = json.loads(path.read_text())
    grid = ["".join(row) for row in d["solution"]]
    slots = G.extract_slots(grid)
    by_start: dict[tuple[int, int, str], str] = {}
    for w in d["words"]:
        by_start[(w["row"], w["col"], w["direction"])] = w["answer"]
    assign = []
    for s in slots:
        r0, c0 = s.cells[0]
        answer = by_start.get((r0, c0, s.direction))
        if answer is None or len(answer) != s.length:
            print(f"  ! {path.name}: slot mismatch at {(r0, c0)}, skipping file")
            return (0, 0)
        assign.append(answer)

    old_by_id = {w["id"]: w for w in d["words"]}
    fresh = G.to_puzzle(grid, slots, assign, sat_lookup,
                        d.get("date", ""), d.get("number", 0))

    changed = leaks_fixed = 0
    for w in fresh["words"]:
        old = old_by_id.get(w["id"], {})
        if old.get("isMarquee"):
            w["isMarquee"] = True
        if w["clue"] != old.get("clue", ""):
            changed += 1
            if old.get("clue") and M.clue_leaks(w["answer"], old["clue"]):
                leaks_fixed += 1

    # preserve top-level extras (featured list refreshed with new clues)
    out = dict(d)
    out["words"] = fresh["words"]
    out["solution"] = fresh["solution"]
    if "featured" in d:
        feat_words = {f["word"] for f in d["featured"]}
        out["featured"] = [
            {"word": w["answer"], "clue": w["clue"],
             "definition": w.get("definition", ""), "id": w["id"]}
            for w in fresh["words"] if w["answer"] in feat_words
        ]
    path.write_text(json.dumps(out, indent=2))
    return (changed, leaks_fixed)


def main() -> None:
    dirs = [HERE / a for a in sys.argv[1:]] or [HERE / "output" / "marquee_15x15"]
    sat = G.load_sat()
    sat_lookup = {w["word"]: w for w in sat}
    for dpath in dirs:
        total_changed = total_leaks = files = 0
        for path in sorted(dpath.glob("*.json")):
            if path.name.startswith("_"):
                continue
            ch, lk = reclue_file(path, sat_lookup)
            total_changed += ch
            total_leaks += lk
            files += 1
        print(f"{dpath.name}: {files} puzzles, {total_changed} clues "
              f"changed, {total_leaks} leaking clues fixed")


if __name__ == "__main__":
    main()
