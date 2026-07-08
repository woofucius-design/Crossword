"""
Round-5 gap triage: the 147 unclued slots in the NYT-grid marquee sets.

Two independent levers, applied together where both make sense:
  CLUES  -> data/fill_clues_ai.json  (fills the gap in shipped puzzles
            via reclue.py; proper nouns already in grids get clues too —
            a clue beats a blank)
  PRUNE  -> data/tier3_force.txt     (removes the word from FUTURE pools)
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

CLUES: dict[str, str] = {
    # --- len 3 ---
    "THE": "Most common English word", "EEK": "Mouse-spotter's shriek",
    "MAH": "___-jongg", "NOS": "Refusals", "BIC": "Ballpoint brand",
    # --- len 4 ---
    "AMID": "Surrounded by", "BENE": "Well, in Latin",
    "FRAE": "From, to a Scot", "NOES": "Dissenting votes",
    "REED": "Marsh plant", "TROD": "Walked heavily",
    "TWOS": "Terrible ___ (toddler phase)", "ALVA": "Edison's middle name",
    "RUDY": "Giuliani or Gobert", "MYRA": "Old-fashioned woman's name",
    # --- len 5 ---
    "ANNUS": "Year, in Latin", "APSES": "Church recesses",
    "CARNE": "Chili con ___", "ENURE": "Toughen by exposure, var.",
    "KARTS": "Go-___ (racetrack rides)", "LAPIS": "___ lazuli",
    "NEAPS": "Low tides", "PUPAE": "Insect stages, plural",
    "SATAY": "Skewered Thai dish", "SWEPT": "Cleaned the floor",
    "TAPAS": "Spanish small plates", "THATS": "\"___ all, folks!\"",
    "TRIER": "One making an attempt", "UNMET": "Like some goals",
    "YESES": "Affirmative votes", "HEIDI": "Alpine orphan of fiction",
    "TANYA": "Country singer Tucker", "NORAD": "Santa-tracking defense org.",
    "JAIME": "Spanish form of James", "KNUTH": "Computer scientist Donald",
    # --- len 6 ---
    "BIASES": "Prejudices", "CAMINO": "El ___ Real",
    "DEMONS": "Underworld fiends", "DOMINI": "Anno ___",
    "GEIGER": "___ counter (radiation detector)",
    "INSULA": "Brain region deep in the cortex",
    "INTUIT": "Grasp instinctively", "LAYMEN": "Non-clergy",
    "NABBED": "Caught red-handed", "NAPPER": "Afternoon dozer",
    "OPTIMA": "Best possible conditions, plural",
    "PINNED": "Held down on the mat", "PREPPY": "Polo-and-khakis sort",
    "PRINTS": "Photo lab output", "REEDIT": "Revise the manuscript again",
    "ROLLED": "Went head over heels", "STRODE": "Walked confidently",
    "STROVE": "Made every effort", "STRUNG": "Threaded, as beads",
    "SUBPAR": "Below standard", "SWIPES": "Card reader actions",
    "TEMPEH": "Fermented soy protein", "YAHOOS": "Boorish sorts",
    "YEASTS": "Bread-rising organisms", "ARAMIS": "Musketeer with a cologne namesake",
    "THELMA": "Louise's road-trip partner", "TULANE": "New Orleans university",
    "LIPTON": "Big name in tea bags", "ELYSEE": "French presidential palace",
    # --- len 7 ---
    "ALABAMA": "Heart of Dixie state", "CLOACAE": "Bird waste ducts, plural",
    "DAIRIES": "Milk farms", "HIPNESS": "Trendy quality",
    "LOOFAHS": "Shower scrubbers", "MUNSTER": "Mild washed-rind cheese",
    "OUTSOLD": "Beat in the market", "PLEASES": "Suits just fine",
    "RETAKEN": "Captured again", "TOOTERS": "Party horns",
    "UNLADEN": "Carrying nothing",
    # --- len 8+ ---
    "LIBRETTI": "Opera texts, plural",
    "IMMORTALS": "Gods of Olympus", "RHINOCERI": "Horned beasts, plural, var.",
    "TIMESHARE": "Vacation property arrangement",
    "CONFISCATOR": "Property seizer",
    "INFRASTRUCTURAL": "Of roads, grids, and pipelines",
}

# Future-pool prune: junk fragments, abbreviations, and proper nouns.
PRUNE: set[str] = {
    # junk / non-words / foreign fragments
    "REE", "GON", "RFC", "BIM", "CPM", "HOO", "ICH", "KOL", "LBW", "OBV",
    "PAU", "RHA", "RND", "SOV", "TWI", "AGEN", "AUBE", "ENCL", "HEER",
    "MAGA", "MEAS", "MELL", "NANE", "NUNC", "TARR", "SATIS", "TECUM",
    "ATMOS", "BAILE", "INDIV", "ISING", "NOLLE", "SOPHY", "SPIRA",
    "CENTUM", "GESTAE", "RETOUR", "CETERIS", "NAHUA", "LABIA",
    # proper nouns (people, places, brands)
    "ALVA", "MYRA", "OLEG", "REVA", "RUDY", "ALVAR", "HEIDI", "HUANG",
    "JAIME", "KNUTH", "LUISA", "MYLES", "NYASA", "RIVAS", "SALAS",
    "SMYTH", "TANYA", "NORAD", "ARAMIS", "BIANCO", "ELYSEE", "GUERRA",
    "LIPTON", "OLIVET", "PEARCE", "PRUITT", "SAVILE", "TATLER", "THELMA",
    "TULANE", "ALABAMA", "LEONORA", "BIC", "MAH", "CAMINO", "GEIGER",
}


def main() -> None:
    import morphology as M
    fill = json.load(open(DATA / "fill_clues_ai.json"))
    added = 0
    for w, c in CLUES.items():
        assert not M.clue_leaks(w, c), f"LEAK: {w} -> {c}"
        if w not in fill:
            fill[w] = c
            added += 1
    (DATA / "fill_clues_ai.json").write_text(
        json.dumps(fill, indent=2, sort_keys=True))
    print(f"fill_clues_ai: +{added} (now {len(fill)})")

    tier3_text = (DATA / "tier3_force.txt").read_text()
    have = {l.strip() for l in tier3_text.splitlines()
            if l.strip() and not l.startswith("#")}
    new = sorted(PRUNE - have)
    if new:
        with open(DATA / "tier3_force.txt", "a") as f:
            f.write("\n# NYT-grid marquee gap triage (round 5)\n"
                    + "\n".join(new) + "\n")
    print(f"tier3_force: +{len(new)}")


if __name__ == "__main__":
    main()
