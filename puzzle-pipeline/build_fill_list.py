"""
Builds clean_fill.json from English ∩ Broda — the intersection of:
  - the 370k dwyl/english-words list (excludes proper nouns, brands, slang)
  - Peter Broda's 492k scored crossword wordlist (gives each word a score)

Why both? Either list alone fails:
  - Broda alone (or Crossword Nexus xwordlist) scores pop-culture / brands /
    internet slang at 50-100, so even high-score-only pools contain SNOOKI,
    BARTMAN, FML, TBILISI, MURICA.
  - English alone has no quality signal — the solver tries entries in pool
    order and there's no ordering hint to prefer common over obscure.
  - English ∩ Broda gives both: ~141k entries, every one is real English,
    each scored by Broda. The 349k Broda junk and 228k unscored English
    words drop out.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
ENGLISH_SRC = HERE / "data" / "english_words.txt"
BRODA_SRC = HERE / "data" / "broda_wordlist.txt"
OUT_PATH = HERE / "data" / "clean_fill.json"

MIN_SCORE = 50
MIN_LEN = 3
MAX_LEN = 15


def main() -> None:
    english = {
        w.strip().upper() for w in ENGLISH_SRC.open()
        if w.strip().isalpha()
    }
    print(f"English wordlist: {len(english):,}")

    scored: list[tuple[str, int]] = []
    junk_skipped = 0
    short_skipped = 0
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
                short_skipped += 1
                continue
            try:
                score = int(score_str)
            except ValueError:
                continue
            if score < MIN_SCORE:
                continue
            if word not in english:
                junk_skipped += 1
                continue
            scored.append((word, score))

    scored.sort(key=lambda p: (-p[1], p[0]))
    ordered = [w for w, _ in scored]
    OUT_PATH.write_text(json.dumps(ordered))

    by_len: dict[int, int] = {}
    for w in ordered:
        by_len[len(w)] = by_len.get(len(w), 0) + 1
    print(f"\nfill words: {len(ordered):,}  (Broda score >= {MIN_SCORE}, in English dict)")
    print(f"  skipped non-English (proper nouns / slang / brands): {junk_skipped:,}")
    print("\nlength distribution:")
    for length in range(MIN_LEN, MAX_LEN + 1):
        print(f"  len {length:2d}: {by_len.get(length, 0):>7,}")
    print(f"\ntop 10 (highest score): {', '.join(ordered[:10])}")
    print(f"written -> {OUT_PATH.relative_to(HERE)}")


if __name__ == "__main__":
    main()
