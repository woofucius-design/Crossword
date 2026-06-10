"""
Builds two enrichment files for SAT vocabulary used by the generator:

  data/sat_alt_clues.json
    Multiple clue phrasings per SAT word so successive puzzles vary.
    Sources combined:
      1. sat (the freevocab clue already in sat_words.json)
      2. webster (cleaned 1913 entry)
      3. wordnet (concise modern gloss)
      4. manual (entries in data/sat_alt_clues_manual.json if present)
    Format: { "LUCID": [{"text": "...", "source": "sat"}, {...}, ...] }

  data/sat_synonym_index.json
    Inverse map for the generator's clue-substitution pass. Combines two
    hand-curated sources:
      - data/sat_synonyms.json: fill words that are synonyms of a SAT
        word (SHREWD -> ASTUTE).
      - data/sat_short_defs.json: 2-3 word definition phrases, squashed
        to crossword answers (EASYTOGRASP -> LUCID). These are ADDED to
        the fill pool by build_fill_list.py even though no dictionary
        contains them.
    When the solver places one of these as fill, the puzzle clue becomes
    the SAT word itself ("Astute" / "Lucid"), turning fill into vocab
    review.
    Format: { "SHREWD":      {"satWords": ["ASTUTE"], "kind": "synonym"},
              "EASYTOGRASP": {"satWords": ["LUCID"],
                              "kind": "short_def",
                              "display": "EASY TO GRASP"} }
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SAT_SRC = HERE / "data" / "sat_words.json"
DEFS_SRC = HERE / "data" / "definitions.json"
SYN_SRC = HERE / "data" / "sat_synonyms.json"
SHORT_DEFS_SRC = HERE / "data" / "sat_short_defs.json"
MANUAL_CLUES = HERE / "data" / "sat_alt_clues_manual.json"
WEBSTER_SRC = HERE / "data" / "dict_webster.json"
OUT_CLUES = HERE / "data" / "sat_alt_clues.json"
OUT_SYN_INDEX = HERE / "data" / "sat_synonym_index.json"


def format_clue(text: str) -> str:
    """Normalize a definition into standard crossword clue style:
      - verbs lose the leading infinitive 'To ' ('To rub or wear off'
        -> 'Rub or wear off')
      - nouns lose the leading article ('A young girl' -> 'Young girl')
      - first letter capitalized
    """
    s = text.strip()
    s = re.sub(r"^(To|A|An|The)\s+", "", s, flags=re.IGNORECASE)
    return s[:1].upper() + s[1:] if s else s


def _clean_webster(text: str, max_len: int = 70) -> str:
    """Webster's 1913 entries are full of editorial scaffolding we strip
    before using as crossword clues:
      - Leading sense numbers "1. ", subject tags "(a) ", "(Rhet.) "
      - Trailing author citations "...is gone. Shak." / "Swift" — these
        are single Capitalized words at the very end after a period
      - Sense markers "2." "3." mid-entry — cut at the next sense
      - "[" examples, "--" appendices, ";" subordinate clauses
      - Hard-cap; if we'd cut mid-word, end on the previous word.
    """
    import re
    s = text
    # leading "1. " sense number
    s = re.sub(r"^\s*\d+\.\s*", "", s)
    # leading "(a)" / "(Rhet.)" markers
    s = re.sub(r"^\([^)]+\)\s*", "", s)
    # cut at next sense number
    s = re.split(r"\s\d+\.\s", s, maxsplit=1)[0]
    # cut at "[" "--" ";"
    s = re.split(r"\s+\[", s, maxsplit=1)[0]
    s = re.split(r"\s+--", s, maxsplit=1)[0]
    s = re.split(r";", s, maxsplit=1)[0]
    # collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    # strip trailing author citations: ". Shak" / ". Swift" — single
    # Capitalized word after the final period, no punctuation after
    s = re.sub(r"\.\s+[A-Z][a-z]+\.?\s*$", "", s).strip()
    s = s.rstrip(" .")
    if len(s) > max_len:
        s = s[:max_len].rsplit(" ", 1)[0] + "..."
    return s


def _wordnet_gloss(word: str) -> str | None:
    """Pull the first WordNet sense gloss for word, cleaned to clue length."""
    import re
    word_lower = word.lower()
    for path in [HERE / "data" / "wn_adj.txt", HERE / "data" / "wn_noun.txt",
                 HERE / "data" / "wn_verb.txt", HERE / "data" / "wn_adv.txt"]:
        if not path.exists():
            continue
        with path.open() as fh:
            for line in fh:
                if line.startswith("  "):
                    continue
                if "|" not in line:
                    continue
                head, _, gloss = line.partition("|")
                tokens = head.split()
                if len(tokens) < 4:
                    continue
                try:
                    w_cnt = int(tokens[3], 16)
                except ValueError:
                    continue
                # check if our word is a lemma in this synset
                for i in range(w_cnt):
                    w_idx = 4 + 2 * i
                    if w_idx >= len(tokens):
                        break
                    if tokens[w_idx].lower() == word_lower:
                        first = gloss.split(";")[0].strip()
                        first = re.sub(r"^\([^)]*\)\s*", "", first).strip()
                        first = re.sub(r"\s+", " ", first).strip(" .")
                        if len(first) > 80:
                            first = first[:80].rsplit(" ", 1)[0] + "..."
                        return first
    return None


def build_alt_clues() -> None:
    sat = json.loads(SAT_SRC.read_text())
    webster = {k.upper(): v for k, v in json.loads(WEBSTER_SRC.read_text()).items()}
    manual = json.loads(MANUAL_CLUES.read_text()) if MANUAL_CLUES.exists() else {}

    out: dict[str, list[dict]] = {}
    for entry in sat:
        word = entry["word"].upper()
        clues: list[dict] = []
        # 1. SAT bank's own clue
        if entry.get("clue"):
            clues.append({"text": entry["clue"], "source": "sat"})
        # 2. SAT bank's own definition (different phrasing from clue)
        if entry.get("definition"):
            clues.append({
                "text": entry["definition"].strip().rstrip(".").capitalize(),
                "source": "sat_def",
            })
        # 3. Webster's 1913 (cleaned)
        if word in webster and isinstance(webster[word], str):
            w_text = _clean_webster(webster[word])
            if w_text:
                clues.append({"text": w_text, "source": "webster"})
        # 4. WordNet
        wn = _wordnet_gloss(word)
        if wn:
            clues.append({"text": wn, "source": "wordnet"})
        # 5. Manual extension (data/sat_alt_clues_manual.json)
        for entry_text in manual.get(word, []):
            if isinstance(entry_text, str):
                clues.append({"text": entry_text, "source": "manual"})
            elif isinstance(entry_text, dict):
                clues.append(entry_text)
        # Crossword-format normalization, then dedupe by lowercased text
        seen: set[str] = set()
        unique: list[dict] = []
        for c in clues:
            c["text"] = format_clue(c["text"])
            key = c["text"].lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(c)
        if unique:
            out[word] = unique
    OUT_CLUES.write_text(json.dumps(out, indent=1))
    multi = sum(1 for v in out.values() if len(v) > 1)
    avg = sum(len(v) for v in out.values()) / max(len(out), 1)
    print(f"alt clues: {len(out):,} SAT words, "
          f"{multi:,} with multiple options ({100*multi/max(len(out),1):.0f}%), "
          f"avg {avg:.1f} clues/word")


def build_synonym_index() -> None:
    """Combined teaching index: synonyms + squashed short-definition
    phrases. Both map fill answer -> SAT word(s), with a kind tag so the
    generator can phrase the entry's definition correctly."""
    index: dict[str, dict] = {}

    syns = json.loads(SYN_SRC.read_text())
    for sat_word, synonyms in syns.items():
        for syn in synonyms:
            key = syn.upper().replace(" ", "")
            if not key.isalpha():
                continue
            slot = index.setdefault(key, {"satWords": [], "kind": "synonym"})
            if sat_word.upper() not in slot["satWords"]:
                slot["satWords"].append(sat_word.upper())

    short_defs = (
        json.loads(SHORT_DEFS_SRC.read_text())
        if SHORT_DEFS_SRC.exists() else {}
    )
    n_phrases = 0
    for sat_word, phrases in short_defs.items():
        for phrase in phrases:
            key = phrase.upper().replace(" ", "")
            if not key.isalpha() or len(key) > 15:
                continue
            slot = index.setdefault(
                key, {"satWords": [], "kind": "short_def", "display": phrase}
            )
            if sat_word.upper() not in slot["satWords"]:
                slot["satWords"].append(sat_word.upper())
            n_phrases += 1

    OUT_SYN_INDEX.write_text(json.dumps(index, indent=1, sort_keys=True))
    n_syn = sum(1 for v in index.values() if v["kind"] == "synonym")
    n_sd = sum(1 for v in index.values() if v["kind"] == "short_def")
    print(f"teaching index: {len(index):,} answers "
          f"({n_syn} synonyms, {n_sd} short-def phrases)")


def main() -> None:
    build_alt_clues()
    build_synonym_index()


if __name__ == "__main__":
    main()
