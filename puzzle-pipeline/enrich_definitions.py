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

import json
from pathlib import Path

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
    # (suffix to strip, possible additions to base, clue template)
    ("IES", ["Y"],            "Plural of {base}"),
    ("ES",  ["", "E"],        "Plural of {base}"),
    ("S",   [""],             "Plural of {base}"),
    ("IED", ["Y"],            "Past tense of {base}"),
    ("ED",  ["", "E"],        "Past tense of {base}"),
    ("ING", ["", "E"],        "Present participle of {base}"),
    ("EST", ["", "E"],        "Superlative of {base}"),
    ("ER",  ["", "E"],        "One who {base}s"),
    ("LY",  [""],             "In a {base} manner"),
]


def lemmatize(word: str, defined: set[str]) -> tuple[str, str] | None:
    """Find a defined base form via suffix stripping; return (base, clue)."""
    for suffix, additions, template in INFLECTION_RULES:
        if not word.endswith(suffix):
            continue
        stem = word[: -len(suffix)]
        if len(stem) < 2:
            continue
        for add in additions:
            base = stem + add
            if base != word and base in defined:
                return base, template.format(base=base.lower())
    return None


def main() -> None:
    defs = json.loads(DEFS_PATH.read_text())
    pool = set(json.loads(POOL_PATH.read_text()))
    defined = set(defs.keys())
    print(f"current definitions: {len(defs):,}")
    print(f"pool size:           {len(pool):,}")
    print(f"missing:             {len(pool - defined):,}")

    added_inflection = 0
    added_roman = 0
    added_abbrev = 0
    skipped_truly_missing = 0

    # Inflectional enrichment
    for word in sorted(pool - defined):
        if word in defs:
            continue
        # Try lemmatize against the original SAT+Webster set so we don't
        # chain inflection -> inflection.
        result = lemmatize(word, defined)
        if result is not None:
            base, clue = result
            defs[word] = {
                "definition": clue,
                "source": "inflection",
                "pos": "",
                "base": base,
            }
            added_inflection += 1

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
