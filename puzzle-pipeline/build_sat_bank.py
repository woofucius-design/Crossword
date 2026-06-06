"""
Build the SAT word bank from the freevocabulary.com list (5,014 entries),
overlaid on the original 30 hand-curated SAT entries.

Input: /tmp/freevocab.json (https://github.com/lrojas94/SAT-Words)
Output: data/sat_words.json — id, word, definition, partOfSpeech, clue

Rules:
- Keep the original 30 entries with their hand-written clues (overwrite the
  definition if the new source has a better one — actually we keep originals
  intact since they were hand-curated).
- Add the rest from freevocab. UPPERCASE words, strip trailing whitespace
  from line-wrap artifacts in definitions, derive a short clue from the
  definition (truncate at first period or ~70 chars).
- Skip non-alphabetic words (hyphens, apostrophes, spaces). Skip length < 3.
- Skip any duplicates of the original 30 (case-insensitive).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path("/tmp/freevocab.json")
DST = HERE / "data" / "sat_words.json"

POS_MAP = {
    "n.": "noun",
    "adj.": "adjective",
    "v.": "verb",
    "adv.": "adverb",
    "conj.": "conjunction",
    "prep.": "preposition",
    "interj.": "interjection",
    "inter.": "interjection",
    "ad.": "adverb",
    "pa.": "verb",
    "Latin.": "phrase",
    "Greek.": "phrase",
}


def clean_definition(d: str) -> str:
    """Collapse internal multi-spaces and trim trailing whitespace."""
    d = re.sub(r"\s+", " ", d).strip()
    if d.endswith(","):  # half-sentence artifact in source
        d = d.rstrip(",") + "..."
    return d


def make_clue(definition: str) -> str:
    """A short NYT-style clue from the definition: first clause or ~70 chars,
    first letter capitalized, no trailing period."""
    # take up to first ';' or '.' that's not followed by abbreviation
    short = re.split(r"[;.]", definition, maxsplit=1)[0].strip()
    if len(short) > 70:
        short = short[:70].rsplit(" ", 1)[0]
    short = short.rstrip(".,;: ")
    return short[:1].upper() + short[1:] if short else definition[:60]


def main() -> None:
    raw = json.loads(SRC.read_text())
    originals = json.loads(DST.read_text())
    original_words = {o["word"].upper() for o in originals}

    bank: list[dict] = list(originals)  # keep curated 30 intact
    next_id = max(o["id"] for o in originals) + 1

    skipped_non_alpha = 0
    skipped_dup = 0
    skipped_short = 0
    for entry in raw:
        word = entry["word"].strip().upper()
        if not word.isalpha():
            skipped_non_alpha += 1
            continue
        if len(word) < 3:
            skipped_short += 1
            continue
        if word in original_words:
            skipped_dup += 1
            continue
        original_words.add(word)
        pos = POS_MAP.get(entry["type"], entry["type"].rstrip(".") or "unknown")
        definition = clean_definition(entry["definition"])
        clue = make_clue(definition)
        bank.append({
            "id": next_id,
            "word": word,
            "definition": definition,
            "partOfSpeech": pos,
            "clue": clue,
        })
        next_id += 1

    DST.write_text(json.dumps(bank, indent=2))
    print(f"input entries:     {len(raw):,}")
    print(f"  skipped non-alpha: {skipped_non_alpha}")
    print(f"  skipped short:     {skipped_short}")
    print(f"  skipped duplicate: {skipped_dup}")
    print(f"output entries:    {len(bank):,}  ({len(originals)} curated + new)")
    from collections import Counter
    lens = Counter(len(w["word"]) for w in bank)
    print("length distribution (lengths 3..15):")
    for L in range(3, 16):
        print(f"  {L:2}: {lens.get(L, 0)}")


if __name__ == "__main__":
    main()
