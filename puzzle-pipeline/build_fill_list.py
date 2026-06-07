"""
Builds clean_fill.json with a TWO-TIER hierarchy that the solver reads via
ID order (lower ID = tried first):

  TIER 1 — common English fill.
    SCOWL-lowercase (curated spell-check dict, ~80k entries — proper nouns
    are uppercase in SCOWL, so they're excluded) ∩ Broda ≥ 50. Sorted by
    Broda score descending.

  TIER 2 — obscure-but-real English fill.
    dwyl English-words (370k, broader coverage of inflections, technical
    terms, demonyms) ∩ Broda ≥ 50 minus tier 1. Sorted by Broda score
    descending.

The third implicit tier (SAT vocab) is prepended by the puzzle generator
itself — see G.load_sat / pool construction — so SAT IDs end up at 0..N
ahead of every fill ID. Solver default value-ordering (lowest ID first)
delivers the full priority: SAT > common English > obscure.

Words in Broda only (slang, brands, place names like FML, MURICA, SNOOKI,
TBILISI, BARTMAN) are dropped — they appear in neither English list.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SCOWL_SRC = HERE / "data" / "scowl.txt"
DWYL_SRC = HERE / "data" / "english_words.txt"
BRODA_SRC = HERE / "data" / "broda_wordlist.txt"
OUT_PATH = HERE / "data" / "clean_fill.json"

MIN_SCORE = 50
MIN_LEN = 3
MAX_LEN = 15


def load_scowl_common() -> set[str]:
    """SCOWL entries that are entirely lowercase letters — common English
    only, no proper nouns ('Aachen', 'Tbilisi') or acronyms ('LSAT', 'LLB')."""
    out: set[str] = set()
    with SCOWL_SRC.open() as fh:
        for w in fh:
            w = w.strip()
            if w and w.islower() and w.isalpha():
                out.add(w.upper())
    return out


def load_dwyl() -> set[str]:
    """dwyl/english-words — broad coverage including inflections, demonyms
    (SPANIARDS), technical English (METASEQUOIA, SOLATIA). May include some
    proper nouns the list happens to contain, but excludes pure slang."""
    return {w.strip().upper() for w in DWYL_SRC.open() if w.strip().isalpha()}


def main() -> None:
    scowl_common = load_scowl_common()
    dwyl = load_dwyl()
    print(f"SCOWL lowercase: {len(scowl_common):,}")
    print(f"dwyl english:    {len(dwyl):,}")

    tier1: list[tuple[str, int]] = []
    tier2: list[tuple[str, int]] = []
    junk_skipped = 0
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
            if score < MIN_SCORE:
                continue
            if word in scowl_common:
                tier1.append((word, score))
            elif word in dwyl:
                tier2.append((word, score))
            else:
                junk_skipped += 1

    tier1.sort(key=lambda p: (-p[1], p[0]))
    tier2.sort(key=lambda p: (-p[1], p[0]))
    # Interleave by score: at equal Broda score, tier 1 (common English)
    # beats tier 2 (obscure English) — so the solver tries common words
    # first at every score level, but a high-score tier-2 entry still wins
    # over a low-score tier-1 entry. Strict tier-first ordering
    # over-constrained the 15x15 solver because all 76k tier-1 entries
    # had to be exhausted before any tier-2 word was tried.
    merged: list[tuple[str, int, int]] = (  # (word, score, tier_rank)
        [(w, s, 0) for w, s in tier1] + [(w, s, 1) for w, s in tier2]
    )
    merged.sort(key=lambda p: (-p[1], p[2], p[0]))
    ordered = [w for w, _, _ in merged]
    OUT_PATH.write_text(json.dumps(ordered))

    print(f"\nTIER 1 (common English):  {len(tier1):>7,}")
    print(f"TIER 2 (obscure English): {len(tier2):>7,}")
    print(f"junk (no dict / slang):   {junk_skipped:>7,}  (excluded)")
    print(f"total fill pool:          {len(ordered):>7,}")
    print(f"\ntier 1 top 10: {', '.join(w for w, _ in tier1[:10])}")
    print(f"tier 2 top 10: {', '.join(w for w, _ in tier2[:10])}")
    print(f"\nwritten -> {OUT_PATH.relative_to(HERE)}")


if __name__ == "__main__":
    main()
