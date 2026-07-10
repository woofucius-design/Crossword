"""
Enriches data/definitions.json by deriving clues for inflected forms whose
base form is already defined. After Webster's 1913 + SAT bank we cover
102k entries (~29% of the 175k pool); the bulk of misses are conjugations
(USED, USING, ASKED) and plurals (YEARS, STATES, THINGS) whose stems do
have entries. Generates clue text like "Past tense of USE" by stripping
common suffixes and looking up the base.

Also adds dedicated handling for:
  - Roman numerals -> "Roman numeral 47" etc.
  - tier2_allow common abbreviations whose meanings we know

Inflection patterns covered (apply in order, first match wins):
  -S       -> trim S, look up plural   (CATS -> CAT, "Plural of CAT")
  -ES      -> trim ES                  (FOXES -> FOX, "Plural of FOX")
  -IES     -> -Y                       (STUDIES -> STUDY)
  -ED      -> trim ED, also try -E    (USED -> USE, "Past tense of USE")
  -IED     -> -Y                       (STUDIED -> STUDY)
  -ING     -> trim ING, also try -E   (USING -> USE)
  -ER      -> trim ER, also try -E    (USER -> USE)
  -EST     -> trim EST                 (BIGGEST -> BIG)
  -LY      -> trim LY                  (QUICKLY -> QUICK)
"""
from __future__ import annotations

import functools
import json
import re
from pathlib import Path

import lemminflect
import nltk

from morphology import clue_leaks

# Ensure the POS tagger model is available (no-op if already downloaded).
for _pkg in ("averaged_perceptron_tagger_eng", "averaged_perceptron_tagger"):
    try:
        nltk.download(_pkg, quiet=True)
    except Exception:
        pass

HERE = Path(__file__).parent
DEFS_PATH = HERE / "data" / "definitions.json"
POOL_PATH = HERE / "data" / "clean_fill.json"
TIER2_ALLOW = HERE / "data" / "tier2_allow.txt"


# Roman numeral check
def is_roman(word: str) -> bool:
    return word and all(c in "IVXLCDM" for c in word)


def roman_to_int(word: str) -> int:
    pairs = [
        ("M", 1000), ("CM", 900), ("D", 500), ("CD", 400),
        ("C", 100), ("XC", 90), ("L", 50), ("XL", 40),
        ("X", 10), ("IX", 9), ("V", 5), ("IV", 4), ("I", 1),
    ]
    i, n = 0, 0
    for sym, val in pairs:
        while word[i:i + len(sym)] == sym:
            n += val
            i += len(sym)
    return n if i == len(word) else 0


INFLECTION_RULES = [
    # (suffix to strip, base reconstructions to try)
    ("IES", ["Y"]),
    ("ES",  ["", "E"]),
    ("S",   [""]),
    ("IED", ["Y"]),
    ("ED",  ["", "E"]),
    ("ING", ["", "E"]),
    ("EST", ["", "E"]),
    ("ER",  ["", "E"]),
    ("LY",  [""]),
]

# Biography/proper-person senses: birth-death years, occupation-led
# glosses, biblical-figure phrasing. Never a safe base for inflection.
_BIO_SENSE = re.compile(
    r"\(\s*\d{4}\s*[-–]\s*\d{4}\s*\)"
    r"|\b(actor|actress|composer|singer|author|writer|poet|painter"
    r"|president|senator|king|queen|emperor|prophet|patriarch|deity"
    r"|god|goddess|saint|apostle)s?\b.*\b(18|19|20)\d\d\b"
    r"|first (children|son|daughter) of",
    re.IGNORECASE,
)

# Tokens we never inflect even at a coordinated head position — particles,
# prepositions, articles, light verbs — so "rub or wear OFF" keeps "off".
_NOINFLECT = {
    "off", "on", "in", "out", "up", "down", "through", "over", "away",
    "with", "to", "of", "at", "for", "into", "from", "about", "around",
    "upon", "forth", "by", "or", "and", "a", "an", "the", "as", "that",
    "be", "is", "are", "not", "without", "than",
}

_TAG = {"past": "VBD", "gerund": "VBG", "third": "VBZ", "plural": "NNS"}


def _resolve_kind(suffix: str, pos: str) -> str | None:
    """Map (suffix, root part-of-speech) to an inflection kind, or None when
    the combination doesn't make sense (so we skip rather than emit junk —
    e.g. -ED on a noun root like TALON)."""
    pos = (pos or "").lower()
    if suffix in ("IES", "ES", "S"):
        if pos == "verb":
            return "third"
        if pos == "noun":
            return "plural"
        return None
    if suffix in ("IED", "ED"):
        return "past" if pos == "verb" else None
    if suffix == "ING":
        return "gerund" if pos == "verb" else None
    if suffix == "EST":
        return "super" if pos in ("adjective", "adj") else None
    if suffix == "ER":
        if pos == "verb":
            return "agent"
        if pos in ("adjective", "adj"):
            return "comp"
        return None
    if suffix == "LY":
        return "adverb" if pos in ("adjective", "adj") else None
    return None


def _clean_root_def(definition: str) -> str:
    """First sense only, leading 'To/A/An/The' stripped, trailing period
    dropped, capped to clue length."""
    s = re.split(r"[.;]", definition, maxsplit=1)[0]
    s = re.sub(r"^(To|A|An|The)\s+", "", s.strip(), flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip(" .")
    # Drop tokens with no letters (e.g. a stray '*' in "Star-shaped
    # character * used in printing") so head detection lands on a real noun.
    s = " ".join(t for t in s.split() if re.search(r"[A-Za-z]", t))
    if len(s) > 70:
        s = s[:70].rsplit(" ", 1)[0]
        # A mid-phrase cut can leave a dangling function word or
        # participle ('...gastropod mollusks usually having'); trim back
        # to the last contentful token.
        toks = s.split()
        while toks and (toks[-1].rstrip(",").lower() in _NP_BOUNDARY
                        or toks[-1].rstrip(",").lower() in _DANGLE):
            toks.pop()
        s = " ".join(toks).rstrip(",")
    return s


@functools.lru_cache(maxsize=4096)
def _pos_tags(clean: str) -> tuple[str, ...]:
    """Penn-Treebank tags for a definition. Lowercased before tagging so a
    capitalized leading word isn't mis-tagged NNP (the tagger reads 'Search'
    as a proper noun but 'search' correctly as a verb/noun)."""
    from nltk import pos_tag
    toks = [re.sub(r"[^A-Za-z]", "", t).lower() for t in clean.split()]
    return tuple(tag for _w, tag in pos_tag(toks))


def _span_before_prep(tags: tuple[str, ...], tokens: list[str]) -> int:
    """Index of the first boundary after which the head no longer lives:
    a preposition, a relative pronoun (who/which/that), a finite verb that
    opens a relative/predicate clause, or a comma. For 'Person who founds
    some institution' this cuts at 'who' so the head is 'Person', not the
    object 'institution'."""
    _cut_tags = ("IN", "TO", "WP", "WDT", "WP$", "VBZ", "VBP", "VBD", "VBN")
    for i, (tok, tag) in enumerate(zip(tokens, tags)):
        if i > 0 and tag in _cut_tags:
            return i
        if tok.endswith((",", ";", ":")):
            return i + 1
    return len(tokens)


def _head_indices(tokens: list[str], tags: tuple[str, ...], want: str) -> list[int]:
    """Indices of the head word(s) to inflect. For verbs: the leading verb
    plus any verb coordinated to it. For nouns: the last noun before the
    first preposition plus nouns joined to it by and/or (so 'X or Y of Z'
    pluralizes X and Y, and 'police officer' pluralizes only officer)."""
    cut = _span_before_prep(tags, tokens)
    span = list(range(cut))
    if not span:
        return []
    if want == "verb":
        # Walk the coordination chain from the leading verb: 'say, state,
        # or perform again' must inflect all three. The chain extends
        # through commas and and/or; span_before_prep cuts at the first
        # comma so we walk raw tokens here instead. The tagger is
        # unreliable on fragments, so a token counts as a verb when
        # lemminflect's lexicon knows it as a base-form verb.
        # Stop at a preposition/relativizer: past it, or/and joins nouns
        # ('fasten, as with a rope or chain' must not inflect 'chain').
        stop_toks = {
            "as", "with", "by", "from", "into", "than", "that", "which",
            "who", "when", "while", "without", "upon", "after", "before",
            "at", "on", "in", "of", "for", "to",
        }
        idxs = [0]
        i = 1
        while i < len(tokens):
            low = tokens[i].rstrip(",").lower()
            if low in stop_toks or (
                i < len(tags) and tags[i] in ("IN", "TO", "WP", "WDT")
            ):
                break
            prev = tokens[i - 1]
            joined = prev.endswith(",") or prev.rstrip(",").lower() in ("or", "and")
            if joined and _is_base_verb(tokens[i]):
                idxs.append(i)
            i += 1
        return idxs
    nn_tags = ("NN", "NNS", "NNP", "NNPS")
    nouns = [i for i in span if tags[i] in nn_tags]
    if not nouns:
        return []
    head = {nouns[-1]}
    for i in nouns[:-1]:
        between = tags[i + 1: nouns[-1]]
        # Coordinated noun heads ('grief or sorrow') pluralize together,
        # but ONLY in a flat noun list. Any adjective in between means
        # these are coordinated MODIFIERS of the head ('freshwater or
        # marine or terrestrial gastropod mollusk') — pluralizing them
        # produced 'marines or terrestrial gastropods mollusk'.
        if "CC" in between and all(b in nn_tags or b == "CC" for b in between):
            head.add(i)
    return sorted(head)


# Pronoun heads pluralize idiomatically, not morphologically.
_PRONOUN_PLURAL = {
    "one": "Ones", "someone": "People", "somebody": "People",
    "anyone": "People", "anybody": "People", "person": "People",
}


def _is_base_verb(token: str) -> bool:
    """True if lemminflect's lexicon knows this token as a base-form verb
    (its own VERB lemma). Beats the POS tagger on headless fragments."""
    core = re.sub(r"[^A-Za-z]", "", token).lower()
    if not core:
        return False
    lemmas = lemminflect.getAllLemmas(core)
    return "VERB" in lemmas and core in lemmas["VERB"]


def _fix_relative_agreement(tokens: list[str], head_idx: int) -> None:
    """After pluralizing the head noun, a following 'who/that/which VBZ...'
    relative clause must agree: 'People who works' -> 'People who work'.
    Converts every 3rd-person-singular verb in the relative clause chain
    (including or-/and-coordinated ones) back to its plural (lemma) form."""
    rel = {"who", "that", "which"}
    i = head_idx + 1
    if i >= len(tokens) or tokens[i].lower().strip(",") not in rel:
        return
    i += 1
    expect_verb = True
    while i < len(tokens):
        core = re.sub(r"[^A-Za-z]", "", tokens[i])
        low = core.lower()
        if expect_verb and core:
            lemmas = lemminflect.getLemma(low, "VERB")
            if lemmas and lemmas[0] != low and low == (
                lemminflect.getInflection(lemmas[0], "VBZ") or [""])[0]:
                tokens[i] = tokens[i].replace(core, lemmas[0], 1)
        expect_verb = tokens[i].rstrip(",").lower() in ("or", "and")
        if not expect_verb and tokens[i].endswith(","):
            expect_verb = True
        i += 1


def _apply(tokens: list[str], idxs: list[int], tag: str,
           tags: tuple[str, ...] = ()) -> bool:
    """Inflect tokens at idxs in place to Penn `tag`. Returns True if any
    token actually changed (or was verified already in the target form)."""
    changed = False
    for i in idxs:
        core = re.sub(r"[^A-Za-z]", "", tokens[i])
        if not core or core.lower() in _NOINFLECT:
            continue
        low = core.lower()
        if tag == "NNS":
            # Pronoun-ish heads: 'Someone who...' -> 'People who...'
            # (before any POS guard — taggers call bare 'one' a number)
            if low in _PRONOUN_PLURAL:
                repl = _PRONOUN_PLURAL[low]
                if core[:1].islower():
                    repl = repl.lower()
                tokens[i] = tokens[i].replace(core, repl, 1)
                _fix_relative_agreement(tokens, i)
                changed = True
                continue
            # Already plural? ('exercises', 'articles') — the definition
            # already reads correctly for a plural headword; accept as-is
            # instead of double-pluralizing to 'exerciseses'.
            lemmas = lemminflect.getLemma(low, "NOUN")
            if lemmas and lemmas[0] != low and low == (
                    lemminflect.getInflection(lemmas[0], "NNS") or [""])[0]:
                changed = True
                continue
        # POS guard. Verbs: trust lemminflect's lexicon over the tagger
        # ('briefly' is never a verb, even when a fragment tagger says so).
        # Nouns: trust the tagger, which sees context.
        if tag.startswith("V") and not _is_base_verb(core):
            continue
        if tag == "NNS" and tags and i < len(tags) and tags[i] not in (
                "NN", "NNS", "NNP", "NNPS"):
            continue
        forms = lemminflect.getInflection(low, tag)
        if forms and forms[0].lower() != low:
            infl = forms[0]
            if core[:1].isupper():
                infl = infl[:1].upper() + infl[1:]
            tokens[i] = tokens[i].replace(core, infl, 1)
            if tag == "NNS":
                _fix_relative_agreement(tokens, i)
            changed = True
        elif forms and tag == "NNS" and forms[0].lower() == low:
            # invariant plural (fish, sheep): definition already reads
            # correctly for the plural headword
            changed = True
    return changed


# Noun-phrase boundary words: past any of these, tokens no longer belong
# to the head noun group. Closed lists beat the POS tagger on headless
# definition fragments (it tags 'mollusk' VBP, 'slimy' NNS...).
_NP_BOUNDARY = {
    "of", "in", "on", "at", "by", "for", "with", "from", "to", "into",
    "as", "upon", "over", "under", "between", "among", "through",
    "during", "without", "within", "against", "about", "around", "near",
    "off", "along", "across", "behind", "beyond", "concerning",
    "regarding", "that", "which", "who", "whom", "whose", "when",
    "where", "having", "used", "characterized", "marked", "found",
    "living", "growing", "intended", "being", "denoting", "resembling",
    "consisting", "containing", "serving", "made", "worn", "held",
}
_QUANTIFIERS = {"any", "one", "some", "several", "all", "each", "either"}

# Trailing tokens that read as dangling after a mid-phrase cut.
_DANGLE = {
    "a", "an", "the", "and", "or", "nor", "but", "usually", "often",
    "sometimes", "very", "more", "most", "such", "its", "their", "his",
    "her", "is", "are", "was", "were", "not", "no", "so", "than",
}


def _noun_head_indices(tokens: list[str]) -> list[int]:
    """Head of the leading noun phrase, via closed-list boundaries: the
    LAST token before the first preposition / relativizer / participle /
    -ly adverb / comma. 'Freshwater or marine or terrestrial gastropod
    mollusk usually having...' -> 'mollusk' (modifiers never pluralize).
    A pure two-noun coordination ('grief or sorrow' as the entire NP)
    pluralizes both heads."""
    window_end = len(tokens)
    for i, tok in enumerate(tokens):
        low = tok.rstrip(",").lower()
        if low in _NP_BOUNDARY or (low.endswith("ly") and len(low) > 4):
            window_end = i
            break
        if tok.endswith(","):
            window_end = i + 1
            break
    window = tokens[:window_end]
    if not window:
        return []
    if len(window) == 1:
        low0 = window[0].lower()
        if low0 in _PRONOUN_PLURAL:
            return [0]  # 'One who...' -> _apply's pronoun branch
        if low0 in _QUANTIFIERS:
            return []   # 'Any of various...' — no safe head
    # flat pair coordination: exactly [N, or/and, N]
    if (len(window) == 3
            and window[1].rstrip(",").lower() in ("or", "and")):
        return [0, 2]
    return [window_end - 1]


def _inflect_head(clean: str, tag: str) -> str | None:
    """Head inflection. Verbs use the tagger-assisted coordination walk
    (backstopped by lemminflect's lexicon); nouns use closed-list
    boundary detection, which is far more reliable on fragments.
    Returns None if nothing could be inflected (caller may fall back)."""
    tokens = clean.split()
    if not tokens:
        return None
    if tag == "NNS":
        idxs = _noun_head_indices(tokens)
        if not idxs:
            return None
        if not _apply(tokens, idxs, tag):
            return None
        res = " ".join(tokens)
        return res[:1].upper() + res[1:]
    try:
        tags = _pos_tags(clean)
    except Exception:
        tags = ()
    idxs = _head_indices(tokens, tags, "verb") if tags else [0]
    if not idxs:
        idxs = [0]
    if not _apply(tokens, idxs, tag, tags):
        return None
    res = " ".join(tokens)
    return res[:1].upper() + res[1:]


def inflect_definition(definition: str, kind: str) -> str | None:
    """Turn a root word's definition into a clue for an inflected form.
    e.g. ('To wear away the surface...', 'past') -> 'Wore away the surface...'
    """
    clean = _clean_root_def(definition)
    if not clean:
        return None
    if kind in _TAG:
        return _inflect_head(clean, _TAG[kind])
    if kind == "agent":
        # ABRADER: "One who wears away the surface..."
        # If the source definition is already agent-shaped, use it as-is
        # rather than double-prefixing ('One who one who wears...').
        if re.match(r"(?:one|ones|someone|somebody|person|people)\s+who\b",
                    clean, re.IGNORECASE):
            return clean[:1].upper() + clean[1:]
        third = _inflect_head(clean, "VBZ") or clean
        return f"One who {third[:1].lower() + third[1:]}"
    if kind == "comp":
        return f"More {clean[:1].lower() + clean[1:]}"
    if kind == "super":
        return f"Most {clean[:1].lower() + clean[1:]}"
    if kind == "adverb":
        return f"In a {clean[:1].lower() + clean[1:]} manner"
    return None


def lemmatize(word: str, defs: dict) -> tuple[str, str] | None:
    """Find a defined base form via suffix stripping, then build a clue by
    inflecting the BASE's definition (not naming the base) so the clue
    reads in crossword style and never leaks the answer's root.

    Iterates EVERY source the base has (primary + alternates) so when one
    of the base's definitions inflects into a leaky clue, we try a
    different sense before giving up — GRASP's noun gloss 'Act of
    grasping' leaks GRASPS, but its verb gloss 'Hold firmly' inflects
    cleanly to 'Holds firmly'."""
    for suffix, additions in INFLECTION_RULES:
        if not word.endswith(suffix):
            continue
        stem = word[: -len(suffix)]
        if len(stem) < 2:
            continue
        for add in additions:
            base = stem + add
            if base == word or base not in defs:
                continue
            base_entry = defs[base]
            candidates = [base_entry] + base_entry.get("alternates", [])
            for cand in candidates:
                # don't chain off another inflection-derived clue
                if cand.get("source") == "inflection":
                    continue
                # don't pluralize biography senses: TREES must not become
                # 'English actors...' via the surname Tree, ABELES must not
                # become 'Cains and Abels...' via the given name.
                cand_def = cand.get("definition", "")
                if _BIO_SENSE.search(cand_def):
                    continue
                kind = _resolve_kind(suffix, cand.get("pos", ""))
                if kind is None:
                    continue
                clue = inflect_definition(cand_def, kind)
                if clue and not clue_leaks(word, clue):
                    return base, clue
    return None


def main() -> None:
    defs = json.loads(DEFS_PATH.read_text())
    pool = set(json.loads(POOL_PATH.read_text()))
    defined = set(defs.keys())
    print(f"current definitions: {len(defs):,}")
    print(f"pool size:           {len(pool):,}")
    print(f"missing:             {len(pool - defined):,}")

    added_inflection = 0
    rescued_leaks = 0
    added_roman = 0
    added_abbrev = 0
    skipped_truly_missing = 0

    # Inflectional enrichment.
    # Two cases get an inflection clue:
    #   (a) The word has no definition at all.
    #   (b) Build_definitions left it with a leaking primary (e.g. AAHED's
    #       only WordNet gloss embeds 'aah'). If we can synthesize a
    #       non-leaking clue by inflecting one of the base's senses, promote
    #       that as the new primary and demote the leaker to alternates.
    for word in sorted(pool):
        existing = defs.get(word)
        if existing and not clue_leaks(word, existing.get("definition", "")):
            continue
        result = lemmatize(word, defs)
        if result is None:
            continue
        base, clue = result
        new_primary = {
            "definition": clue,
            "source": "inflection",
            "pos": "",
            "base": base,
        }
        if existing:
            old = {k: v for k, v in existing.items() if k != "alternates"}
            new_primary["alternates"] = [old] + existing.get("alternates", [])
            rescued_leaks += 1
        else:
            new_primary["alternates"] = []
            added_inflection += 1
        defs[word] = new_primary

    # Roman numerals
    for word in sorted(pool - defs.keys()):
        if is_roman(word):
            n = roman_to_int(word)
            if n > 0:
                defs[word] = {
                    "definition": f"Roman numeral for {n}",
                    "source": "roman",
                    "pos": "noun",
                }
                added_roman += 1

    # Curated common abbreviations
    abbrev_meanings = {
        # Tech / electronics
        "GPS": "Navigation system, briefly",
        "HUD": "Head-up display, briefly",
        "USB": "Common port type, briefly",
        "HDMI": "Video cable standard",
        "WIFI": "Wireless network technology",
        "URL": "Web address, briefly",
        "PDF": "Document file format",
        "GIF": "Animated image format",
        "MP3": "Audio file format",
        "MP4": "Video file format",
        "JPG": "Image file format",
        "PNG": "Image file format",
        "HTML": "Web page language, briefly",
        "CSS": "Web page styler",
        "RAM": "Computer memory type",
        "ROM": "Read-only memory",
        "CPU": "Computer's brain, briefly",
        "GPU": "Graphics processor",
        "SSD": "Fast storage, briefly",
        "HDD": "Hard drive, briefly",
        "API": "Software interface, briefly",
        "OS": "Operating system, briefly",
        "IDE": "Coder's tool, briefly",
        "AI": "Modern tech buzzword",
        "VR": "Immersive tech, briefly",
        "AR": "Augmented reality, briefly",
        "IP": "Address type, briefly",
        "DNS": "Internet directory, briefly",
        "SDK": "Developer's toolkit",
        "GHZ": "Processor speed unit",
        "MHZ": "Frequency unit, briefly",
        "DPI": "Print resolution unit",
        "OBD": "Car diagnostics standard",
        "VIN": "Car ID, briefly",

        # Medical / health
        "DNA": "Genetic material",
        "RNA": "Genetic intermediary",
        "MRI": "Medical imaging method",
        "CPR": "Resuscitation technique",
        "EKG": "Heart-monitoring test",
        "ECG": "Heart-monitoring test",
        "IV": "Hospital drip, briefly",
        "UV": "Sunlight component, briefly",
        "IR": "Heat radiation, briefly",
        "ICU": "Hospital unit, briefly",
        "ER": "Hospital section, briefly",
        "AED": "Heart-shock device",
        "EMT": "First responder, briefly",
        "MD": "Medical degree, briefly",
        "RN": "Nursing credential",
        "DO": "Doctor of osteopathy",
        "PT": "Physical therapy, briefly",
        "OT": "Therapy type, briefly",
        "ENT": "Throat doc, briefly",
        "ED": "Emergency dept., briefly",
        "HIV": "Immune-system virus",
        "STD": "Health concern, briefly",
        "CT": "Imaging scan",
        "PET": "Imaging scan",
        "IQ": "Intelligence test result",

        # Cars / transit
        "SUV": "Family vehicle, briefly",
        "ATV": "Off-road vehicle",
        "EV": "Battery-powered car, briefly",
        "LED": "Light type",
        "TSA": "Airport screeners",
        "DOT": "Transit agency",
        "FAA": "Aviation regulator",
        "MPG": "Fuel efficiency unit",
        "MPH": "Speed unit",

        # Government / org
        "IRS": "Tax-collecting agency",
        "FDA": "Food regulator, briefly",
        "EPA": "Environmental regulator",
        "CDC": "Health agency",
        "USDA": "Agriculture department",
        "USPS": "Mail carrier",
        "DOJ": "Justice department",
        "DOE": "Energy department",
        "DOD": "Defense department",
        "HUD": "Housing dept.",
        "NASA": "Space agency",
        "FEMA": "Disaster response agency",
        "OSHA": "Workplace safety agency",
        "NIH": "Health research org",
        "SBA": "Small business agency",
        "UN": "International body, briefly",
        "EU": "Continental union, briefly",
        "UK": "British isles, briefly",
        "USA": "US, briefly",
        "FBI": "Federal investigators",
        "CIA": "Spy agency",
        "NSA": "Eavesdropping agency",
        "DEA": "Drug enforcers",
        "GAO": "Govt. accountability office",
        "GDP": "Economic measure, briefly",
        "CPI": "Inflation measure, briefly",

        # Business / org
        "CEO": "Top corporate role",
        "CFO": "Finance chief",
        "CTO": "Tech chief",
        "COO": "Operations chief",
        "HR": "Personnel dept., briefly",
        "PR": "Image management, briefly",
        "ROI": "Investment metric",
        "IPO": "Stock market debut, briefly",
        "LLC": "Business entity, briefly",
        "INC": "Corp. type, briefly",
        "CORP": "Big company, briefly",
        "MFG": "Manufacturing, briefly",
        "NGO": "International aid org, briefly",
        "NPO": "Charity type, briefly",

        # School / test
        "GPA": "Student's average",
        "SAT": "College entrance exam",
        "ACT": "College entrance exam (or do)",
        "AP": "Advanced course, briefly",
        "IB": "International school credential",
        "PHD": "Doctoral degree, briefly",
        "MBA": "Business degree, briefly",
        "BA": "College degree, briefly",
        "BS": "College degree, briefly",
        "MA": "Master's degree, briefly",
        "MS": "Master's degree, briefly",
        "MFA": "Arts degree, briefly",
        "JD": "Law degree, briefly",
        "GED": "High school equivalent",
        "ESL": "Language class, briefly",
        "ELL": "Language learner, briefly",
        "AAS": "Associate degree, briefly",

        # Time / date
        "AM": "Morning hours",
        "PM": "Afternoon/evening hours",
        "BC": "Pre-Common Era marker",
        "AD": "Common Era marker",
        "BCE": "Era abbreviation",
        "CE": "Era abbreviation",
        "EST": "Eastern time, briefly",
        "EDT": "Eastern daylight time",
        "PST": "West coast time, briefly",
        "CST": "Central time, briefly",
        "UTC": "Universal time, briefly",

        # General
        "ATM": "Cash machine",
        "ETA": "Arrival estimate, briefly",
        "FYI": "For your info, briefly",
        "AKA": "Also known as",
        "RSVP": "Reply request",
        "TBA": "Future announcement, briefly",
        "TBD": "Decision pending, briefly",
        "DIY": "Self-made, briefly",
        "FAQ": "Question section, briefly",
        "KO": "Boxing finish, briefly",
        "MVP": "Sports MVP, briefly",
        "ASAP": "Right away, briefly",
        "BTW": "By the way, briefly",
        "AAA": "Roadside helper",
        "AARP": "Senior advocacy group",
        "OK": "All right",
        "GMO": "Engineered food, briefly",
        "POW": "Captured soldier, briefly",
        "MIA": "Lost soldier, briefly",
        "POV": "Camera angle, briefly",
        "BFF": "Close pal, briefly",
        "VIP": "Honored guest, briefly",
        "DOB": "Form field, briefly",
        "SSN": "Govt. ID number",
        "ZIP": "Postal code",
        "QED": "Proof closer, briefly",
        "AC": "Cooling system, briefly",
        "DC": "Capital, briefly (or current type)",
        "PA": "Public address, briefly",
        "ID": "Card type",
        "BBQ": "Outdoor cookout",
        "ASCII": "Character encoding standard",
    }
    tier2_allow_set = {
        w.strip().upper() for w in TIER2_ALLOW.open() if w.strip().isalpha()
    }
    for word, meaning in abbrev_meanings.items():
        if word in pool and word not in defs:
            defs[word] = {
                "definition": meaning,
                "source": "abbrev_curated",
                "pos": "abbrev",
            }
            added_abbrev += 1

    still_missing = pool - defs.keys()
    skipped_truly_missing = len(still_missing)

    DEFS_PATH.write_text(json.dumps(defs, indent=1))
    print()
    print(f"added inflection clues:    {added_inflection:,}")
    print(f"rescued leaking primaries:  {rescued_leaks:,}")
    print(f"added Roman numerals:      {added_roman:,}")
    print(f"added curated abbrevs:     {added_abbrev:,}")
    print(f"still missing:             {skipped_truly_missing:,} "
          f"({100*skipped_truly_missing/len(pool):.0f}% of pool)")
    print(f"total definitions:         {len(defs):,}")
    # Refresh missing list
    (HERE / "data" / "definitions_missing.txt").write_text(
        "\n".join(sorted(still_missing)[:50_000]) + "\n"
    )
    print()
    print("sample still-missing:")
    for w in sorted(still_missing)[:20]:
        print(f"  {w}")


if __name__ == "__main__":
    main()
