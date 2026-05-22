"""
Builds clean_fill.json — the fill word list for the puzzle generator.

Uses the FULL English dictionary (~274k words from the npm `word-list`
package). That dictionary is entirely lowercase common words, so proper
nouns, brand names, and titles are absent by construction — a puzzle filled
from it cannot contain a pop-culture word.

Words are ordered most-common-first using wordfreq, so the generator naturally
prefers familiar words and only reaches for obscure ones when a hard grid
forces it. Nothing is dropped for being rare: a big pool is what makes tightly
interlocked, fully-checked grids fillable.
"""
import json
import re
from pathlib import Path

from wordfreq import zipf_frequency

HERE = Path(__file__).parent
DICT_PATH = HERE / "data" / "dictionary.txt"
OUT_PATH = HERE / "data" / "clean_fill.json"

MIN_LEN = 3
MAX_LEN = 15


def main() -> None:
    scored: list[tuple[str, float]] = []
    with DICT_PATH.open() as fh:
        for raw in fh:
            word = raw.strip().lower()
            if not re.fullmatch(r"[a-z]+", word):
                continue
            if not (MIN_LEN <= len(word) <= MAX_LEN):
                continue
            scored.append((word.upper(), zipf_frequency(word, "en")))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    ordered = [w for w, _ in scored]
    OUT_PATH.write_text(json.dumps(ordered))

    by_len: dict[int, int] = {}
    for w in ordered:
        by_len[len(w)] = by_len.get(len(w), 0) + 1
    common = sum(1 for _, z in scored if z >= 3.0)
    print(f"fill words: {len(ordered)}  ({common} common, zipf >= 3.0)")
    for length in range(MIN_LEN, MAX_LEN + 1):
        print(f"  len {length:2d}: {by_len.get(length, 0)}")
    print(f"written -> {OUT_PATH.relative_to(HERE)}")


if __name__ == "__main__":
    main()
