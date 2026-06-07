"""
Builds data/definitions.json — a unified word -> definition map drawing
from multiple offline sources, used as raw material for cluing fill words
and (more immediately) for evaluating the quality of words appearing in
generated puzzles.

Sources, in priority order:
  1. data/sat_words.json — the freevocabulary SAT bank (5,000 entries),
     hand-shaped definitions targeted at students.
  2. data/dict_webster.json — Webster's Unabridged 1913 in JSON (102k
     entries via matthewreagan/WebstersEnglishDictionary). Period
     phrasing but comprehensive English coverage including educational
     proper nouns (Caesar, Nile, Egypt).

A word in source 1 wins over source 2. Modern abbreviations (GPS, MRI,
NSC) and recent proper nouns aren't in either source — those go in
data/definitions_missing.txt for follow-up.

Output schema:
  {WORD: {"definition": "...", "source": "sat" | "webster", "pos": "..."}}
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SAT_SRC = HERE / "data" / "sat_words.json"
WEBSTER_SRC = HERE / "data" / "dict_webster.json"
POOL_SRC = HERE / "data" / "clean_fill.json"
OUT_PATH = HERE / "data" / "definitions.json"
MISSING_PATH = HERE / "data" / "definitions_missing.txt"


def clean_webster(text: str) -> str:
    """Webster's 1913 entries include sense numbers, examples, and citations.
    Take the first sense's gloss only, drop citations, condense whitespace,
    truncate to ~140 chars so it reads as a clue-like definition."""
    # strip leading sense number "1. "
    text = re.sub(r"^\s*\d+\.\s*", "", text)
    # cut at next sense number "2. " etc.
    text = re.split(r"\s\d+\.\s", text, maxsplit=1)[0]
    # cut at example markers
    text = re.split(r"\s+\[", text, maxsplit=1)[0]
    text = re.split(r"\s+--", text, maxsplit=1)[0]
    text = re.sub(r"\s+", " ", text).strip(" .")
    if len(text) > 140:
        text = text[:140].rsplit(" ", 1)[0] + "..."
    return text


def main() -> None:
    sat = json.loads(SAT_SRC.read_text())
    webster = json.loads(WEBSTER_SRC.read_text())
    # Normalize Webster's keys to UPPER for our lookup.
    webster_upper = {k.upper(): v for k, v in webster.items()}

    out: dict[str, dict] = {}
    for entry in sat:
        word = entry["word"].upper()
        out[word] = {
            "definition": entry.get("definition", "").strip(),
            "source": "sat",
            "pos": entry.get("partOfSpeech", ""),
        }

    webster_added = 0
    for word, raw in webster_upper.items():
        if word in out:
            continue
        if not raw or not isinstance(raw, str):
            continue
        defn = clean_webster(raw)
        if defn:
            out[word] = {
                "definition": defn,
                "source": "webster",
                "pos": "",
            }
            webster_added += 1

    OUT_PATH.write_text(json.dumps(out, indent=1))

    # Coverage report: which pool words don't have a definition?
    if POOL_SRC.exists():
        pool = json.loads(POOL_SRC.read_text())
        missing = [w for w in pool if w.upper() not in out]
        MISSING_PATH.write_text("\n".join(missing[:50_000]) + "\n")
        print(f"pool size: {len(pool):,}")
        print(f"defined:   {len(pool) - len(missing):,}  "
              f"({100 * (len(pool) - len(missing)) / len(pool):.0f}%)")
        print(f"missing:   {len(missing):,}  "
              f"(first 50k written to {MISSING_PATH.relative_to(HERE)})")
    print(f"\nSAT bank entries:     {len(sat):,}")
    print(f"Webster entries added: {webster_added:,}")
    print(f"total definitions:    {len(out):,}")
    print(f"written -> {OUT_PATH.relative_to(HERE)}")


if __name__ == "__main__":
    main()
