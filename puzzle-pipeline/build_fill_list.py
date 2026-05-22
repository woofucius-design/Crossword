"""
Builds clean_fill.json — the non-theme fill word list for the puzzle generator.

The list is the intersection of two sources:
  1. A standard English dictionary (lowercase common words only — proper nouns,
     brand names, and titles are absent by construction).
  2. wordfreq frequency data, used to keep only reasonably common words.

The intersection guarantees: no pop-culture words (no proper nouns survive a
dictionary that contains none), and no obscure crosswordese (a frequency floor
removes rare entries). Output is sorted most-common-first so the grid filler
naturally prefers familiar words.
"""
import json
import re
from pathlib import Path

from wordfreq import zipf_frequency

HERE = Path(__file__).parent
DICT_PATH = HERE / "data" / "dictionary.txt"
OUT_PATH = HERE / "data" / "clean_fill.json"

MIN_LEN = 3
MAX_LEN = 10
# Zipf scale: 6 ~ "the", 4 ~ "apple", 3 ~ "lucid". 3.0 keeps words an
# average reader knows while dropping crosswordese like "odea" / "esne".
ZIPF_FLOOR = 3.0

# A short manual blocklist: dictionary words that are slurs / not puzzle-friendly.
BLOCKLIST = set()


def main() -> None:
    words = []
    with DICT_PATH.open() as fh:
        for raw in fh:
            word = raw.strip().lower()
            if not re.fullmatch(r"[a-z]+", word):
                continue
            if not (MIN_LEN <= len(word) <= MAX_LEN):
                continue
            if word in BLOCKLIST:
                continue
            zipf = zipf_frequency(word, "en")
            if zipf < ZIPF_FLOOR:
                continue
            words.append((word.upper(), zipf))

    words.sort(key=lambda pair: pair[1], reverse=True)
    ordered = [w for w, _ in words]

    OUT_PATH.write_text(json.dumps(ordered))

    by_len: dict[int, int] = {}
    for w in ordered:
        by_len[len(w)] = by_len.get(len(w), 0) + 1
    print(f"clean fill words: {len(ordered)}")
    for length in range(MIN_LEN, MAX_LEN + 1):
        print(f"  len {length:2d}: {by_len.get(length, 0)}")
    print(f"written -> {OUT_PATH.relative_to(HERE)}")


if __name__ == "__main__":
    main()
