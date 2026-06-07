"""
Builds clean_fill.json using a TIER hierarchy + English-frequency ordering.
Drops Broda scoring entirely — Broda assigns 100 to vulgar / slang (DAFUCK,
MURICA, LGBTQ), 70-80 to common words (BREAD, HORSE), and 50 to both SAT
vocab (LUCID, EPHEMERAL) and obscure technical English (DASHEEN, NIGELLA).
That ranking is exactly backwards for our use case.

Pool order (solver tries lowest ID first, so this == preference):

  TIER 1 — school vocabulary.
    SCOWL spell-check entries (lowercase common English PLUS uppercase
    educational proper nouns: CAESAR, NAPOLEON, EGYPT, NILE, ATHENA,
    HAMLET, EINSTEIN, NEWTON, KENNEDY, IRISH, SAHARA, AMAZON, HOMER).
    Within tier 1, sorted by English word-frequency rank (top-100k list)
    so MOTHER (rank 200) outranks ALACRITY (rank 50k+).

  TIER 2 — allowed but deprioritized.
    (a) dwyl English-words minus tier 1, min length 4 — obscure-but-real
        English (DASHEEN, NIGELLA, HUMIC, METASEQUOIA, SOLATIA).
    (b) Roman numerals I..MM (from tier2_allow.txt).
    (c) Curated common abbreviations (GPS, HUD, DNA, MRI, USB, CEO).
    Within tier 2, sorted alphabetically — none of these have a clean
    frequency signal.

  TIER 3 — random acronyms / fallback.
    3-6 char entries from the Broda wordlist that are NOT in any English
    dict and NOT in our tier-2 allow list, AND whose Broda score is ≤ 65
    (to filter out trendy slang like DAFUCK / LGBTQ scored 70+). The
    "boring acronyms students wouldn't recognize" bucket: BEC, CSC, MGR,
    CDR, NCO. Within tier 3, alphabetical.

Sources we look at solely to find which entries should be in the pool:
  data/scowl.txt          spell-check dictionary (89k)
  data/english_words.txt  dwyl/english-words (370k, broader)
  data/tier2_allow.txt    Roman + curated abbrevs (1.1k)
  data/broda_wordlist.txt source list of all candidate fill words
  data/english_frequency.txt  top-100k English by frequency
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SCOWL_SRC = HERE / "data" / "scowl.txt"
DWYL_SRC = HERE / "data" / "english_words.txt"
TIER2_SRC = HERE / "data" / "tier2_allow.txt"
BRODA_SRC = HERE / "data" / "broda_wordlist.txt"
FREQ_SRC = HERE / "data" / "english_frequency.txt"
OUT_PATH = HERE / "data" / "clean_fill.json"

MIN_LEN = 3
MAX_LEN = 15
TIER2_MIN_LEN = 4   # length-3 obscure English is mostly junk abbrevs
TIER3_MAX_LEN = 6   # tier-3 fallback is for short acronyms; longer
                    # Broda-only entries (BABYHITLER, ACCENTCOACH,
                    # ARTISTICNUDITY) are concentrated vulgar phrases.
TIER3_MAX_BRODA = 65  # tier-3 caps Broda score at 65 so we keep the
                    # boring random acronyms (BEC, CSC, MGR scored 50-65)
                    # but drop trendy slang (DAFUCK / LGBTQ / FML scored
                    # 70-100). Broda is only used as a junk filter here,
                    # not as a quality ranking.


def load_alpha(path: Path, *, case_filter=lambda w: True) -> set[str]:
    out: set[str] = set()
    for w in path.open():
        w = w.strip()
        if w and w.isalpha() and case_filter(w):
            out.add(w.upper())
    return out


def load_frequency_rank() -> dict[str, int]:
    """word -> 1-indexed rank (1 = most common). Words outside the top-100k
    list get rank len+1, putting them at the end of within-tier sort."""
    rank: dict[str, int] = {}
    for i, w in enumerate(FREQ_SRC.open(), 1):
        w = w.strip().upper()
        if w.isalpha() and w not in rank:
            rank[w] = i
    return rank


def main() -> None:
    scowl = load_alpha(SCOWL_SRC)
    dwyl = load_alpha(DWYL_SRC)
    tier2_allow = load_alpha(TIER2_SRC)
    frequency = load_frequency_rank()
    print(f"SCOWL (school vocab):     {len(scowl):,}")
    print(f"dwyl english (broader):   {len(dwyl):,}")
    print(f"tier 2 allow list:        {len(tier2_allow):,}")
    print(f"frequency list:           {len(frequency):,}")

    # Collect Broda entries — only used to filter tier-3 junk.
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

    for w in scowl:
        if MIN_LEN <= len(w) <= MAX_LEN:
            tier1.add(w)
    for w in dwyl:
        if w in tier1:
            continue
        if not (TIER2_MIN_LEN <= len(w) <= MAX_LEN):
            continue
        # tier 2 still uses Broda as a "is this a reasonable crossword
        # entry" inclusion filter — Broda's 492k entries reflect "yes a
        # constructor would consider this". We're NOT using Broda's
        # score values, just the membership. Without this filter tier 2
        # balloons to 278k including AAHED / AALII / AARDWOLVES.
        if w not in broda:
            continue
        tier2.add(w)
    for w in tier2_allow:
        if w in tier1:
            continue
        if MIN_LEN <= len(w) <= MAX_LEN:
            tier2.add(w)
    for w, s in broda.items():
        if w in tier1 or w in tier2:
            continue
        if not (MIN_LEN <= len(w) <= TIER3_MAX_LEN):
            continue
        if s > TIER3_MAX_BRODA:
            continue
        tier3.add(w)

    no_rank = len(frequency) + 1
    tier1_sorted = sorted(tier1, key=lambda w: (frequency.get(w, no_rank), w))
    tier2_sorted = sorted(tier2)
    tier3_sorted = sorted(tier3)
    ordered = tier1_sorted + tier2_sorted + tier3_sorted
    OUT_PATH.write_text(json.dumps(ordered))

    print(f"\nTIER 1 (school vocab):             {len(tier1):>7,}")
    print(f"TIER 2 (obscure + abbrev + Roman): {len(tier2):>7,}")
    print(f"TIER 3 (random acronyms):          {len(tier3):>7,}")
    print(f"total fill pool:                   {len(ordered):>7,}")
    print(f"\ntier 1 top 10 by frequency: {', '.join(tier1_sorted[:10])}")
    print(f"tier 2 sample:              {', '.join(tier2_sorted[:10])}")
    print(f"tier 3 sample:              {', '.join(tier3_sorted[:10])}")
    print(f"\nwritten -> {OUT_PATH.relative_to(HERE)}")


if __name__ == "__main__":
    main()
