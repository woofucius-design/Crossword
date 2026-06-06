"""
Builds clean_fill.json from the Crossword Nexus collaborative word list — a
real crossword-quality, scored wordlist (score 0-100, higher = better) of the
kind used by professional constructors. It includes common words, proper
nouns, and phrases that show up in real NYT-style crosswords.

We keep entries with score >= MIN_SCORE; the list is sorted score-descending,
so the solver tries the cleanest, most familiar entries first.

Source: https://github.com/Crossword-Nexus/collaborative-word-list
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "data" / "xwordlist.dict"
ENGLISH_DICT = HERE / "data" / "english_words.txt"
OUT_PATH = HERE / "data" / "clean_fill.json"

MIN_SCORE = 50    # 50+ cuts low-score abbreviation/partial fill.
MIN_LEN = 3
MAX_LEN = 15


def main() -> None:
    english = {w.strip().upper() for w in ENGLISH_DICT.open() if w.strip()}
    scored: list[tuple[str, int, bool]] = []  # (word, score, is_english)
    with SRC.open() as fh:
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
            scored.append((word, score, word in english))

    # Sort by score descending, tie-broken by English-dict first. At equal
    # score (e.g. 50-score TBILISI vs 50-score ALEE), the English word wins
    # and gets a lower ID, so the solver's natural lowest-ID-first iteration
    # prefers it. We DON'T put all English ahead of all non-English: many
    # high-score crossword-glue entries (often pop-culture but well-loved by
    # constructors) score 80+ and aren't in the English dict, and demoting
    # them en masse strangles the solver.
    scored.sort(key=lambda p: (-p[1], not p[2], p[0]))
    ordered = [w for w, _, _ in scored]
    english_count = sum(1 for _, _, is_en in scored if is_en)
    OUT_PATH.write_text(json.dumps(ordered))

    by_len: dict[int, int] = {}
    for w in ordered:
        by_len[len(w)] = by_len.get(len(w), 0) + 1
    print(f"fill words: {len(ordered):,}  (score >= {MIN_SCORE})")
    print(f"  English-dict (preferred): {english_count:,}")
    print(f"  non-dict (fallback):      {len(ordered) - english_count:,}")
    for length in range(MIN_LEN, MAX_LEN + 1):
        print(f"  len {length:2d}: {by_len.get(length, 0):>7,}")
    print(f"top 10 (highest score): {', '.join(ordered[:10])}")
    print(f"written -> {OUT_PATH.relative_to(HERE)}")


if __name__ == "__main__":
    main()
