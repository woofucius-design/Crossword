"""
Shared rule: a clue must not contain any morphological form of its answer.
A crossword clue that gives away the answer's root word is editorially
broken — "Acts of grasping" for GRASPS, "One who elopes" for ELOPER,
"Expressed admiration by uttering 'aah'" for AAHED.

morph_forms(word)  -> set[str]
    All inflected/derived forms of word's lemma, across noun/verb/adj/adv.
    Computed via lemminflect, with conservative lemma resolution so
    irregulars round-trip (wear -> wore/wears/wearing/worn).

clue_leaks(answer, clue) -> bool
    True iff `clue` contains any morph_form(answer) as a whole word
    (case-insensitive).

Usable both at definition-build time (enrich_definitions drops leaking
inflection clues) and at puzzle assembly time (generator.to_puzzle picks
a non-leaking alt clue for SAT vocab, blanks the clue for fill when its
sole definition leaks).
"""
from __future__ import annotations

import functools
import re

import lemminflect


_POS_LIST = ("VERB", "NOUN", "ADJ", "ADV")
_TAG_LIST = (
    "VB", "VBD", "VBG", "VBZ", "VBN",
    "NN", "NNS",
    "JJ", "JJR", "JJS",
    "RB", "RBR", "RBS",
)


def _safe_lemma(word: str, upos: str) -> tuple[str, ...]:
    if not word:
        return ()
    try:
        return tuple(lemminflect.getLemma(word, upos) or ())
    except Exception:
        return ()


def _safe_inflect(lemma: str, tag: str) -> tuple[str, ...]:
    if not lemma:
        return ()
    try:
        return tuple(lemminflect.getInflection(lemma, tag) or ())
    except Exception:
        return ()


@functools.lru_cache(maxsize=65536)
def morph_forms(word: str) -> frozenset[str]:
    """All lowercase morphological forms of `word` (the word itself, every
    lemma it resolves to under each part of speech, and every inflection
    of those lemmas). Lemminflect failures are skipped silently."""
    a = word.lower()
    forms: set[str] = {a}
    for upos in _POS_LIST:
        for lemma in _safe_lemma(a, upos):
            if not lemma:
                continue
            forms.add(lemma)
            for tag in _TAG_LIST:
                for f in _safe_inflect(lemma, tag):
                    forms.add(f.lower())
    return frozenset(f for f in forms if f and f.isalpha())


@functools.lru_cache(maxsize=65536)
def _leak_pattern(word: str) -> re.Pattern[str] | None:
    forms = morph_forms(word)
    if not forms:
        return None
    return re.compile(
        r"\b(" + "|".join(re.escape(f) for f in forms) + r")\b",
        re.IGNORECASE,
    )


try:
    from nltk.stem.snowball import SnowballStemmer
    _STEMMER = SnowballStemmer("english")
except Exception:  # pragma: no cover — nltk always present in pipeline env
    _STEMMER = None


@functools.lru_cache(maxsize=65536)
def _stem(word: str) -> str:
    if _STEMMER is None:
        return word.lower()
    try:
        return _STEMMER.stem(word.lower())
    except Exception:
        return word.lower()


def clue_leaks(answer: str, clue: str) -> bool:
    """True if `clue` contains any morphological form of `answer` as a whole
    word, or a word sharing the answer's derivational ROOT. Inflection
    catches "Acts of grasping" leaking GRASPS; stemming catches
    "keep secret or private" leaking SECRETIVE — derived answers must not
    be clued with their root family. False for empty clue."""
    if not clue:
        return False
    pat = _leak_pattern(answer)
    if pat is not None and pat.search(clue) is not None:
        return True
    # Root-family check via Snowball stems. Guard against tiny stems
    # (<=3 chars) that would fire on unrelated words.
    ans_stem = _stem(answer)
    if len(ans_stem) <= 3:
        return False
    for tok in re.findall(r"[A-Za-z]+", clue):
        if len(tok) >= 4 and _stem(tok) == ans_stem:
            return True
    return False
