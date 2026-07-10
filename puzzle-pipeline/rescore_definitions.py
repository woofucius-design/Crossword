"""
Common-sense sense selection for data/definitions.json.

build_definitions promotes the first NON-LEAKING source to primary with
no regard for which SENSE it is, so everyday words get whatever the
dictionaries listed first: HEN's octopus sense, PIE the proto-language,
CUTE's "obviously contrived to charm". Students read those as bugs.

Each candidate definition is scored by how common its content words are
(english_frequency ranks). Everyday senses are written in everyday
words ("female chicken"); technical senses reach for technical ones
("gallinaceous", "etiology", genus names). The best-scoring non-leaking
candidate becomes primary; the rest stay as alternates in score order.

Run:  python3 rescore_definitions.py            (after enrich)
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from morphology import clue_leaks

HERE = Path(__file__).parent
DEFS = HERE / "data" / "definitions.json"

STOP = set(
    "a an the and or of in on at by with for as to into from that which "
    "who whom whose is are was were be being been have has had its their "
    "his her any some several all each one two more most other others "
    "usually often very such not no than when where used".split()
)


def load_rank() -> dict[str, int]:
    rank: dict[str, int] = {}
    for i, line in enumerate((HERE / "data" / "english_frequency.txt")
                             .read_text().splitlines()):
        w = line.strip().lower()
        if w and w not in rank:
            rank[w] = i + 1
    return rank


RANK = load_rank()
UNKNOWN_PENALTY = math.log(500_000)


def commonness(definition: str) -> float:
    """Mean -log(freq rank) of content words; higher = more everyday.
    Unknown tokens (genus names, jargon) take a heavy penalty. Slight
    bonus for definitions that already fit in a clue."""
    toks = [t.lower() for t in re.findall(r"[A-Za-z]+", definition)
            if len(t) >= 3 and t.lower() not in STOP]
    if not toks:
        return -UNKNOWN_PENALTY
    total = 0.0
    for t in toks:
        r = RANK.get(t)
        total += -math.log(r + 1) if r else -UNKNOWN_PENALTY
    score = total / len(toks)
    if len(definition) <= 80:
        score += 0.5
    # capitalized mid-definition words = encyclopedic (proper nouns)
    caps = len(re.findall(r"(?<!^)(?<!\. )[A-Z][a-z]+", definition))
    score -= 0.4 * caps
    return score


def main() -> None:
    defs = json.loads(DEFS.read_text())
    promoted = 0
    for word, entry in defs.items():
        cands = [entry] + entry.get("alternates", [])
        if len(cands) < 2:
            continue
        scored = []
        for c in cands:
            d = c.get("definition", "")
            if not d or clue_leaks(word, d):
                continue
            scored.append((commonness(d), c))
        if not scored:
            continue
        scored.sort(key=lambda x: -x[0])
        best = scored[0][1]
        if best is not entry:
            promoted += 1
        head = {k: v for k, v in best.items() if k != "alternates"}
        rest = [
            {k: v for k, v in c.items() if k != "alternates"}
            for _s, c in scored[1:]
        ]
        # keep leaking candidates at the very back (reclue never uses
        # them, but they document the source)
        for c in cands:
            d = c.get("definition", "")
            if d and clue_leaks(word, d) and c is not best:
                rest.append({k: v for k, v in c.items() if k != "alternates"})
        if rest:
            head["alternates"] = rest
        defs[word] = head

    DEFS.write_text(json.dumps(defs, indent=1))
    print(f"entries: {len(defs):,}  promoted better senses: {promoted:,}")

    for probe in ("HEN", "PIE", "OPEN", "CUTE", "ELM", "MIN"):
        e = defs.get(probe)
        if e:
            print(f"  {probe}: {e['definition'][:70]}")


if __name__ == "__main__":
    main()
