"""
Clue-quality linter. Scans every clue source for mechanical defects:

  citation   — dictionary cross-references and scripture cites that leaked
               into clue text ("See Rostrum, 2", "Of Lie. See lain.",
               "Acts viii", "Ps. lxviii")
  fragment   — teaching phrases that start mid-clause ("but more remote")
  grammar    — inflection-engine artifacts ("exerciseses", "Someones who
               works", plural subject + singular relative verb)
  typo       — tokens not found in the English wordlist
  trivial    — clue so short it can't stand alone ("Do" for ADO)

Run:  python3 lint_clues.py            # report only
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

CITATION = re.compile(
    r"(\bSee [A-Z]|\bCf\.|\bpl\. of\b|^Of [A-Z][a-z]+\.?$|^Of [A-Z][a-z]+\."
    r"|\b(?:Acts|Ps|Gen|Matt|Cor|Rom|Luke|John|Rev|Deut|Exod|Isa)\.? [ivxlc]+\b"
    r"|\bimp\. & p\. p\.|\bp\. p\. of\b|\bimp\. of\b)"
)
LEAD_CONJ = re.compile(r"^(but|than|nor|yet|whereas|unless|whilst)\b", re.I)
DOUBLE_PLURAL = re.compile(r"\b\w+(?:ses|xes|zes|ches|shes)es\b|\b\w+eses\b")
BAD_PRONOUN = re.compile(r"\b(Someones|Anyones|Somebodies|Ones who \w+s\b)")
PLURAL_SING_VERB = re.compile(
    r"\b(?:women|men|people|things|ones|persons)\s+who\s+\w+?(?<!s)s\b", re.I
)


def load_wordlist() -> set[str]:
    words = set()
    for line in (DATA / "english_words.txt").read_text().splitlines():
        words.add(line.strip().lower())
    return words


def lint_text(text: str, wordlist: set[str]) -> list[str]:
    flags = []
    if CITATION.search(text):
        flags.append("citation")
    if DOUBLE_PLURAL.search(text):
        flags.append("grammar")
    if BAD_PRONOUN.search(text):
        flags.append("grammar")
    if PLURAL_SING_VERB.search(text):
        flags.append("grammar")
    if len(text.strip()) <= 3:
        flags.append("trivial")
    toks = re.findall(r"[A-Za-z]+", text)
    for t in toks:
        tl = t.lower()
        if len(tl) >= 5 and tl not in wordlist and not t[0].isupper():
            flags.append(f"typo:{t}")
            break
    return flags


def main() -> None:
    wl = load_wordlist()
    stats: Counter = Counter()
    samples: dict[str, list[str]] = {}

    def record(src: str, key: str, text: str) -> None:
        for f in lint_text(text, wl):
            kind = f.split(":")[0]
            stats[f"{src}:{kind}"] += 1
            samples.setdefault(f"{src}:{kind}", [])
            if len(samples[f"{src}:{kind}"]) < 6:
                samples[f"{src}:{kind}"].append(f"{key}: {text[:70]!r} [{f}]")

    # 1. sat_words.json — the curated bank
    for e in json.loads((DATA / "sat_words.json").read_text()):
        record("sat_bank", e["word"], e.get("clue", ""))
        record("sat_bank", e["word"], e.get("definition", ""))

    # 2. sat_alt_clues.json
    for w, alts in json.loads((DATA / "sat_alt_clues.json").read_text()).items():
        for a in alts:
            record("sat_alts", w, a.get("text", ""))

    # 3. sat_short_defs.json — teaching phrases (also check mid-clause starts)
    for w, phrases in json.loads((DATA / "sat_short_defs.json").read_text()).items():
        for p in phrases:
            record("short_defs", w, p)
            if LEAD_CONJ.search(p.strip()):
                stats["short_defs:fragment"] += 1
                samples.setdefault("short_defs:fragment", [])
                if len(samples["short_defs:fragment"]) < 6:
                    samples["short_defs:fragment"].append(f"{w}: {p!r}")

    # 4. definitions.json — primary + alternates
    defs = json.loads((DATA / "definitions.json").read_text())
    for w, d in defs.items():
        for cand in [d] + d.get("alternates", []):
            record(f"defs_{cand.get('source','?')}", w, cand.get("definition", ""))

    # 5. fill_clues_ai.json
    for w, c in json.loads((DATA / "fill_clues_ai.json").read_text()).items():
        record("hand_ai", w, c)

    print("defects by source:kind")
    for k, n in stats.most_common():
        print(f"  {k:<28} {n:>6}")
    print()
    for k in sorted(samples):
        print(f"--- {k} ---")
        for s in samples[k]:
            print(f"  {s}")


if __name__ == "__main__":
    main()
