"""
Builds clean_fill.json with a THREE-TIER hierarchy. The solver iterates by
ID order (lower ID = tried first), so pool position == preference:

  TIER 1 — common English fill.
    SCOWL-lowercase (curated spell-check dict, ~80k entries — proper
    nouns are uppercase in SCOWL, so they're excluded) ∩ Broda ≥ 50.
    Sorted by Broda score descending.

  TIER 2 — well-known abbreviations + Roman numerals.
    From data/tier2_allow.txt: GPS, HUD, USB, AKA, RSVP, DNA, MRI, plus
    Roman numerals I..MM. These help short slots without falling to
    obscure technical English.

  TIER 3 — obscure-but-real English fill.
    dwyl English-words ∩ Broda ≥ 50, minus tiers 1+2. Includes
    DASHEEN (taro), NIGELLA (plant), HUMIC (chemistry), SOLATIA (legal),
    ATAVIST, ASPERSE. Min length 4 — 3-letter "junk" like BEC, CSC, MGR
    is excluded (length-3 fill must come from tier 1 or 2).

The fourth tier (SAT vocab) is prepended by the puzzle generator itself
— SAT IDs end up at 0..N ahead of every fill ID. The full ordering the
solver sees: SAT > common English > abbreviations/Roman > obscure.

Broda entries NOT in any English list (FML, MURICA, SNOOKI, TBILISI,
BARTMAN, PADUCAH) are dropped entirely.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SCOWL_SRC = HERE / "data" / "scowl.txt"
DWYL_SRC = HERE / "data" / "english_words.txt"
TIER2_SRC = HERE / "data" / "tier2_allow.txt"
BRODA_SRC = HERE / "data" / "broda_wordlist.txt"
OUT_PATH = HERE / "data" / "clean_fill.json"

MIN_SCORE = 50
MIN_LEN = 3
MAX_LEN = 15
TIER3_MIN_LEN = 4   # 3-letter slots must use tier 1 or 2, not tier 3


def load_scowl_lower() -> set[str]:
    out: set[str] = set()
    with SCOWL_SRC.open() as fh:
        for w in fh:
            w = w.strip()
            if w and w.islower() and w.isalpha():
                out.add(w.upper())
    return out


def load_dwyl() -> set[str]:
    return {w.strip().upper() for w in DWYL_SRC.open() if w.strip().isalpha()}


def load_tier2_allow() -> set[str]:
    return {w.strip().upper() for w in TIER2_SRC.open() if w.strip().isalpha()}


def main() -> None:
    scowl_lower = load_scowl_lower()
    dwyl = load_dwyl()
    tier2_allow = load_tier2_allow()
    print(f"SCOWL lowercase:    {len(scowl_lower):,}")
    print(f"dwyl english:       {len(dwyl):,}")
    print(f"tier2 allow list:   {len(tier2_allow):,}")

    tier1: list[tuple[str, int]] = []
    tier2: list[tuple[str, int]] = []
    tier3: list[tuple[str, int]] = []
    excluded_junk = 0
    seen_in_broda: set[str] = set()
    with BRODA_SRC.open(encoding="latin-1") as fh:
        for line in fh:
            line = line.strip()
            if not line or ";" not in line:
                continue
            word, _, score_str = line.partition(";")
            word = word.upper()
            if not re.fullmatch(r"[A-Z]+", word):
                continue
            if not (MIN_LEN <= len(word) <= MAX_LEN):
                continue
            try:
                score = int(score_str)
            except ValueError:
                continue
            seen_in_broda.add(word)
            # tier 2 allow-list entries bypass MIN_SCORE — most Roman numerals
            # score 30-40 in Broda but we want them in the pool regardless,
            # since they're standard crossword fill and any tier-2 entry is
            # by definition something we've decided is OK.
            if word in tier2_allow:
                tier2.append((word, max(score, 50)))
                continue
            if score < MIN_SCORE:
                continue
            if word in scowl_lower:
                tier1.append((word, score))
            elif word in dwyl and len(word) >= TIER3_MIN_LEN:
                tier3.append((word, score))
            else:
                excluded_junk += 1

    # Add tier-2 allow-list entries that aren't in Broda at all (some Roman
    # numerals and very obscure abbrevs) with a synthetic score of 50.
    added_synthetic = 0
    for w in tier2_allow:
        if MIN_LEN <= len(w) <= MAX_LEN and w not in seen_in_broda:
            tier2.append((w, 50))
            added_synthetic += 1

    tier1.sort(key=lambda p: (-p[1], p[0]))
    tier2.sort(key=lambda p: (-p[1], p[0]))
    tier3.sort(key=lambda p: (-p[1], p[0]))
    # Interleave tier 1 & 2 by Broda score (so a score-80 tier-2 word still
    # outranks a score-50 tier-1 word — score is the primary signal at the
    # top of the pool). Tier 3 comes last regardless of score, so obscure
    # English is reached only when tiers 1+2 dry up.
    merged_12: list[tuple[str, int, int]] = (
        [(w, s, 0) for w, s in tier1] + [(w, s, 1) for w, s in tier2]
    )
    merged_12.sort(key=lambda p: (-p[1], p[2], p[0]))
    ordered = [w for w, _, _ in merged_12] + [w for w, _ in tier3]
    OUT_PATH.write_text(json.dumps(ordered))

    print(f"\nTIER 1 (common English):       {len(tier1):>7,}")
    print(f"TIER 2 (abbrev + Roman):       {len(tier2):>7,}  "
          f"({added_synthetic} added synthetic)")
    print(f"TIER 3 (obscure English >=4):  {len(tier3):>7,}")
    print(f"excluded junk:                 {excluded_junk:>7,}")
    print(f"total fill pool:               {len(ordered):>7,}")
    print(f"\ntier 2 top 10: {', '.join(w for w, _ in tier2[:10])}")
    print(f"tier 3 top 10: {', '.join(w for w, _ in tier3[:10])}")
    print(f"\nwritten -> {OUT_PATH.relative_to(HERE)}")


if __name__ == "__main__":
    main()
