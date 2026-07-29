"""
Hand clues for the ~300 most-recurring fill words (fix 2 of the
student-experience pass). Fill frequency is Zipfian: these words do most
of the appearing, so cluing them by hand upgrades nearly every puzzle.
Every clue is verified non-leaking (stem checker) before landing in
data/fill_clues_ai.json. Junk that shouldn't recur goes to tier3_force.
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

CLUES: dict[str, str] = {
    # --- ultra-common 3s ---
    "USE": "Put to work", "END": "Finish line", "ITS": "Grammatical possessive",
    "ERA": "Notable period of history", "ACT": "Part of a play",
    "EVE": "Night before a holiday", "YOU": "Second-person pronoun",
    "ATE": "Had lunch", "AND": "Plus", "ERE": "Before, in poems",
    "FOR": "In favor of", "ALL": "Every last one", "AMY": "Author Tan",
    "SEE": "Take a look at", "ETA": "Arrival guess, briefly",
    "AGE": "Number of candles on the cake", "ARE": "Exist",
    "CAN": "Soup container", "LEE": "Sheltered side, at sea",
    "ASH": "Fireplace residue", "TEN": "Perfect gymnastics score",
    "ACE": "Unreturnable serve", "EAT": "Have a meal",
    "ASK": "Pose a question", "ASS": "Stubborn pack animal",
    "ALE": "Pub pint", "USA": "Home of the brave, briefly",
    "ORE": "Miner's find", "APE": "Gorilla or chimp",
    "SEC": "Wait a moment!", "AIR": "What we breathe",
    "ICE": "Rink surface", "NEO": "Prefix meaning new",
    "ENE": "Compass point toward sunrise-ish", "RED": "Stop-sign color",
    "GET": "Come to understand", "EYE": "Needle's hole",
    "SHE": "Woman's pronoun", "EEL": "Slippery swimmer",
    "IRA": "Retirement acct.", "YET": "Up to now",
    "ROI": "Investor's concern, briefly", "HIV": "Virus studied by NIAID",
    "ANI": "Tropical blackbird", "RNA": "DNA's messenger cousin",
    "ONE": "Loneliest number, in song", "ORT": "Dinner scrap",
    "HIM": "That guy", "BAA": "Sheep's cry", "ALI": "Boxing legend Muhammad",
    "ADE": "Fruity drink suffix", "SEA": "Sailor's expanse",
    "EMS": "Printer's dashes", "LAN": "Office network, briefly",
    "ERR": "Slip up", "TBS": "Recipe amts.", "ILL": "Under the weather",
    "ROE": "Sushi-bar eggs", "CEO": "Corner-office exec",
    "LIT": "Turned on", "ART": "Museum display", "OUT": "Not at home",
    "BUT": "However", "ESP": "Mind reader's gift, briefly",
    "URN": "Coffee dispenser", "TAP": "Faucet", "IDE": "Coder's workspace, briefly",
    "AHA": "Cry of discovery", "TOO": "As well", "SPA": "Massage venue",
    "MAC": "Apple computer", "IRS": "Taxing org.", "AIM": "Point at a target",
    "EPA": "Clean-air org.", "BRA": "Lingerie item",
    "TEA": "Afternoon cuppa", "CAB": "Taxi", "DNA": "Genetic blueprint",
    "AAA": "Roadside-assistance org.", "TRY": "Give it a shot",
    "ANN": "Landers of advice columns", "FIG": "Newton fruit",
    "PRO": "Expert", "JOB": "Nine-to-five thing", "ADD": "Sum up",
    "MEN": "Chess pieces, collectively", "NOR": "Neither's partner",
    "TWO": "Company, they say", "OBI": "Kimono sash",
    "NTH": "To the ___ degree", "PEE": "Letter after 'o'",
    "ASA": "Botanist Gray", "GPA": "Transcript stat",
    "TAU": "Greek letter after sigma", "HRS": "Sched. slots",
    "DEC": "Last mo.", "LIE": "Fib", "TSA": "Airport screening org.",
    "BIT": "Small piece", "EMU": "Flightless Aussie bird",
    "TED": "___ Talk", "TAB": "Bar bill", "LET": "Allow",
    "ELL": "Building wing shape", "BIG": "Opposite of little",
    "DEA": "Narc's org.", "WAS": "Existed once", "ANE": "Chemical suffix",
    "SLY": "Fox-like", "DYE": "Hair-color product", "OWL": "Hooting bird",
    "INN": "Roadside lodging", "YRS": "Long times, briefly",
    "ADA": "Programming language named for Lovelace", "TAT": "Ink, informally",
    "LEO": "Zodiac lion", "CPR": "Lifesaving technique, briefly",
    "TIA": "Aunt, in Spanish", "BOA": "Feathery scarf",
    "OAT": "Granola grain", "MAN": "Chess piece", "PIE": "Dessert with a crust",
    "LIB": "Ad-___ (improvise)", "GNU": "Bearded antelope",
    "SIR": "Knight's title", "CRT": "Old monitor type, briefly",
    "NET": "Tennis-court divider", "ANT": "Picnic invader",
    "ZED": "British Z", "ISN": "\"___'t that nice?\"",
    "WED": "Tie the knot", "ABM": "Cold War defense abbr.",
    "MAO": "Chairman of old China", "CHI": "Greek X",
    "ION": "Charged particle", "REF": "Whistle blower on the court",
    "CUT": "Editor's snip", "AMP": "Guitarist's gear", "LIP": "Kiss target",
    "ELS": "Chicago trains", "APT": "Fitting", "EDS": "Magazine bosses, briefly",
    "EST": "NYC clock setting, briefly", "ENS": "Printer's spaces",
    "ESS": "Curvy letter", "SSE": "Compass heading, briefly",
    "ETA_": "", "DEL": "Key near Backspace", "EME": "TIER3",
    "ELA": "TIER3", "OCA": "TIER3", "BAI": "TIER3", "ILE": "TIER3",
    "SESS": "TIER3", "LES": "TIER3", "RES": "TIER3", "ATP": "Cell's energy currency, briefly",
    "NSA": "Codebreaking govt. org.", "SSS": "Draft-registration org.",
    "ESR": "TIER3", "EDO": "Tokyo, long ago", "TSAR": "Old Russian ruler",
    "OTC": "Like some meds, briefly", "CSS": "Web stylist's language",
    "ANA": "TIER3", "AGEE": "TIER3", "REE": "TIER3", "LER": "TIER3",
    "ALS": "TIER3", "IDA": "TIER3", "RAS": "TIER3", "NAA": "TIER3",
    "ERD": "TIER3", "DAS": "TIER3", "SEP": "Fall mo.", "DIA": "TIER3",
    "LII": "52, to Caesar", "SECS": "Brief moments, briefly",
    "AAS": "Two-year degs.", "ARA": "TIER3", "FNMA": "TIER3",
    "FCS": "TIER3", "CLI": "Terminal interface, briefly", "ABO": "TIER3",
    "NEP": "TIER3", "SDS": "TIER3", "MDI": "TIER3", "LAS": "Vegas lead-in",
    "GSA": "TIER3", "CPS": "TIER3", "EEC": "Old European bloc, briefly",
    "SAA": "TIER3", "ROS": "TIER3", "ULT": "TIER3", "EURO": "Continental currency",
    "ARSE": "TIER3", "LESE": "TIER3", "ANTA": "TIER3",

    # --- round-2 stragglers: common words the dictionaries clued with an
    # obscure or encyclopedic sense (found by auditing generated puzzles) ---
    "OVER": "Finished", "EVERY": "Each and all", "TAX": "April burden",
    "STYLE": "Manner of expression", "SMITH": "Metalworker",
    "PLATE": "Dinner dish", "DRAW": "Sketch", "SHEET": "Bed linen",
    "GUN": "Firearm", "NOSE": "Face feature", "OHIO": "Buckeye State",
    "STORM": "Thunder-and-lightning event", "PHOTO": "Snapshot",
    "TAIL": "Dog's waggable part", "LASER": "Focused light beam",
    "CUTE": "Adorable", "ELM": "Shade tree", "ACTS": "Does something",
    "AGES": "Long spans of time", "USES": "Puts to work",
    "ERRORS": "Mistakes", "ADAMS": "President John Quincy ___",
    "MIN": "TIER3", "DAS": "TIER3",

    # --- common 4s+ ---
    "AREA": "Length times width", "ALSO": "In addition",
    "LEI": "Luau garland", "STEP": "Stair unit", "EVEN": "Tied, as a score",
    "NEED": "Must have", "ONES": "Singles in a wallet",
    "OFFS": "Play-___ (postseason games)", "SETS": "Tennis match units",
    "EELS": "Slippery swimmers", "ISLAM": "Faith of one in five people",
    "AFLOAT": "Not sinking", "ABOLITION": "Slavery's end",
    "FINALES": "Season-ending episodes", "ARSENATE": "Toxic salt",
    "STET": "Editor's 'keep it'", "STD": "Common, as a feature: Abbr.",
    "ODOR": "Nose's notice", "OLA": "Wave, in Spanish",
    "THAI": "Bangkok native", "EDEN": "Original garden",
    "ASEA": "On the ocean", "MATT": "Damon of film",
    "ARAB": "Gulf resident", "ABBA": "\"Dancing Queen\" band",
    "ARTS": "Humanities, informally", "ENDS": "Wraps up",
    "ARC": "Rainbow shape", "ANON": "Shortly, to Shakespeare",
    "ELSE": "If not", "ADDS": "Tacks on", "EDGE": "Slight advantage",
    "INTO": "Fascinated by", "ITER": "TIER3", "SAME": "Identical",
    "HERO": "Cape wearer", "ASPS": "Nile vipers", "ACRE": "Farm unit",
    "ECG": "Heart test, briefly", "APNEA": "Sleep disorder",
    "SNIP": "Quick cut", "DATA": "Spreadsheet contents",
    "TETE": "Head, in Paris", "EACH": "Apiece", "ALAR": "Wing-shaped",
    "EYES": "Portrait focal points", "ITEMS": "List entries",
    "ALPS": "Swiss peaks", "IDEA": "Light-bulb moment",
    "SALE": "Bargain hunter's event", "STIR": "Mix with a spoon",
    "EDIT": "Polish a draft", "REST": "Musical pause",
    "STYE": "Eyelid bump", "EGOS": "Inflated senses of self",
    "ROOT": "Cheer (for)", "BIAS": "Slant", "BRAN": "Fiber-rich cereal bit",
    "AFAR": "From a distance", "TEST": "Pop quiz, e.g.",
    "YEAR": "Calendar span", "SEMI": "Big rig", "EASY": "Like pie, in a saying",
    "AHEM": "Polite throat-clearing", "DAYS": "Calendar squares",
    "RHEA": "Ostrich cousin", "OPERA": "La Scala performance",
    "HER": "That woman's", "PAL": "Buddy", "LACE": "Shoe string",
    "OPERAS": "Met productions", "ADAM": "First man",
    "SAT": "Took a chair", "KEY": "Piano part", "TOP": "Spinning toy",
    "ANNE": "Green Gables girl", "ASSE": "TIER3", "ERAS": "History chapters",
    "UPON": "Once ___ a time", "ENID": "Oklahoma city",
    "TETRA": "Aquarium fish", "EDDA": "Norse saga",
    "IDOL": "Pop star, to fans", "SARS": "2003 outbreak, briefly",
    "STUD": "Poker variety", "ELAN": "Stylish flair",
    "ENNUI": "World-weary boredom", "EERY": "Spooky, var.",
    "ARNO": "Florence's river", "IMAM": "Mosque leader",
    "GASP": "Shocked intake of breath", "SLAB": "Thick slice",
    "NYSE": "Wall Street letters", "EDEMA": "Fluid swelling",
    "OPEN": "Ready for business", "AGORA": "Ancient Greek marketplace",
    "ERNST": "Surrealist Max", "ESTATE": "Manor grounds",
    "STY": "Pig's pen", "PEELE": "Jordan of horror films",
}


def main() -> None:
    import morphology as M
    fill = json.load(open(DATA / "fill_clues_ai.json"))
    tier3_new = []
    added = replaced = 0
    for w, c in CLUES.items():
        if not w or w.endswith("_") or not c:
            continue
        if c == "TIER3":
            tier3_new.append(w)
            continue
        assert not M.clue_leaks(w, c), f"LEAK: {w} -> {c}"
        if w in fill:
            if fill[w] != c:
                replaced += 1
            fill[w] = c
        else:
            fill[w] = c
            added += 1
    (DATA / "fill_clues_ai.json").write_text(
        json.dumps(fill, indent=2, sort_keys=True))
    print(f"hand clues: +{added} new, {replaced} replaced (now {len(fill)})")

    tier3_text = (DATA / "tier3_force.txt").read_text()
    have = {l.strip() for l in tier3_text.splitlines()
            if l.strip() and not l.startswith("#")}
    new = sorted(set(tier3_new) - have)
    if new:
        with open(DATA / "tier3_force.txt", "a") as f:
            f.write("\n# recurring junk from the common-fill pass\n"
                    + "\n".join(new) + "\n")
    print(f"tier3_force: +{len(new)}")


if __name__ == "__main__":
    main()
