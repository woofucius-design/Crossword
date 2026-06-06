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
OUT_PATH = HERE / "data" / "clean_fill.json"

MIN_SCORE = 50    # 50+ cuts low-score abbreviation/partial fill.
MIN_LEN = 3
MAX_LEN = 15


def main() -> None:
    scored: list[tuple[str, int]] = []
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
            scored.append((word, score))

    scored.sort(key=lambda p: (-p[1], p[0]))
    ordered = [w for w, _ in scored]
    OUT_PATH.write_text(json.dumps(ordered))

    by_len: dict[int, int] = {}
    for w in ordered:
        by_len[len(w)] = by_len.get(len(w), 0) + 1
    print(f"fill words: {len(ordered):,}  (score >= {MIN_SCORE})")
    for length in range(MIN_LEN, MAX_LEN + 1):
        print(f"  len {length:2d}: {by_len.get(length, 0):>7,}")
    print(f"top 10 (highest score): {', '.join(ordered[:10])}")
    print(f"written -> {OUT_PATH.relative_to(HERE)}")


if __name__ == "__main__":
    main()
