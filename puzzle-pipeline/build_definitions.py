"""
Builds data/definitions.json — unified word -> definition map from:

  1. data/sat_words.json — SAT freevocab bank (5k entries), top priority.
  2. data/wn_{noun,verb,adj,adv}.txt — Princeton WordNet data files in raw
     format. ~117k entries with concise modern definitions. Covers
     post-1913 vocabulary the Webster source misses (ABLATE, ABSEIL,
     ABSORBANCE, ACCESSORIZE).
  3. data/dict_webster.json — Webster's Unabridged 1913 in JSON (102k
     entries). Comprehensive but archaic phrasing.

Higher-numbered source wins only when no lower-numbered source has it.
SAT entries override others (curated clue text).

Definition cleaning:
  - WordNet glosses are already concise; we just take the first sense and
    strip example sentences ("...; \"example here\"").
  - Webster entries get sense-number stripped, examples cut, citations
    removed, hard-capped at 80 chars (down from 140 to read more like a
    crossword clue).
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
POOL_SRC = HERE / "data" / "clean_fill.json"
OUT_PATH = HERE / "data" / "definitions.json"
MISSING_PATH = HERE / "data" / "definitions_missing.txt"

MAX_CLUE_LEN = 80


def format_clue(text: str) -> str:
    """Standard crossword clue style: drop leading infinitive 'To ' and
    articles 'A '/'An '/'The ', capitalize first letter. 'To rub or wear
    off' -> 'Rub or wear off'; 'A young girl' -> 'Young girl'."""
    s = text.strip()
    s = re.sub(r"^(To|A|An|The)\s+", "", s, flags=re.IGNORECASE)
    return s[:1].upper() + s[1:] if s else s


def clean_webster(text: str) -> str:
    """See build_sat_extras._clean_webster — same logic kept in sync."""
    s = text
    s = re.sub(r"^\s*\d+\.\s*", "", s)
    s = re.sub(r"^\([^)]+\)\s*", "", s)
    s = re.split(r"\s\d+\.\s", s, maxsplit=1)[0]
    s = re.split(r"\s+\[", s, maxsplit=1)[0]
    s = re.split(r"\s+--", s, maxsplit=1)[0]
    s = re.split(r";", s, maxsplit=1)[0]
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\.\s+[A-Z][a-z]+\.?\s*$", "", s).strip()
    s = s.rstrip(" .")
    if len(s) > MAX_CLUE_LEN:
        s = s[:MAX_CLUE_LEN].rsplit(" ", 1)[0] + "..."
    return s


def clean_wordnet_gloss(gloss: str) -> str:
    """WordNet glosses are already terse. Strip embedded examples (quoted
    sentences) and condense whitespace."""
    parts = gloss.split(";")
    primary = parts[0].strip()
    # Drop any leading "(...)" qualifier
    primary = re.sub(r"^\([^)]*\)\s*", "", primary).strip()
    primary = re.sub(r"\s+", " ", primary)
    primary = primary.strip(" .")
    if len(primary) > MAX_CLUE_LEN:
        primary = primary[:MAX_CLUE_LEN].rsplit(" ", 1)[0] + "..."
    return primary


def parse_wordnet_file(path: Path) -> dict[str, tuple[str, str]]:
    """Return {WORD_UPPER: (pos, gloss)} for the first sense of each lemma.

    WordNet data file lines look like:
      08 03 n 02 word1 0 word2 0 002 @ 12345 n 0000 | gloss text; "ex"
    Format: synset_offset lex_filenum ss_type w_cnt [word lex_id]* p_cnt
            [pointer]* | gloss
    """
    out: dict[str, tuple[str, str]] = {}
    pos_letter_to_name = {"n": "noun", "v": "verb", "a": "adjective",
                          "s": "adjective", "r": "adverb"}
    with path.open() as fh:
        for line in fh:
            if line.startswith("  "):  # license header
                continue
            if "|" not in line:
                continue
            head, _, gloss = line.partition("|")
            tokens = head.split()
            if len(tokens) < 4:
                continue
            try:
                pos_letter = tokens[2]
                w_cnt = int(tokens[3], 16)
            except (ValueError, IndexError):
                continue
            pos = pos_letter_to_name.get(pos_letter, pos_letter)
            cleaned_gloss = format_clue(clean_wordnet_gloss(gloss))
            if not cleaned_gloss:
                continue
            # Words start at index 4; each pair is (word, lex_id).
            for i in range(w_cnt):
                w_idx = 4 + 2 * i
                if w_idx >= len(tokens):
                    break
                word = tokens[w_idx].replace("_", " ")
                # We only handle single-word lemmas (no spaces / hyphens).
                if " " in word or "-" in word or "'" in word:
                    continue
                upper = word.upper()
                if upper not in out:
                    out[upper] = (pos, cleaned_gloss)
    return out


def main() -> None:
    sat = json.loads(SAT_SRC.read_text())
    webster = json.loads(WEBSTER_SRC.read_text())
    webster_upper = {k.upper(): v for k, v in webster.items()}

    # Collect EVERY available source per word. We rank them later by leak
    # status so the primary stored in definitions.json is always non-
    # leaking when at least one source is, and the rest are kept as
    # alternates the generator (or enrich) can fall back to.
    from collections import defaultdict
    by_word: dict[str, list[dict]] = defaultdict(list)

    for entry in sat:
        word = entry["word"].upper()
        clue = (entry.get("clue") or "").strip()
        defn = (entry.get("definition") or "").strip()
        if clue:
            by_word[word].append({
                "definition": clue,
                "source": "sat",
                "pos": entry.get("partOfSpeech", ""),
            })
        if defn and defn != clue:
            by_word[word].append({
                "definition": format_clue(defn),
                "source": "sat_def",
                "pos": entry.get("partOfSpeech", ""),
            })

    wn_added = 0
    for path in WN_FILES:
        if not path.exists():
            continue
        for word, (pos, gloss) in parse_wordnet_file(path).items():
            by_word[word].append({
                "definition": gloss,
                "source": "wordnet",
                "pos": pos,
            })
            wn_added += 1

    webster_added = 0
    for word, raw in webster_upper.items():
        if not raw or not isinstance(raw, str):
            continue
        defn = format_clue(clean_webster(raw))
        if defn:
            by_word[word].append({
                "definition": defn,
                "source": "webster",
                "pos": "",
            })
            webster_added += 1

    # Promote the first non-leaking candidate to primary; rest become
    # alternates. Iteration order = original priority (SAT > WordNet >
    # Webster) so within the non-leaking set we still favor the curated
    # source.
    from morphology import clue_leaks
    out: dict[str, dict] = {}
    n_promoted = 0
    n_all_leak = 0
    for word, candidates in by_word.items():
        # Dedupe by definition text so identical SAT clue / SAT def don't
        # both consume slots.
        seen_text: set[str] = set()
        unique: list[dict] = []
        for c in candidates:
            key = c["definition"].lower().strip()
            if not key or key in seen_text:
                continue
            seen_text.add(key)
            unique.append(c)
        non_leaking = [c for c in unique if not clue_leaks(word, c["definition"])]
        leaking = [c for c in unique if clue_leaks(word, c["definition"])]
        if non_leaking:
            primary = non_leaking[0]
            alternates = non_leaking[1:] + leaking
            if primary is not unique[0]:
                n_promoted += 1
        elif unique:
            primary = unique[0]
            alternates = unique[1:]
            n_all_leak += 1
        else:
            continue
        out[word] = {
            **primary,
            "alternates": alternates,
        }

    OUT_PATH.write_text(json.dumps(out, indent=1))
    print(f"  alt source promoted to primary (avoided leak): {n_promoted:,}")
    print(f"  all sources leak (kept best primary anyway):   {n_all_leak:,}")

    if POOL_SRC.exists():
        pool = json.loads(POOL_SRC.read_text())
        missing = [w for w in pool if w.upper() not in out]
        MISSING_PATH.write_text("\n".join(missing[:50_000]) + "\n")
        print(f"pool size: {len(pool):,}")
        print(f"defined:   {len(pool) - len(missing):,}  "
              f"({100 * (len(pool) - len(missing)) / len(pool):.0f}%)")
        print(f"missing:   {len(missing):,}")
    print(f"\nSAT bank entries:    {len(sat):,}")
    print(f"WordNet added:       {wn_added:,}")
    print(f"Webster added:       {webster_added:,}")
    print(f"total definitions:   {len(out):,}")
    print(f"written -> {OUT_PATH.relative_to(HERE)}")


if __name__ == "__main__":
    main()
