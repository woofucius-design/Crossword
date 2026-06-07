"""
Builds clean_fill.json using a frequency-driven THREE-TIER hierarchy.

The earlier "SCOWL alone for tier 1" was the root cause of the user's
specific complaints (NSC, MEIER, MCADOO, CREESE in fill): SCOWL is a
spell-checker dictionary and accepts ANY proper noun or abbreviation it
recognizes (NSC, AACHEN, ABERNATHY, ABM). The fix is to require words in
the higher tiers to also appear at meaningful frequency rank in modern
English usage. English-frequency separates clean common words from niche
ones by usage rather than by spell-check membership.

Pool order (solver tries lowest ID first, so this == preference):

  TIER 1 — common, school-relevant vocabulary.
    All entries are either:
      (a) SCOWL-lowercase (common English: APPLE, MOTHER, LUCID), OR
      (b) SCOWL ∩ english-frequency top 12,000 (well-known proper
          nouns and abbrevs: CAESAR @7.6k, NILE @10.7k, EGYPT @2.9k,
          EINSTEIN @8.9k, IRISH @2.4k).
    Excludes NSC @26k, MEIER @22k, MCADOO @49k, AACHEN @20k+ — proper
    nouns SCOWL knows but that aren't in active modern usage.
    Sort within: frequency rank ascending (most-common first).

  TIER 2 — moderately uncommon but real, still encountered.
    All entries either:
      (a) dwyl entries with frequency rank 12k..100k, length ≥ 4,
          in Broda (technical English / less-known terms that still
          appear in modern text: HUMIC @32k, GESTATION @15k).
      (b) Roman numerals from tier2_allow.
      (c) Common abbreviations from tier2_allow (GPS, HUD, DNA, MRI,
          USB, CEO) — these are in tier 2 deliberately as "well-known
          but should not preempt school vocab".
    Sort within: alphabetical.

  TIER 3 — fallback (rare-or-niche, students wouldn't recognize).
    All entries either:
      (a) Short (3-6 char) Broda-only entries scored ≤65 — boring
          acronyms (BEC, CSC, CDR, MGR-ish) without trendy slang.
      (b) dwyl entries NOT in top-100k frequency — archaic / dialectal
          English (CREESE, DASHEEN, NIGELLA, SOLATIA, ATAVIST).
      (c) data/tier3_force.txt — hand-curated override for items the
          dictionaries get wrong (specific surnames, niche acronyms).
    Sort within: alphabetical.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SCOWL_SRC = HERE / "data" / "scowl.txt"
DWYL_SRC = HERE / "data" / "english_words.txt"
TIER2_SRC = HERE / "data" / "tier2_allow.txt"
TIER3_FORCE_SRC = HERE / "data" / "tier3_force.txt"
BRODA_SRC = HERE / "data" / "broda_wordlist.txt"
FREQ_SRC = HERE / "data" / "english_frequency.txt"
OUT_PATH = HERE / "data" / "clean_fill.json"

MIN_LEN = 3
MAX_LEN = 15
TIER1_PROPER_RANK = 12_000  # SCOWL proper nouns / abbrevs must rank at or
                             # below this in english_frequency to enter
                             # tier 1. CAESAR @7.6k, NILE @10.7k, HAMLET
                             # @8.1k all qualify. NSC @26k, MEIER @22k,
                             # MCADOO @49k drop out.
TIER2_FREQ_CAP = 100_000     # dwyl entries above this rank fall to tier 3.
TIER2_MIN_LEN = 4
TIER3_MAX_LEN = 6
TIER3_MAX_BRODA = 65


def load_alpha_upper(path: Path) -> set[str]:
    return {w.strip().upper() for w in path.open()
            if w.strip() and w.strip().isalpha()}


def load_alpha_lower_in_scowl() -> set[str]:
    out: set[str] = set()
    for w in SCOWL_SRC.open():
        w = w.strip()
        if w and w.islower() and w.isalpha():
            out.add(w.upper())
    return out


def load_frequency_rank() -> dict[str, int]:
    rank: dict[str, int] = {}
    for i, w in enumerate(FREQ_SRC.open(), 1):
        w = w.strip().upper()
        if w.isalpha() and w not in rank:
            rank[w] = i
    return rank


def load_tier3_force() -> set[str]:
    out: set[str] = set()
    for line in TIER3_FORCE_SRC.open():
        line = line.split("#", 1)[0].strip().upper()
        if line and line.isalpha():
            out.add(line)
    return out


def main() -> None:
    scowl_all = load_alpha_upper(SCOWL_SRC)
    scowl_lower = load_alpha_lower_in_scowl()
    dwyl = load_alpha_upper(DWYL_SRC)
    tier2_allow = load_alpha_upper(TIER2_SRC)
    tier3_force = load_tier3_force()
    freq = load_frequency_rank()
    print(f"SCOWL all:         {len(scowl_all):,}")
    print(f"SCOWL lowercase:   {len(scowl_lower):,}")
    print(f"dwyl english:      {len(dwyl):,}")
    print(f"tier2 allow:       {len(tier2_allow):,}")
    print(f"tier3 force:       {len(tier3_force):,}")
    print(f"frequency list:    {len(freq):,}")

    broda: dict[str, int] = {}
    with BRODA_SRC.open(encoding="latin-1") as fh:
        for line in fh:
            w, _, s = line.strip().partition(";")
            w = w.upper()
            if not re.fullmatch(r"[A-Z]+", w):
                continue
            if not (MIN_LEN <= len(w) <= MAX_LEN):
                continue
            try:
                broda[w] = int(s)
            except ValueError:
                pass

    tier1: set[str] = set()
    tier2: set[str] = set()
    tier3: set[str] = set()

    # TIER 1: SCOWL-lower (common English) + SCOWL entries in top 12k freq.
    for w in scowl_lower:
        if w in tier3_force or not (MIN_LEN <= len(w) <= MAX_LEN):
            continue
        tier1.add(w)
    for w in scowl_all - scowl_lower:
        if w in tier3_force or not (MIN_LEN <= len(w) <= MAX_LEN):
            continue
        r = freq.get(w)
        if r is not None and r <= TIER1_PROPER_RANK:
            tier1.add(w)

    # TIER 2 from dwyl: rank between TIER1_PROPER_RANK and TIER2_FREQ_CAP.
    for w in dwyl:
        if w in tier1 or w in tier3_force:
            continue
        if not (TIER2_MIN_LEN <= len(w) <= MAX_LEN):
            continue
        if w not in broda:
            continue  # Broda inclusion filter so weird dwyl entries drop
        r = freq.get(w)
        if r is None or r > TIER2_FREQ_CAP:
            continue
        tier2.add(w)

    # TIER 2 also includes our curated common abbrevs + Roman numerals.
    for w in tier2_allow:
        if w in tier1 or w in tier3_force:
            continue
        if MIN_LEN <= len(w) <= MAX_LEN:
            tier2.add(w)

    # TIER 3: short Broda-only acronyms + dwyl entries outside top 100k.
    for w, s in broda.items():
        if w in tier1 or w in tier2:
            continue
        if not (MIN_LEN <= len(w) <= TIER3_MAX_LEN):
            continue
        if s > TIER3_MAX_BRODA:
            continue
        tier3.add(w)
    for w in dwyl:
        if w in tier1 or w in tier2 or w in tier3:
            continue
        if not (TIER2_MIN_LEN <= len(w) <= MAX_LEN):
            continue
        if w not in broda:
            continue
        # By construction these are dwyl ∩ Broda with freq rank > 100k or
        # missing entirely — archaic / dialectal English (CREESE, DASHEEN,
        # NIGELLA, SOLATIA).
        tier3.add(w)
    for w in tier3_force:
        if MIN_LEN <= len(w) <= MAX_LEN:
            tier3.add(w)

    no_rank = len(freq) + 1
    tier1_sorted = sorted(tier1, key=lambda w: (freq.get(w, no_rank), w))
    tier2_sorted = sorted(tier2)
    tier3_sorted = sorted(tier3)
    ordered = tier1_sorted + tier2_sorted + tier3_sorted
    OUT_PATH.write_text(json.dumps(ordered))

    print(f"\nTIER 1 (school vocab):              {len(tier1):>7,}")
    print(f"TIER 2 (in top 100k freq + Rmn):    {len(tier2):>7,}")
    print(f"TIER 3 (archaic/niche/random):      {len(tier3):>7,}")
    print(f"total fill pool:                    {len(ordered):>7,}")
    print(f"\ntier 1 top 10 by frequency: "
          f"{', '.join(tier1_sorted[:10])}")
    print(f"tier 2 sample:              "
          f"{', '.join(tier2_sorted[:10])}")
    print(f"tier 3 sample:              "
          f"{', '.join(tier3_sorted[:10])}")
    print(f"\nwritten -> {OUT_PATH.relative_to(HERE)}")


if __name__ == "__main__":
    main()
