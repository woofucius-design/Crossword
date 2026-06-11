"""
Auto-generates short-definition phrases for every SAT word in
data/sat_words.json by mining the definition sources we already have:

  - SAT bank's own clue + definition fields (crossword-flavored already)
  - WordNet first-sense gloss (concise modern phrasing)
  - Webster's 1913 cleaned first clause

For each source, definition strings are split into short clauses
(comma / semicolon / period boundaries), leading articles and stopwords
trimmed, then squashed to alphabetic-only with no spaces. Anything
between MIN_LEN..MAX_LEN characters survives.

Output adds to data/sat_short_defs.json — keyed by SAT word, value is
a list of display strings (so the original spacing is preserved for
the puzzle's `display` field). The squashed alphabetic answer is what
goes in the pool.

This file augments the existing hand-curated entries; manual ones win
on duplicates.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SAT_SRC = HERE / "data" / "sat_words.json"
WEBSTER_SRC = HERE / "data" / "dict_webster.json"
WN_FILES = [
    HERE / "data" / "wn_noun.txt",
    HERE / "data" / "wn_verb.txt",
    HERE / "data" / "wn_adj.txt",
    HERE / "data" / "wn_adv.txt",
]
MANUAL_SHORT_DEFS = HERE / "data" / "sat_short_defs_manual.json"
OUT_PATH = HERE / "data" / "sat_short_defs.json"

MIN_LEN = 6
MAX_LEN = 15

# Words that should drop from the start of a candidate phrase. Internal
# stopwords are kept because we don't want to mangle phrasing — the
# pool entry compresses them away anyway when we strip non-letters.
LEADING_DROPS = {
    "to", "a", "an", "the", "of", "in", "on", "at", "by", "for", "is",
    "are", "was", "were", "being", "be", "been", "very", "any", "some",
    "as", "having", "having", "becoming", "showing", "characterized",
    "marked", "relating", "pertaining", "or", "and", "that", "which",
    "who", "whom", "having", "into",
}


def squash(text: str) -> str:
    """ABCDEF — alphabetic only, uppercase. The puzzle answer form."""
    return re.sub(r"[^A-Za-z]", "", text).upper()


def split_clauses(text: str) -> list[str]:
    """Split a definition into short candidate clauses."""
    # Drop trailing parenthetical asides like (Bot.) or (Mus.)
    text = re.sub(r"\([^)]*\)", " ", text)
    # Split on , ; . — and "; " etc.
    parts = re.split(r"[,;.:|]+", text)
    return [p.strip() for p in parts if p.strip()]


def trim_leading(clause: str) -> str:
    tokens = re.findall(r"[A-Za-z]+", clause)
    while tokens and tokens[0].lower() in LEADING_DROPS:
        tokens.pop(0)
    return " ".join(tokens)


def phrase_candidates(definition: str) -> list[str]:
    """All viable (display, squashed) candidates from one definition string."""
    out: list[str] = []
    for clause in split_clauses(definition):
        trimmed = trim_leading(clause)
        if not trimmed:
            continue
        tokens = trimmed.split()
        # Reject Webster syllable artifacts: "Op u lent ly", "Ver bose ly"
        # — sequences with several short tokens that look like syllables.
        short_tokens = sum(1 for t in tokens if len(t) <= 3)
        if len(tokens) >= 3 and short_tokens >= len(tokens) - 1:
            continue
        sq = squash(trimmed)
        if not (MIN_LEN <= len(sq) <= MAX_LEN):
            continue
        # Skip single-word clauses that are already common English — they'd
        # already cover themselves via the dictionary. We want multi-word
        # phrases like EASYTOFOLLOW or KNOWSTHEROPES, not bare nouns.
        if len(tokens) < 2:
            continue
        out.append(trimmed)
    return out


def wordnet_gloss(word_lower: str) -> str | None:
    for path in WN_FILES:
        if not path.exists():
            continue
        with path.open() as fh:
            for line in fh:
                if line.startswith("  ") or "|" not in line:
                    continue
                head, _, gloss = line.partition("|")
                tokens = head.split()
                if len(tokens) < 4:
                    continue
                try:
                    w_cnt = int(tokens[3], 16)
                except ValueError:
                    continue
                for i in range(w_cnt):
                    w_idx = 4 + 2 * i
                    if w_idx >= len(tokens):
                        break
                    if tokens[w_idx].lower() == word_lower:
                        return gloss.strip()
    return None


def main() -> None:
    sat = json.loads(SAT_SRC.read_text())
    webster = {k.upper(): v for k, v in json.loads(WEBSTER_SRC.read_text()).items()}
    manual = (
        json.loads(MANUAL_SHORT_DEFS.read_text())
        if MANUAL_SHORT_DEFS.exists() else {}
    )

    out: dict[str, list[str]] = {}
    n_words = 0
    n_total = 0
    for entry in sat:
        word = entry["word"].upper()
        # Pool the definition sources we have for this SAT word.
        sources: list[str] = []
        if entry.get("clue"):
            sources.append(entry["clue"])
        if entry.get("definition"):
            sources.append(entry["definition"])
        if word in webster and isinstance(webster[word], str):
            sources.append(webster[word])
        wn = wordnet_gloss(word.lower())
        if wn:
            sources.append(wn)

        candidates: list[str] = []
        seen: set[str] = set()
        # Manual entries win
        for phrase in manual.get(word, []):
            sq = squash(phrase)
            if MIN_LEN <= len(sq) <= MAX_LEN and sq not in seen:
                candidates.append(phrase)
                seen.add(sq)
        # Then mined phrases
        for src in sources:
            for phrase in phrase_candidates(src):
                sq = squash(phrase)
                if sq in seen:
                    continue
                # Reject phrases that contain the SAT word itself
                if word.lower() in phrase.lower():
                    continue
                seen.add(sq)
                candidates.append(phrase)
                if len(candidates) >= 8:
                    break
            if len(candidates) >= 8:
                break

        if candidates:
            out[word] = candidates
            n_words += 1
            n_total += len(candidates)

    OUT_PATH.write_text(json.dumps(out, indent=1))
    print(f"short defs: {n_words:,} SAT words covered, "
          f"{n_total:,} phrases total, avg {n_total/max(n_words,1):.1f}/word")
    print()
    print("Samples:")
    sat_words = [e["word"].upper() for e in sat[:30]]
    for w in sat_words[:8]:
        phrases = out.get(w, [])
        print(f"  {w:<12} -> {phrases[:4]}")


if __name__ == "__main__":
    main()
