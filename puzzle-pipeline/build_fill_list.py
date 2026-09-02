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


def load_clueable() -> set[str]:
    """Every answer we can actually put a clue on.

    Having a definition is not enough: the generator refuses any clue that
    leaks its own answer, so an inflected form whose every gloss contains the
    root (SEVENS -> "...seven...", OILED -> "...oil...") has a definition and
    still ships blank. The predicate has to be "owns at least one
    NON-LEAKING candidate", mirroring the selection in generator.py.
    """
    from morphology import clue_leaks

    words: set[str] = set()

    # Hand and AI fill clues are written not to leak, but verify anyway —
    # cheap, and it keeps a bad hand clue from silently reaching a grid.
    for name in ("fill_clues_ai.json", "fill_clues.json"):
        path = HERE / "data" / name
        if path.exists():
            for w, clue in json.loads(path.read_text()).items():
                if clue and not clue_leaks(w, clue):
                    words.add(w)

    sat_path = HERE / "data" / "sat_words.json"
    if sat_path.exists():
        for e in json.loads(sat_path.read_text()):
            # SAT entries carry curated clues plus alternates; the bank is
            # the whole point of the app, so keep them and let the generator
            # pick among their candidates.
            words.add(e["word"])

    defs_path = HERE / "data" / "definitions.json"
    if defs_path.exists():
        for w, d in json.loads(defs_path.read_text()).items():
            if w in words:
                continue
            for cand in [d] + d.get("alternates", []):
                text = cand.get("definition", "")
                if text and not clue_leaks(w, text):
                    words.add(w)
                    break

    return words


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

    # SAT teaching boost: words in the synonym/short-def index go to the
    # very front of tier 1 so the solver prefers them over ordinary fill
    # whenever they fit — each one placed turns a fill slot into vocab
    # review (its clue becomes the SAT word). Short-def phrases like
    # EASYTOGRASP exist in no dictionary, so they're added to the pool
    # here.
    teach_path = HERE / "data" / "sat_synonym_index.json"
    teaching: set[str] = set()
    if teach_path.exists():
        teaching = {
            w for w in json.loads(teach_path.read_text())
            if w.isalpha() and MIN_LEN <= len(w) <= MAX_LEN
        }
        new_phrases = teaching - tier1 - tier2 - tier3
        tier1 |= teaching
        tier2 -= teaching
        tier3 -= teaching
        print(f"teaching words boosted to tier-1 front: {len(teaching):,} "
              f"({len(new_phrases)} new phrase entries)")

    # Cluability is a hard constraint, not a nice-to-have: an answer with no
    # clue source cannot be presented to a solver. Without this the generator
    # was free to place any of ~61k unclueable entries, and 6% of all placed
    # words shipped with a blank clue — affecting 89% of generated puzzles.
    clueable = load_clueable()
    before = len(tier1) + len(tier2) + len(tier3)
    tier1 &= clueable
    tier2 &= clueable
    tier3 &= clueable
    dropped = before - (len(tier1) + len(tier2) + len(tier3))
    print(f"dropped as unclueable:              {dropped:>7,}")

    no_rank = len(freq) + 1
    tier1_sorted = sorted(
        tier1, key=lambda w: (w not in teaching, freq.get(w, no_rank), w)
    )
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
