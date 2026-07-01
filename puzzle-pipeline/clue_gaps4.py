"""
Round-4 gap triage for the 15x15 sweep, per the chosen strategy:
  - auto-clue inflections where the engine can (folded in here as explicit
    clues for the ones it rescued: ASTERISKS, FORTIETHS)
  - prune proper nouns + junk abbreviations to tier3_force
  - hand-clue the genuine real words (mostly irregular/Latin plurals and
    comparatives whose base isn't in definitions.json)
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

DECISIONS: dict[str, str] = {
    # ---- proper nouns (people/places/brands) -> prune ----
    "ABSALOM": "TIER3", "ADLER": "TIER3", "ADOLF": "TIER3", "ALFONSO": "TIER3",
    "ALTON": "TIER3", "ALVARO": "TIER3", "AMIN": "TIER3", "ARACHNE": "TIER3",
    "ASHMAN": "TIER3", "AVERY": "TIER3", "BABI": "TIER3", "BASSI": "TIER3",
    "BATU": "TIER3", "BEEK": "TIER3", "BELLI": "TIER3", "BETSEY": "TIER3",
    "BLAS": "TIER3", "BOMA": "TIER3", "BONO": "TIER3", "BUSCH": "TIER3",
    "CAIN": "TIER3", "CAMPO": "TIER3", "CESSNA": "TIER3", "CHER": "TIER3",
    "CHO": "TIER3", "COMO": "TIER3", "CONOR": "TIER3", "CORY": "TIER3",
    "CURA": "TIER3", "CUSH": "TIER3", "DALEY": "TIER3", "DANI": "TIER3",
    "DANNY": "TIER3", "DEENA": "TIER3", "DEIRDRE": "TIER3", "DELMAR": "TIER3",
    "DENE": "TIER3", "DOREEN": "TIER3", "DUBCEK": "TIER3", "DURO": "TIER3",
    "EFFIE": "TIER3", "ELISSA": "TIER3", "ELLIE": "TIER3", "ELLIOT": "TIER3",
    "EPCOT": "TIER3", "FARRIS": "TIER3", "FRANCA": "TIER3", "FRANZ": "TIER3",
    "GENGHIS": "TIER3", "GORDON": "TIER3", "GREER": "TIER3", "GUILLERMO": "TIER3",
    "HELGA": "TIER3", "HONDA": "TIER3", "IGLESIA": "TIER3", "IMELDA": "TIER3",
    "INDIRA": "TIER3", "INGA": "TIER3", "INTEL": "TIER3", "IRELAND": "TIER3",
    "IRVIN": "TIER3", "ISADORA": "TIER3", "ISCARIOT": "TIER3", "IZAAK": "TIER3",
    "JOHANN": "TIER3", "KAREEM": "TIER3", "KARINA": "TIER3", "LAURENCE": "TIER3",
    "LAURENT": "TIER3", "LILA": "TIER3", "LUI": "TIER3", "LUIS": "TIER3",
    "MADEIRA": "TIER3", "MADRES": "TIER3", "MARG": "TIER3", "MATSU": "TIER3",
    "MAURA": "TIER3", "MAUREEN": "TIER3", "MICRA": "TIER3", "MILNER": "TIER3",
    "MOMO": "TIER3", "MOSE": "TIER3", "NATALIE": "TIER3", "NELL": "TIER3",
    "NONA": "TIER3", "NORA": "TIER3", "NORAH": "TIER3", "PABST": "TIER3",
    "PAMELA": "TIER3", "PAOLA": "TIER3", "PASCO": "TIER3", "PENOBSCOT": "TIER3",
    "PETO": "TIER3", "PHINEAS": "TIER3", "PICT": "TIER3", "PIOTR": "TIER3",
    "POOLE": "TIER3", "QANTAS": "TIER3", "RABI": "TIER3", "RAFE": "TIER3",
    "RHEE": "TIER3", "RICHARD": "TIER3", "RIPA": "TIER3", "RIVA": "TIER3",
    "ROCCO": "TIER3", "ROXANE": "TIER3", "SAAD": "TIER3", "SAMAR": "TIER3",
    "SAUDI": "TIER3", "SEATO": "TIER3", "SEUSS": "TIER3", "SEVE": "TIER3",
    "SHA": "TIER3", "SHERI": "TIER3", "SIENA": "TIER3", "SISLEY": "TIER3",
    "STIRLING": "TIER3", "SUSIE": "TIER3", "TAINO": "TIER3", "TATAR": "TIER3",
    "TERKEL": "TIER3", "TOMSK": "TIER3", "UPTON": "TIER3", "URIS": "TIER3",
    "WASATCH": "TIER3", "WEISS": "TIER3", "WERNER": "TIER3",

    # ---- junk / abbreviations / fragments -> prune ----
    "ARYL": "TIER3", "AUTH": "TIER3", "AVOIR": "TIER3", "BIOS": "TIER3",
    "BOE": "TIER3", "CAMB": "TIER3", "CAV": "TIER3", "CHON": "TIER3",
    "CRC": "TIER3", "DBL": "TIER3", "DIEL": "TIER3", "ECUS": "TIER3",
    "EMP": "TIER3", "EMPT": "TIER3", "ENGL": "TIER3", "ESTAB": "TIER3",
    "EXCH": "TIER3", "FAITS": "TIER3", "FRAUEN": "TIER3", "GOV": "TIER3",
    "GTC": "TIER3", "GUNGE": "TIER3", "HADST": "TIER3", "HEIL": "TIER3",
    "HOMINEM": "TIER3", "HORA": "TIER3", "HUND": "TIER3", "HUP": "TIER3",
    "INTROD": "TIER3", "KAL": "TIER3", "KETO": "TIER3", "KOA": "TIER3",
    "KOU": "TIER3", "LPG": "TIER3", "MICS": "TIER3", "MOR": "TIER3",
    "NASI": "TIER3", "NFC": "TIER3", "NOA": "TIER3", "OKLA": "TIER3",
    "PENTA": "TIER3", "PERCHA": "TIER3", "PETRO": "TIER3", "PIL": "TIER3",
    "PIM": "TIER3", "POLIT": "TIER3", "POURQUOI": "TIER3", "QUAM": "TIER3",
    "REORGS": "TIER3", "RPT": "TIER3", "SACRA": "TIER3", "SATA": "TIER3",
    "SICKLING": "TIER3", "SIM": "TIER3", "SINH": "TIER3", "THON": "TIER3",
    "TIERRAS": "TIER3", "TUNG": "TIER3", "UNUM": "TIER3", "VERSA": "TIER3",
    "VOCAB": "TIER3", "XRAY": "TIER3", "YAH": "TIER3",

    # ---- genuine real words -> clue (non-leaking) ----
    "ACHIER": "More sore", "ALUMNAE": "Female school grads",
    "AMEBAE": "Single-celled organisms, Latin plural", "ARBORETA": "Tree gardens, Latin plural",
    "ARISEN": "Gotten up", "ARTHROSCOPIC": "Like some minimally invasive knee surgery",
    "ASTERISKS": "Star-shaped characters used in printing",
    "AUTHENTICATIONS": "Identity verifications", "AWARDEES": "Prize winners",
    "BALDS": "Goes hairless, with 'out'", "BEFELL": "Happened to",
    "BEWARING": "Watching out for", "BLEW": "Failed spectacularly, slangily",
    "BOOGIEMAN": "Bedtime scare figure", "BUDGETED": "Allotted funds for",
    "BUSIEST": "Most hectic", "CADUCEI": "Physician's staffs, Latin plural",
    "CAISSE": "Fund, in French", "CARBONS": "Copies, in old office lingo",
    "CASSIS": "Blackcurrant liqueur", "CASTANET": "Flamenco clacker",
    "CHECKOFF": "Item marked as done", "CIABATTA": "Italian bread",
    "CLOAKED": "Concealed", "CONGRATS": "\"Well done!\", briefly",
    "CONSTRUABLE": "Open to interpretation", "CONTEXTUALIZING": "Setting the scene for",
    "COPPICED": "Cut back, as trees", "COTS": "Fold-up beds",
    "CREEPIER": "More unsettling", "CREMES": "Custard dessert layers",
    "CRUELLER": "More heartless", "CUTIE": "Adorable one",
    "DATASET": "Analyst's collection of records", "DID": "Accomplished",
    "DIGERATI": "Tech elite", "DRATTED": "Confounded",
    "DREAMBOAT": "Ideal romantic partner", "DRIVELERS": "Talkers of nonsense",
    "ELKS": "Antlered lodge members", "EMPTIEST": "Most vacant",
    "ENCYSTS": "Encloses in a sac", "ENFOLDS": "Wraps up",
    "EQUALS": "Comes to, in math", "ESCALOPED": "Thinly sliced, as veal",
    "ETHERIC": "Of the upper atmosphere", "ETHNICS": "Cultural-group members",
    "EXTREMAL": "At a maximum or minimum, in math", "FAIRE": "Renaissance ___",
    "FANNED": "Cooled with a waft", "FILER": "One submitting taxes",
    "FORTIETHS": "Positions in a countable series",
    "FOSSAE": "Anatomical hollows, Latin plural", "FREESIA": "Fragrant garden flower",
    "FRUSTA": "Cone sections, Latin plural", "GETTER": "Go-___ (ambitious sort)",
    "GODDAMED": "Confounded, mildly", "GRAMPA": "Old-timer, affectionately",
    "GRANDE": "Starbucks size", "GROUPED": "Clustered together",
    "HAIRIEST": "Most nerve-racking", "HAPLESSNESS": "Chronic bad luck",
    "HAZIEST": "Foggiest", "HONORARIA": "Speaker's fees, Latin plural",
    "HOODED": "Wearing a cowl", "HOSTELER": "Budget traveler's lodger",
    "HUMERI": "Upper arm bones, Latin plural", "IAMBI": "Metrical feet, plural",
    "IDIOSYNCRACIES": "Personal quirks, var.", "INTELLECTIVE": "Of the reasoning mind",
    "ISLANDER": "Archipelago dweller", "KINDERGARTENER": "Five-year-old pupil",
    "LAMBADA": "Sensual Brazilian dance", "LARYNGES": "Voice boxes, Latin plural",
    "LEFTEST": "Most to the port side", "LOCOS": "Crazy ones, in Spanish slang",
    "MADRASSA": "Islamic school", "MILDEST": "Least harsh",
    "MILER": "Track runner in a middle-distance race", "MONIES": "Sums of cash",
    "MOTLIER": "More varied", "NOISIER": "Louder", "NOSECONES": "Rocket tips",
    "NONCOOPERATIVE": "Refusing to go along", "OILIER": "More greasy",
    "OWED": "Was in debt for", "PACED": "Measured by steps",
    "PASSBAND": "Filter's frequency range", "PEAHENS": "Female peafowl",
    "PHAT": "Cool, in '90s slang", "PIETIES": "Displays of devotion",
    "PIKER": "Cheapskate", "POINTE": "Ballet toe position",
    "POLYUNSATURATE": "Healthy dietary fat", "PRECOLONIAL": "Before European settlement",
    "PRIVIES": "Outhouses", "PSYCH": "\"Just kidding!\"",
    "RAGAS": "Indian melodic frameworks", "RARES": "___ back (rears up)",
    "REBID": "Bridge auction move", "RESPRAYS": "Repaints, as a car",
    "RETURNEES": "Those coming back", "REVANCHE": "Retaliation, in French",
    "RISKED": "Gambled", "RODS": "Fishing gear", "ROOTKIT": "Stealthy malware",
    "ROPIER": "Shabbier, in British slang", "ROSTRA": "Speaking platforms, Latin plural",
    "SANDLOTTERS": "Pickup-game players", "SAUNAED": "Took a steam bath",
    "SCHEMATA": "Diagrams, Latin plural", "SHEETING": "Bolt of bed fabric",
    "SHES": "Female pronouns", "SHONE": "Gleamed", "SNORTED": "Laughed derisively",
    "SOAPING": "Lathering up", "SOLIDI": "Old Roman coins, Latin plural",
    "SPINOFF": "Series derived from another", "SPORTIER": "Jauntier",
    "STORMIEST": "Most tempestuous", "SUBSAMPLE": "Portion of a larger set",
    "TESSERAE": "Mosaic tiles, Latin plural", "THEATRICS": "Melodramatic behavior",
    "THREADIEST": "Most sinewy, as a pulse", "TIMBERING": "Wooden framework",
    "TOASTY": "Pleasantly warm", "TOUCHE": "\"Good point!\"",
    "TRAUMATA": "Injuries, Latin plural", "TSARISTS": "Old Russian monarchists",
    "UKELELE": "Small Hawaiian guitar, var.", "UNSTOPPED": "Unblocked, as a drain",
    "VECTORIAL": "Having magnitude and direction", "VEEP": "Second-in-command, informally",
    "VERIEST": "Most utter", "VETTED": "Checked out thoroughly",
    "VILLI": "Intestinal projections, plural", "WASABI": "Sushi's green heat",
    "WATERBED": "Liquid-filled mattress", "WOES": "Troubles",
    "YEAHS": "Casual affirmatives",
}


def main() -> None:
    fill = json.load(open(DATA / "fill_clues_ai.json"))
    tier3_text = (DATA / "tier3_force.txt").read_text()
    tier3_set: set[str] = set()
    for line in tier3_text.splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            tier3_set.add(s)

    added_clues = 0
    new_tier3: list[str] = []
    for word, decision in DECISIONS.items():
        if decision == "TIER3":
            if word not in tier3_set:
                new_tier3.append(word)
                tier3_set.add(word)
        elif word not in fill:
            fill[word] = decision
            added_clues += 1

    (DATA / "fill_clues_ai.json").write_text(json.dumps(fill, indent=2, sort_keys=True))
    print(f"fill_clues_ai.json: added {added_clues} (now {len(fill)})")
    if new_tier3:
        block = ("\n# 15x15 sweep round-4: proper-noun + junk prune\n"
                 + "\n".join(sorted(new_tier3)) + "\n")
        with open(DATA / "tier3_force.txt", "a") as f:
            f.write(block)
    print(f"tier3_force.txt: added {len(new_tier3)}")


if __name__ == "__main__":
    main()
