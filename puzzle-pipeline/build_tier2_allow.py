"""
Generates data/tier2_allow.txt — the curated tier-2 fill list of common
abbreviations and Roman numerals. These should be PREFERRED over tier-3
obscure English (DASHEEN, NIGELLA, HUMIC) but rank below tier-1 SCOWL
common English.

Two sources:
  1. Roman numerals 1..2000 (auto-generated). Many short crossword slots
     happily accept III, IV, VII, XIV, etc., and these are universally
     recognized.
  2. A hand-curated list of widely-known abbreviations / acronyms that
     read as fair crossword fill: GPS, HUD, USB, AKA, RSVP, etc.
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "data" / "tier2_allow.txt"


def roman(n: int) -> str:
    pairs = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    out = []
    for v, sym in pairs:
        while n >= v:
            out.append(sym)
            n -= v
    return "".join(out)


COMMON_ABBREVS = """
# Tech / electronics
GPS USB HDMI WIFI URL HTML CSS HTTP HTTPS RAM ROM CPU GPU SSD HDD
PDF JPG JPEG GIF PNG MP3 MP4 SVG AI VR AR IP DNS API SDK IDE OS

# Time / measure
AM PM BC AD BCE CE EST EDT PST CST UTC MPG MPH AC DC KM CM MM
GHZ MHZ KHZ DPI PPI

# Body / medical
DNA RNA MRI EKG ECG CPR IV UV IR IQ ICU ER AED EMT MD RN DO PT OT
ENT ED HIV STD CT PET

# Cars / transit
HUD SUV ATV EV LED OBD VIN TSA DOT FAA

# Govt / nonprofit (widely recognized)
IRS FDA EPA CDC USDA USPS DOJ DOE DOD HUD NASA
FEMA OSHA NIH SBA UN EU UK USA NIH

# Business / org
CEO CFO CTO COO CIO HR PR ROI IPO LLC INC CORP MFG NGO NPO

# School / test
GPA SAT ACT AP IB PHD MBA BA BS MA MS MFA JD GED ESL ELL AAS AAU

# General
ATM ETA FYI AKA RSVP TBA TBD DIY FAQ KO MVP ASAP BTW AAA AARP
GMO NIMBY NSFW MIA POW POV BFF VIP DOB SSN ZIP STD QED OK
"""


def main() -> None:
    entries: set[str] = set()
    for n in range(1, 2001):
        entries.add(roman(n))
    for line in COMMON_ABBREVS.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        for tok in line.split():
            entries.add(tok.upper())
    valid = sorted(e for e in entries if e.isalpha() and 2 <= len(e) <= 6)
    OUT.write_text("\n".join(valid) + "\n")
    print(f"tier 2 allow: {len(valid):,} entries")
    print(f"  Roman numerals: {sum(1 for e in valid if all(c in 'IVXLCDM' for c in e)):,}")
    by_len: dict[int, int] = {}
    for e in valid:
        by_len[len(e)] = by_len.get(len(e), 0) + 1
    print(f"  by length: {sorted(by_len.items())}")
    print(f"written -> {OUT.relative_to(HERE)}")


if __name__ == "__main__":
    main()
