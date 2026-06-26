"""Round 3: triage remaining 386 gaps from the post-r2 sweep."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

DECISIONS: dict[str, str] = {
    # ---------- length 3 ----------
    "ABR": "TIER3", "ALY": "TIER3", "BCH": "TIER3", "BEF": "TIER3",
    "BLU": "TIER3", "CEP": "TIER3", "CHM": "TIER3",
    "COM": "Web domain ending", "DAO": "Way, in Chinese philosophy",
    "DAU": "TIER3", "DEP": "TIER3", "FEC": "TIER3", "FWY": "Big road, briefly",
    "GAZ": "TIER3", "HOI": "___ polloi", "IFF": "Iff (logic notation)",
    "INF": "Stat above OBP", "JCS": "TIER3", "JER": "TIER3",
    "KIL": "TIER3", "MFR": "TIER3", "MIG": "Soviet-era fighter jet",
    "MOU": "TIER3", "NAV": "TIER3", "NEV": "TIER3", "NOH": "Japanese theater",
    "NWT": "Canada's far-north abbr.", "OXY": "Acne cleanser brand",
    "PPM": "Pollution unit, briefly", "ROG": "TIER3", "SML": "TIER3",
    "SOG": "TIER3", "TAL": "TIER3", "TOA": "TIER3", "TWA": "Defunct U.S. carrier",
    "WAT": "Cambodian temple, e.g., Angkor ___", "YOR": "TIER3",
    "YUK": "Hearty laugh",

    # ---------- length 4 ----------
    "ADDR": "Mailing info, briefly", "ADDY": "Modern email, briefly",
    "AIDA": "Verdi opera", "AINU": "Indigenous Japanese people",
    "ALLS": "TIER3", "ARIZ": "Grand Canyon state, briefly",
    "AUDI": "Luxury car brand", "BARR": "Late Sen. Bob",
    "BELG": "TIER3", "BIBL": "TIER3", "BINT": "British slang for girl",
    "BLED": "Lost blood", "BOCA": "___ Raton, FL", "BOYD": "Actor Stephen",
    "BUTE": "TIER3", "CHID": "Scolded, archaically", "CRIT": "TIER3",
    "DEUS": "___ ex machina", "DEUX": "Pas de ___",
    "DIEM": "Per ___ (daily)", "DOMS": "TIER3", "ELMO": "Sesame Street tickler",
    "ERNA": "TIER3", "FAIT": "Done deal, in French",
    "FAVE": "Top pick, casually", "FLEW": "Took to the air",
    "GAWD": "Eye-rolling exclamation", "GERS": "TIER3", "GIGI": "Lerner-Loewe musical",
    "HOSP": "Medical center, briefly", "HOSS": "Bonanza's big brother",
    "JOIE": "___ de vivre", "KART": "Go-___ track",
    "KIRI": "Soprano Te Kanawa", "KUAN": "TIER3", "LISE": "TIER3",
    "LODI": "California town", "LOLA": "Kinks song", "LOTT": "Late Sen. Trent",
    "LYLE": "Lovett of country", "MIRV": "Multi-warhead missile, briefly",
    "MOTA": "TIER3", "MUMS": "Stays silent", "NASO": "TIER3",
    "NEBR": "Cornhusker State, briefly", "NITA": "TIER3",
    "NOAM": "Linguist Chomsky", "OLIN": "Actress Lena",
    "PARC": "Park, in Paris", "PENA": "Actor Michael",
    "PHYS": "Lab class, briefly", "PREV": "TIER3", "PUTT": "Golf short shot",
    "QUAL": "TIER3", "RARA": "___ avis", "SCOP": "TIER3",
    "SHEE": "TIER3", "SHEN": "TIER3", "SKYE": "Scottish isle",
    "STIM": "TIER3", "SURG": "TIER3", "TAXA": "Biology classifications",
    "TERI": "Actress Hatcher", "TINA": "Singer Turner", "TOBE": "TIER3",
    "TOPO": "Map type, briefly", "VERI": "TIER3", "VINT": "TIER3",
    "VOGT": "TIER3", "VOLS": "Library set, briefly", "WAKA": "TIER3",
    "WEPT": "Cried", "WIKI": "Online collaborative site",
    "WOKE": "Roused; modern hot-button term", "YANA": "TIER3",
    "YEPS": "Casual affirmations", "ZACH": "Actor Galifianakis",

    # ---------- length 5 ----------
    "ABEND": "Computer crash, in old slang", "ACING": "Doing perfectly",
    "ALLIE": "TIER3", "AURUM": "Latin for gold",
    "AUTRE": "Other, in French", "AWACS": "Radar plane, briefly",
    "BEATA": "TIER3", "BEEBE": "TIER3", "BEHAN": "Irish playwright Brendan",
    "BETSY": "Old Ford Mustang", "CALLI": "TIER3", "CARLA": "Cheers waitress",
    "CARLE": "TIER3", "CHEKA": "TIER3", "CHERI": "Author Colette novel",
    "CLINT": "Eastwood of film", "CONAN": "Late-night host O'Brien",
    "CONTR": "TIER3", "CUTEY": "Cutie, alt spelling",
    "CYCLO": "Three-wheeled taxi in Vietnam", "DANGS": "TIER3",
    "DARIN": "Singer Bobby", "DAVAO": "Philippine city",
    "DIPLOMATA": "TIER3", "ELDON": "TIER3", "EMDEN": "TIER3",
    "ENTRE": "Between, in Madrid", "ERVIN": "Watergate Sen. Sam",
    "ETHAN": "Coen brother", "ETIAM": "Yes, in Latin",
    "FALUN": "TIER3", "FEDEX": "Overnight delivery giant",
    "FRITS": "TIER3", "GARDE": "Avant-___", "GARNI": "Decorated with greens",
    "GOREN": "Bridge expert Charles", "GRATA": "Persona non ___",
    "HENNY": "Late comic Youngman", "IDLES": "Sits in neutral",
    "ILLUS": "TIER3", "IRIAN": "TIER3", "KENAI": "Alaskan peninsula",
    "KENNY": "Rogers of country", "LAUDE": "Magna cum ___",
    "LEONA": "Hotel heiress Helmsley", "LIBRI": "TIER3",
    "LINEA": "TIER3", "LINEN": "Bedsheet fabric",
    "LOUIE": "Police's voice", "LYSED": "Broke open, cellularly",
    "MAUDE": "Bea Arthur sitcom", "MEYER": "Director Russ",
    "NAACP": "Civil rights org., briefly", "NADIA": "Gymnast Comaneci",
    "OLSON": "TIER3", "OMNES": "TIER3", "OPHIR": "TIER3",
    "OPRAH": "Talk show legend", "PABLO": "Painter Picasso",
    "PANZA": "Sancho ___ (Quixote's squire)", "PELEE": "TIER3",
    "PEPSI": "Coke rival", "PIMAS": "Arizona's native people",
    "POLIS": "Greek city-state", "PONTO": "TIER3",
    "RHEME": "TIER3", "RHODA": "Mary Tyler Moore spinoff",
    "RICHE": "Nouveau ___", "ROUTH": "TIER3", "RUBEN": "Pres. candidate Diaz-Balart",
    "SAKAI": "TIER3", "SALLE": "TIER3", "SENSA": "TIER3",
    "SHIER": "More bashful", "SLUNK": "Crept off",
    "SMOTE": "Struck down", "STACY": "TIER3",
    "STATS": "Numbers in box scores", "STENO": "Court reporter, briefly",
    "TERRI": "TIER3", "TIGRE": "Tiger, in Madrid",
    "TWERE": "It were, archaically", "UMPED": "Called balls and strikes",
    "VEEPS": "POTUS seconds, briefly", "WALED": "TIER3",
    "WANDA": "Comedian Sykes", "WRIER": "More sarcastic",
    "YEGGS": "Old slang for safecrackers",

    # ---------- length 6 ----------
    "ACOSTA": "Reporter Jim", "ALSTON": "TIER3", "ALTMAN": "Director Robert",
    "ALYSSA": "Actress Milano", "BADMAN": "Outlaw of the West",
    "BARRES": "Bar exercises, plural", "CANERS": "TIER3",
    "CEDARS": "Lebanese trees", "COMSAT": "Communications satellite, briefly",
    "DAIMYO": "Feudal Japanese lord", "DREAMT": "Imagined while sleeping",
    "DUSTED": "Wiped clean", "EISNER": "Old Disney CEO Michael",
    "EMBOLI": "Blood clots, plural", "FANNIE": "Mae of Wall Street",
    "FAVELA": "Brazilian slum", "FULCRA": "Lever pivots, plural",
    "GARCIA": "Late Grateful Dead frontman", "GERARD": "Old-fashioned name",
    "GLENDA": "Good Witch of Oz", "GLUING": "Sticking together",
    "HETERO": "Straight, briefly", "HOLMAN": "TIER3",
    "HUSKED": "Removed from corn", "IEYASU": "Tokugawa shogun",
    "IRONED": "Pressed clothes", "ISMAIL": "TIER3",
    "ISTHMI": "TIER3", "JOSHUA": "Biblical leader",
    "KULTUR": "TIER3", "LIMBED": "TIER3",
    "LORAIN": "Ohio city", "LOUISA": "May Alcott of Little Women",
    "MALADE": "Sick, in French", "MAORIS": "New Zealand natives",
    "MEDIAS": "Plural of medium, var.", "OBISPO": "San Luis ___, CA",
    "OTTERS": "River swimmers", "PENSEE": "French for a thought",
    "PRAVDA": "Old Soviet daily", "PRENSA": "Press, in Spanish",
    "RAINED": "Poured", "RANDAL": "TIER3", "RASHES": "Skin breakouts",
    "REDYES": "Refreshes a faded color", "REMAPS": "Charts again",
    "RETOLD": "Recounted again", "SAGEST": "Wisest",
    "SARGES": "TIER3", "SHERRI": "TIER3",
    "SHTETL": "Eastern European Jewish village", "SIXTUS": "Pope's name",
    "SONDRA": "TIER3", "SPADED": "Dug into the garden",
    "SPORES": "Mushroom seeds", "STREWN": "Scattered about",
    "TAKETH": "The Lord giveth and ___ away", "TERRAN": "Of Earth, in sci-fi",
    "TOGAED": "Wearing classical garb", "TOMMIE": "TIER3",
    "TONIER": "More chichi",

    # ---------- length 7 ----------
    "APPARAT": "Soviet government machinery", "BASEMEN": "Infielders, plural",
    "BELTING": "Singing loudly", "CALIBAN": "Tempest creature",
    "CALYCES": "Flower bases, plural", "CARRARA": "Italian marble source",
    "CATTERY": "Boarding place for felines", "CHIPPED": "Nicked",
    "DEBRIEF": "Get the after-action report", "DESERET": "Utah's old name",
    "EMITTED": "Gave off", "EMPTIER": "Less full",
    "ENEMATA": "Medical procedures, plural", "EUGENIE": "British royal",
    "FOOTMEN": "Liveried servants", "GLADDER": "Happier",
    "INDWELT": "Resided within, archaically", "ISLANDS": "Manhattan and others",
    "LACIEST": "Most delicately patterned", "MONEYED": "Loaded",
    "NEMESES": "Arch-rivals, plural", "NEVILLE": "Singer Aaron",
    "OILIEST": "Most slick", "PEEBLES": "TIER3",
    "PHOEBES": "Insect-eating birds", "PISSOIR": "Public urinal, in France",
    "PLANKED": "Boarded up", "PROPPED": "Held up",
    "RADIALS": "Some tires", "RETEACH": "Go over the lesson again",
    "RETYPED": "Keyed in once more", "RUBIEST": "Reddest, like wine",
    "SALTING": "Curing meat", "SCARVES": "Winter wraps",
    "SOLARIA": "Sun rooms, plural", "SPACIER": "More daydreamy",
    "THROMBI": "Blood clots, plural", "TINIEST": "Smallest",
    "WHEELIE": "Bike trick",

    # ---------- length 8 ----------
    "AFRICANA": "African studies, briefly", "ALBRECHT": "Painter Durer's first name",
    "ALIASING": "Pixelated edge effect", "BEANPOLE": "Skinny person",
    "BUTTERED": "Spread on the bread", "CASELOAD": "Lawyer's burden",
    "CRAWLIES": "Creepy ___", "DATASETS": "Collections for analysis",
    "DOGGONED": "Heck-darn, mildly", "DORSALIS": "Of the back, in anatomy",
    "DRAGSTER": "Quarter-mile racer", "FERNANDO": "ABBA song",
    "FORESTED": "Tree-covered", "GREEDIER": "Hungrier for more",
    "GRISELDA": "Patient virtue, from Chaucer", "ITERATOR": "Coding loop helper",
    "LIVELIER": "More vivacious", "MERRIEST": "Most cheerful",
    "MISHEARD": "Got the words wrong", "MORDECAI": "Esther's cousin",
    "MOSSIEST": "Most overgrown", "OTOLITHS": "Inner ear stones",
    "PERTAINS": "Has to do with", "PHALANGE": "Finger bone",
    "PRESSMEN": "Print shop workers", "REEDITED": "Revised again",
    "RERECORD": "Cut a new version", "RESTAFFS": "Hires anew",
    "SCHWARTZ": "Author of 'Tuesdays with Morrie'", "SEEDIEST": "Most rundown",
    "SISSIEST": "Most timid", "SOOTHERS": "Pacifiers",
    "SPIRALED": "Wound downward", "SRIRACHA": "Hot sauce brand",
    "TWEEDIER": "More academic-looking",

    # ---------- length 9 ----------
    "AIRBUSSES": "European jets, plural", "ARCHFIEND": "Sworn enemy",
    "ASCORBATE": "Vitamin C salt", "COVARIATE": "Statistical variable",
    "CREEPIEST": "Most chilling", "ECLIPSING": "Overshadowing",
    "ELEVENSES": "Brit's midmorning snack", "EROSIONAL": "Of wearing away",
    "EUCALYPTI": "Aussie gum trees, plural", "FEATURING": "Starring",
    "GRISLIEST": "Most gory", "HARPOONER": "Whaler with a spear",
    "INSTATING": "Putting in office", "ITERATORS": "Loops in code",
    "LANGUEDOC": "French wine region", "MACADAMIA": "Hawaiian nut",
    "NATHANAEL": "TIER3", "NICKNAMED": "Called familiarly",
    "NONCREDIT": "Like an audit course", "ONRUSHING": "Bearing down",
    "OUTHOUSES": "Old backyard facilities", "PASSERSBY": "Sidewalk crowd",
    "PATTERSON": "Thriller writer James", "REINDEERS": "Santa's team, plural",
    "REMASTERS": "Updates old recordings", "RETURNERS": "Veterans coming back",
    "SARCOMATA": "Cancers, plural", "SCUMMIEST": "Most pondlike",
    "SHAREABLE": "Worth retweeting", "SKEWBALDS": "Spotted horses",
    "SLEAZEBAG": "Total creep", "TANGIBLES": "Touchable assets",

    # ---------- length 10 ----------
    "BELLADONNA": "Deadly nightshade", "PREPACKAGE": "Bundle in advance",
    "PROTESTORS": "Marchers, var.", "SMARTPHONE": "Pocket computer",
    "THROATIEST": "Most husky-voiced",

    # ---------- length 11 ----------
    "MIDFIELDERS": "Soccer middle players",
    "POLYAMORIES": "Multi-partner relationships",
    "SOUNDSCAPES": "Sonic environments",

    # ---------- length 13 ----------
    "MISDIAGNOSING": "Getting the illness wrong",

    # ---------- length 14 ----------
    "EMOTIONALIZING": "Making feelings the issue",
    "MORALISTICALLY": "Self-righteously",
    "NONCOLLECTABLE": "Not redeemable",
    "OVEROPTIMISTIC": "Pollyannaish",
    "STEREOCHEMICAL": "Of 3-D molecular structure",

    # ---------- length 15 ----------
    "DEMOGRAPHICALLY": "By population breakdown",
    "PHOTOMULTIPLIER": "Light-amplifying tube",
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
        else:
            if word not in fill:
                fill[word] = decision
                added_clues += 1

    (DATA / "fill_clues_ai.json").write_text(json.dumps(fill, indent=2, sort_keys=True))
    print(f"fill_clues_ai.json: added {added_clues} (now {len(fill)})")

    if new_tier3:
        block = (
            "\n# 15x15 sweep round-3 gap triage\n"
            + "\n".join(sorted(new_tier3)) + "\n"
        )
        with open(DATA / "tier3_force.txt", "a") as f:
            f.write(block)
    print(f"tier3_force.txt: added {len(new_tier3)}")


if __name__ == "__main__":
    main()
