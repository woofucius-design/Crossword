"""
Builds clean_fill.json with a THREE-TIER hierarchy organized around what
students are likely to recognize. Solver iterates by pool ID, so the order
of entries == preference: SAT > tier 1 > tier 2 > tier 3.

  TIER 1 — school vocabulary.
    SCOWL ∩ Broda ≥ 50. SCOWL (both lowercase common English AND
    uppercase proper nouns from the spell-check dictionary) catches:
      - everyday English: APPLE, HORSE, LUCID, DEFT
      - educational proper nouns students learn in school: CAESAR,
        NAPOLEON, EGYPT, NILE, ATHENA, HAMLET, ROMEO, EINSTEIN, NEWTON,
        LINCOLN, KENNEDY, SAHARA, IRISH, SHAKESPEARE, PLATO, HOMER,
        CURIE, GALILEO, ROMAN, GREEK, AMAZON.
    Reject from SCOWL via "in the spell-check dictionary at all" — that
    catches CAESAR but not BARTMAN, NEWTON but not SNOOKI, ATHENA but
    not LEAMICHELE.

  TIER 2 — allowed but deprioritized.
    Three sources unioned:
    (a) dwyl English-words ∩ Broda ≥ 50, minus tier 1 — obscure-but-real
        English (DASHEEN taro, NIGELLA plant, HUMIC chemistry, ATAVIST,
        ASPERSE, METASEQUOIA, SOLATIA).
    (b) Roman numerals I..MM (from tier2_allow.txt).
    (c) Common abbreviations from tier2_allow.txt (GPS, HUD, USB, AKA,
        RSVP, DNA, MRI, CEO, BFF, FAQ).
    Min length 4 for (a) so 3-letter junk like BEC, CSC, MGR doesn't
    sneak into tier 2.

  TIER 3 — random acronyms / older fill / fallback.
    Broda ≥ 50 entries that don't make tier 1 or tier 2 — abbreviations
    students wouldn't know (BEC, CSC, MGR, CDR), and pop-culture or
    brand entries (SNOOKI, BARTMAN). Min length 3, lowest priority,
    solver only reaches when tiers 1+2 dry up.
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
TIER2_MIN_LEN = 4   # length-3 obscure English would mostly be junk abbrevs
TIER3_MAX_LEN = 6   # tier 3 is for short random acronyms only; longer
                    # Broda-only entries (ARTISTICNUDITY, BABYHITLER,
                    # ACCENTCOACH) are concentrated vulgar / pop-culture
                    # phrases that we exclude entirely.
TIER3_MAX_SCORE = 65  # Broda scores boring acronyms (BEC, CSC, NCO, MGR)
                    # at 50-65 but trendy slang / inappropriate (DAFUCK,
                    # LGBTQ, BTDUBS, WTF, FML) at 70-100. Capping tier 3
                    # at 65 keeps the inoffensive random acronyms students
                    # wouldn't know and excludes the slang.


def load_scowl_all() -> set[str]:
    """SCOWL spell-check dictionary, both lowercase common English and
    uppercase educational proper nouns. ~89k entries."""
    out: set[str] = set()
    with SCOWL_SRC.open() as fh:
        for w in fh:
            w = w.strip()
            if w and w.isalpha():
                out.add(w.upper())
    return out


def load_dwyl() -> set[str]:
    return {w.strip().upper() for w in DWYL_SRC.open() if w.strip().isalpha()}


def load_tier2_allow() -> set[str]:
    return {w.strip().upper() for w in TIER2_SRC.open() if w.strip().isalpha()}


def main() -> None:
    scowl = load_scowl_all()
    dwyl = load_dwyl()
    tier2_allow = load_tier2_allow()
    print(f"SCOWL all (school vocab):  {len(scowl):,}")
    print(f"dwyl english (broader):    {len(dwyl):,}")
    print(f"tier2 allow list:          {len(tier2_allow):,}")

    tier1: list[tuple[str, int]] = []
    tier2: list[tuple[str, int]] = []
    tier3: list[tuple[str, int]] = []
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
            # tier 2 allow-list (Roman numerals, common abbrevs) bypasses
            # MIN_SCORE — most Roman numerals score 30-38 in Broda but we
            # always want them in the pool.
            if word in tier2_allow:
                tier2.append((word, max(score, 50)))
                continue
            if score < MIN_SCORE:
                continue
            if word in scowl:
                tier1.append((word, score))
            elif word in dwyl and len(word) >= TIER2_MIN_LEN:
                tier2.append((word, score))
            elif len(word) <= TIER3_MAX_LEN and score <= TIER3_MAX_SCORE:
                tier3.append((word, score))
            # else: dropped — Broda-only entries longer than 6 chars are
            # almost always vulgar phrases or pop-culture (ACCENTCOACH,
            # ARTISTICNUDITY, BABYHITLER, BIGBERTHA, LEAMICHELE).

    # Add tier-2 allow-list entries that aren't in Broda at all (some Roman
    # numerals and obscure abbrevs) with a synthetic score of 50.
    added_synthetic = 0
    for w in tier2_allow:
        if MIN_LEN <= len(w) <= MAX_LEN and w not in seen_in_broda:
            tier2.append((w, 50))
            added_synthetic += 1

    tier1.sort(key=lambda p: (-p[1], p[0]))
    tier2.sort(key=lambda p: (-p[1], p[0]))
    tier3.sort(key=lambda p: (-p[1], p[0]))
    # Strict tier order: tier 1 all before tier 2 all before tier 3 all.
    # Within each tier, sort by Broda score descending. The earlier soft
    # blend (tier as tie-breaker at equal score) was abandoned because the
    # user wants pop-culture / acronyms genuinely deprioritized, not just
    # ranked behind same-score common English.
    ordered = (
        [w for w, _ in tier1]
        + [w for w, _ in tier2]
        + [w for w, _ in tier3]
    )
    OUT_PATH.write_text(json.dumps(ordered))

    print(f"\nTIER 1 (school vocab):              {len(tier1):>7,}")
    print(f"TIER 2 (obscure Eng + abbrev + Rmn): {len(tier2):>7,}  "
          f"({added_synthetic} added synthetic)")
    print(f"TIER 3 (random acronyms / fallback): {len(tier3):>7,}")
    print(f"total fill pool:                     {len(ordered):>7,}")
    print(f"\ntier 1 sample (educational): {', '.join(w for w, _ in tier1[2000:2010])}")
    print(f"tier 2 sample (obscure Eng): {', '.join(w for w, _ in tier2[200:210])}")
    print(f"tier 3 sample (random):      {', '.join(w for w, _ in tier3[:10])}")
    print(f"\nwritten -> {OUT_PATH.relative_to(HERE)}")


if __name__ == "__main__":
    main()
