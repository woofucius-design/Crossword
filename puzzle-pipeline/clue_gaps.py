"""
Triage every unclued entry from the 15x15 factory sweep:
  - real word with a non-leaking clue  ->  add to data/fill_clues_ai.json
  - junk / bare letters / no real meaning ->  add to data/tier3_force.txt

Run:  python3 clue_gaps.py
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

# word -> "TIER3" (prune) or clue string (add to fill_clues_ai)
DECISIONS: dict[str, str] = {
    # ---------- length 3 ----------
    "AAL": "TIER3", "ADV": "Wrestling letters", "AFB": "USAF base abbr.",
    "AFR": "TIER3", "AHO": "TIER3", "ALK": "TIER3", "AMU": "Atomic mass unit",
    "ANC": "Mandela's party, briefly", "AOR": "TIER3", "ARG": "TIER3",
    "ARN": "TIER3", "AVE": "Street crossing, briefly", "BAE": "Modern term of endearment",
    "BRR": "Cold reaction", "BUL": "TIER3", "CIF": "TIER3", "CPL": "Army E-4, briefly",
    "CRE": "TIER3", "CTF": "Hacker contest, briefly", "DAP": "Greet with a fist bump",
    "DET": "Sleuth, briefly", "DLR": "TIER3", "EEO": "Workplace fairness, briefly",
    "ENC": "Postal abbr.", "ENG": "Maker of bridges, briefly", "ENV": "Letter holder, briefly",
    "FPM": "TIER3", "GOI": "TIER3", "GOL": "TIER3", "GTE": "TIER3",
    "HAE": "Have, in Glasgow", "HCL": "Stomach acid", "HOC": "Ad ___",
    "HON": "Term of endearment", "HRH": "Royal title, briefly", "HTS": "TIER3",
    "IBA": "TIER3", "IBO": "Nigerian people", "IGN": "TIER3", "IHS": "Christogram",
    "ILA": "TIER3", "IMA": "Bandleader Sumac", "INA": "Actress Garten",
    "ISS": "Orbiting lab, briefly", "KAY": "Singer Lenny ___",
    "LAI": "TIER3", "LAK": "TIER3", "LEN": "Actor ___ Cariou",
    "LNG": "Liquefied gas, briefly", "LOC": "Whereabouts, briefly", "LUB": "TIER3",
    "MAI": "TIER3", "MAL": "TIER3", "MAU": "TIER3", "MEA": "___ culpa",
    "MEH": "Shrug response", "MEO": "TIER3", "MER": "Sea, in Marseille",
    "MGD": "TIER3", "MOC": "TIER3", "MSL": "TIER3", "MTG": "Meeting, on a calendar",
    "NAR": "TIER3", "NOU": "TIER3", "OCK": "TIER3", "OCR": "Scanning tech, briefly",
    "ONT": "TIER3", "OOH": "Reaction to fireworks", "ORL": "TIER3",
    "OSC": "TIER3", "OUD": "Lute of the Mideast", "OVA": "Eggs, biologically",
    "PAH": "Bah!", "PHU": "TIER3", "PPD": "TIER3", "PPS": "After-PS afterthought",
    "PRN": "TIER3", "PWN": "Crush, in gamer slang", "PYM": "Marvel's Hank ___",
    "QID": "TIER3", "RAH": "Cheerleader's cry", "RCT": "TIER3",
    "REH": "TIER3", "RHE": "TIER3", "RIK": "TIER3", "RIN": "TIER3",
    "RMS": "TIER3", "SAB": "TIER3", "SAE": "Frat letters", "SAK": "TIER3",
    "SEI": "Baleen whale", "SEQ": "TIER3", "SER": "TIER3", "SGT": "Stripes wearer, briefly",
    "SHH": "Hush!", "SIL": "TIER3", "SKA": "Reggae precursor",
    "SRO": "Sold-out sign, briefly", "STG": "TIER3", "SYM": "TIER3",
    "TOI": "You, to Yves", "TVA": "TIER3", "UAW": "Detroit union",
    "UBI": "TIER3", "UBS": "Swiss bank", "UDI": "TIER3", "UMM": "Stalling sound",
    "UNA": "One, in Italy", "UNC": "Family Cousin's father",
    "URI": "Spoonbender Geller", "VEE": "Neckline shape", "VEL": "TIER3",
    "VHS": "Predecessor of DVD", "VOA": "TIER3", "VOL": "Library set, briefly",
    "YAT": "TIER3",

    # ---------- length 4 ----------
    "ABIE": "Old-time name", "ACLU": "Civil rights org.", "ADAN": "TIER3",
    "AGIN": "Opposed, in dialect", "AGIT": "TIER3", "ALIA": "Et ___",
    "AMAL": "TIER3", "AMAR": "TIER3", "AMOS": "Biblical prophet",
    "ANDS": "Linking words", "ANNO": "___ Domini", "APPS": "Phone downloads",
    "ARTE": "TIER3", "ARYA": "Stark of 'Game of Thrones'", "ASCI": "TIER3",
    "ASSI": "TIER3", "ATMA": "TIER3", "ATTA": "Encouraging cry, '___ boy'",
    "AYRE": "TIER3", "BACT": "TIER3", "BAPT": "TIER3", "BEIN": "TIER3",
    "BENA": "TIER3", "BIBI": "Israeli PM Netanyahu, familiarly", "BLDG": "Skyscraper, briefly",
    "BONA": "___ fide", "BROD": "TIER3", "BROS": "Buddies, briefly",
    "CALC": "AP math class, briefly", "CANA": "Wedding-miracle town",
    "CAPA": "Photographer Robert ___", "CARA": "Singer Irene ___",
    "CATV": "Old TV delivery, briefly", "CECA": "TIER3", "CEPA": "TIER3",
    "CERN": "Geneva research lab", "CHAO": "Trump cabinet member Elaine ___",
    "CHEM": "AP class, briefly", "CHET": "Newsman Huntley", "CLIN": "TIER3",
    "COMS": "TIER3", "CORK": "Bottle stopper", "COTT": "TIER3",
    "CREA": "TIER3", "CTRL": "Keyboard key", "DATE": "Calendar entry",
    "DESI": "Lucy's TV husband", "DICT": "TIER3", "DONN": "TIER3",
    "DONT": "\"Stop!\", informally", "DORI": "Finding Nemo's friend",
    "DOSA": "South Indian crepe", "DRAT": "\"Foiled again!\"",
    "EBEN": "TIER3", "ECCL": "TIER3", "EDNA": "Aunt in 'Hairspray'",
    "ELEM": "Periodic table entry, briefly", "ELLA": "Singer Fitzgerald",
    "ELLE": "Magazine for women", "EMIL": "TIER3", "EMOS": "Goth's cousins",
    "ENGR": "Bridge designer, briefly", "ERIK": "Hockey's Karlsson",
    "ESPN": "Sports network", "ETTA": "Singer James", "FIXE": "Idee ___",
    "FURN": "TIER3", "GENL": "TIER3", "GINA": "Actress Gershon",
    "GMAT": "B-school exam", "GOVT": "Uncle Sam's outfit, briefly",
    "HEIN": "TIER3", "HGWY": "Interstate, briefly", "HIYA": "Casual greeting",
    "HOON": "TIER3", "HOPI": "Pueblo people", "HUEY": "Helicopter type",
    "HYDE": "Stevenson's Mr. ___", "INTL": "Global, briefly",
    "INTR": "TIER3", "IPSE": "TIER3", "IRAS": "Nest eggs, briefly",
    "ISDN": "Old phone line, briefly", "ITZA": "Chichen ___",
    "JONI": "Singer Mitchell", "KARI": "Skater Strug, alt sp.", "KARL": "Philosopher Marx",
    "KOKO": "Famous signing gorilla", "LACS": "TIER3", "LAIN": "Reclined",
    "LARA": "Croft of video games", "LECT": "TIER3", "LEHI": "TIER3",
    "LIRE": "Old Italian money", "LOIS": "Lane of Metropolis", "LORA": "TIER3",
    "LOWA": "TIER3", "LSAT": "Law school exam", "LYSE": "Break open, as a cell",
    "MACY": "Department store namesake", "MAHI": "___-mahi (fish)",
    "MANI": "Half a salon visit", "MBPS": "Net speed, briefly",
    "MENO": "Less, in music", "MERC": "British dictionary publisher, briefly",
    "METS": "NL East team", "MOET": "Champagne brand", "MOHR": "TIER3",
    "NAIR": "Hair-removal brand", "NATE": "Berkus of TV", "NATL": "Across-the-board, briefly",
    "NCAA": "March Madness org.", "NEIL": "Astronaut Armstrong",
    "NEMO": "Finding ___", "NITE": "Late hour, informally", "NOLA": "The Big Easy, briefly",
    "NOTA": "TIER3", "NSEC": "TIER3", "OGPU": "Old Soviet police",
    "OHMS": "Resistance units", "OILS": "Painter's choice", "OLDE": "Quaint shoppe word",
    "OLES": "Bullring cheers", "OLOF": "Slain Swedish PM Palme", "OMAR": "Actor Sharif",
    "ONAN": "Biblical sinner", "OOOO": "Reaction to fireworks", "OOPS": "\"My bad!\"",
    "OPED": "Newspaper page", "ORIG": "Authentic, briefly", "PASO": "El ___, Texas",
    "PATA": "TIER3", "PERP": "Suspect, in cop talk", "PHIL": "Talk show host Donahue",
    "PIUS": "Pope's name 12 times", "POOS": "TIER3", "PRUE": "Eldest 'Charmed' sister",
    "PSST": "\"Hey, you!\"", "PYKE": "TIER3", "RALL": "TIER3",
    "RAVI": "Sitarist Shankar", "RCPT": "Cashier's tear-off, briefly",
    "REBA": "Country singer McEntire", "RECS": "Suggestions, briefly",
    "RECT": "TIER3", "REGO": "TIER3", "REMI": "Animated rat chef",
    "RIGA": "Latvia's capital", "RISS": "TIER3", "ROND": "TIER3",
    "ROXY": "Music venue name", "RYAN": "Reynolds of film", "SACO": "Maine river",
    "SADO": "TIER3", "SANK": "Went under", "SAPA": "TIER3", "SARA": "Singer Bareilles",
    "SASE": "Mail-in inclusion, briefly", "SASK": "Canadian prov.",
    "SATI": "TIER3", "SEEN": "Witnessed", "SEIS": "Half a dozen, in Madrid",
    "SELE": "TIER3", "SERO": "TIER3", "SERS": "TIER3", "SHER": "TIER3",
    "SIDI": "TIER3", "SIMS": "Long-running EA game", "SKAL": "TIER3",
    "SOLI": "Music for one, plural", "SPED": "Drove too fast",
    "STAM": "TIER3", "STER": "TIER3", "STOA": "Greek portico", "SVEN": "Frozen reindeer",
    "TALI": "Anklebones", "TANO": "TIER3", "TEAS": "Afternoon meals",
    "TEED": "Set up the golf ball", "TEMA": "TIER3", "TENS": "Big bills",
    "TEWA": "TIER3", "THEY": "Third-person plural", "THRO": "Through, poetically",
    "TNPK": "Toll road, briefly", "TONI": "Author Morrison", "TONY": "Broadway award",
    "TRAC": "TIER3", "TRAN": "TIER3", "TRAV": "TIER3", "TRIN": "TIER3",
    "TROP": "TIER3", "USEE": "TIER3", "USIA": "TIER3", "WORE": "Had on",
    "YEGG": "Safecracker, in old slang", "YIPE": "Yelp of pain",
    "YURI": "Cosmonaut Gagarin", "YVES": "Saint Laurent of fashion",

    # ---------- length 5 ----------
    "ABBAS": "Palestinian leader Mahmoud", "ADLAI": "1952 candidate Stevenson",
    "AGERS": "TIER3", "AGRIC": "TIER3", "AHMAD": "Common Arabic name",
    "ALCOA": "Aluminum giant", "ALOHA": "Hawaiian hello", "ALTAI": "Asian mountain range",
    "AMADO": "Brazilian novelist Jorge", "AMARA": "TIER3", "ANDRE": "Tennis great Agassi",
    "ANIMO": "TIER3", "ANTIQ": "TIER3", "ARCOS": "TIER3", "ARSED": "TIER3",
    "ARTSY": "Pretentiously aesthetic", "ASSES": "Pack animals",
    "ASSOC": "Trade group, briefly", "ATRIA": "Heart chambers",
    "AUDRA": "Singer McDonald", "AWAYS": "Distances off",
    "AYALA": "Mexican folk hero", "AYERS": "Australian rock",
    "BAIRD": "TV pioneer John Logie", "BANCA": "TIER3", "BANDO": "TIER3",
    "BLUET": "Small blue flower", "BOBBI": "TIER3", "BODHI": "Buddhist enlightenment",
    "BOLTS": "Hardware store buys", "BOYCE": "Actor Cameron",
    "CALEB": "Biblical spy", "CANST": "Bible's \"are you able\"",
    "CARLI": "Soccer star Lloyd", "CARPI": "Wrist bones",
    "CELEB": "Star, briefly", "CHERE": "Dear, in Paris",
    "CLARA": "Red Cross founder Barton", "COEDS": "Mixed-school students",
    "COHEN": "Singer Leonard", "COMME": "Like, in French",
    "CONTD": "More on the next page, briefly", "CRAIG": "Bond actor Daniel",
    "CRISS": "Magician Angel", "DARYA": "TIER3", "DARYL": "Hannah of film",
    "DATER": "One seeking romance", "DAUBE": "TIER3", "DECCA": "Old record label",
    "DELIA": "Cookbook author Smith", "DILLY": "Real beauty, in slang",
    "DISTR": "TIER3", "DOBRO": "Resonator guitar", "DOLPH": "Lundgren of action films",
    "DORSI": "Latissimus ___", "EARLE": "Singer Steve", "EATEN": "Consumed",
    "EBERT": "Late film critic Roger", "ECOLE": "School, in Lyon",
    "EDGER": "Lawn-tidying tool", "EDSEL": "Famous Ford flop",
    "ELDER": "Senior member", "ELLEN": "Talk show host DeGeneres",
    "ELMER": "Bugs' \"wabbit\" hunter", "ELROY": "Jetson boy",
    "ELTON": "Sir John", "EMACS": "Coder's editor",
    "ENIAC": "Early computer", "ENOCH": "Biblical patriarch",
    "ENRON": "Infamous energy firm", "EQUIV": "Same as, briefly",
    "ERNIE": "Sesame Street roommate", "EXURB": "Far suburb",
    "FIERI": "TV chef Guy", "FREDA": "TIER3", "GIRTS": "TIER3",
    "GONNA": "Going to, casually", "GRETA": "Actress Garbo",
    "GUPTA": "TIER3", "GUYED": "Steadied with ropes", "HARAM": "Forbidden, in Islam",
    "HENAN": "Chinese province", "HENRI": "Painter Matisse",
    "HIVED": "Stored, as bees do", "HOSED": "Sprayed with water",
    "HSUAN": "TIER3", "IDENT": "Station identifier", "IMBER": "TIER3",
    "IMPER": "TIER3", "INBOX": "Where new emails arrive", "INDIO": "California city",
    "IRENE": "Hurricane of 2011", "IRGUN": "TIER3", "IVIED": "Like Princeton's walls",
    "KELLI": "Actress Garner", "KERRY": "Former Sec. of State John",
    "KMART": "Discount chain", "LANNY": "TIER3", "LEANT": "Inclined, British style",
    "LEMME": "Allow me, informally", "LENNY": "Bruce of comedy",
    "LEONE": "Western film director Sergio", "LEPTA": "Greek pennies",
    "LIDIA": "TV chef Bastianich", "LIMED": "Treated with calcium oxide",
    "LOGON": "Sign-on event", "LONGA": "TIER3", "LOSES": "Misplaces",
    "LOVEY": "Term of endearment", "LUCIO": "TIER3", "LURIA": "TIER3",
    "LYNNE": "Singer-songwriter Jeff", "MAHAL": "Taj ___",
    "MAIRE": "TIER3", "MANAS": "TIER3", "MANOS": "Hands, in Madrid",
    "MARCI": "TIER3", "MAREK": "TIER3", "MINDS": "Pays attention to",
    "MINGO": "TIER3", "MINOT": "North Dakota city", "MOVED": "Changed homes",
    "MUANG": "TIER3", "NEWTS": "Pond salamanders", "NICHT": "Not, in Berlin",
    "NITRO": "Explosive shortened form", "NOVAE": "Stellar bursts",
    "NYAYA": "TIER3", "OCALA": "Florida city", "ODELL": "TIER3",
    "OPING": "TIER3", "ORAGE": "TIER3", "OSTIA": "Mouths of rivers",
    "PAMPA": "Argentine plain", "PASSU": "TIER3", "PERLA": "TIER3",
    "PIKED": "Dove with a bent body", "PONCE": "Spanish explorer ___ de Leon",
    "PRIED": "Worked loose with a lever", "PRIMI": "TIER3", "RALES": "Lung sounds",
    "RAMON": "Spanish form of Raymond", "RAMOS": "Soccer star Sergio",
    "REBBE": "Hasidic leader", "REDUX": "Brought back", "REINA": "Queen, in Madrid",
    "REORG": "Corporate shake-up, briefly", "RESAT": "Took the test again",
    "REYNA": "TIER3", "RICER": "Potato-mashing tool",
    "ROLFE": "TIER3", "RUDGE": "TIER3", "SAHEL": "African region south of the Sahara",
    "SALTA": "Argentine city", "SENSO": "TIER3", "SERIO": "TIER3",
    "SHAKA": "Zulu king", "SIMBA": "Lion King protagonist", "SIMUL": "TIER3",
    "SITUP": "Crunch alternative", "SLEPT": "Caught some Zs",
    "SOTHO": "Lesotho language", "SPANN": "TIER3", "STINE": "Goosebumps writer R.L.",
    "STOTT": "TIER3", "STROM": "Late Sen. Thurmond", "SULCI": "Brain grooves",
    "SWUNG": "Took a cut at the ball", "TANIA": "TIER3", "TANNA": "TIER3",
    "TAPIA": "TIER3", "TAURI": "T ___ stars", "TEARS": "Drops of grief",
    "TEMPI": "Music speeds", "TERRE": "Earth, to Pierre", "TESSA": "Thompson of film",
    "TIRER": "TIER3", "TITUS": "Roman emperor", "TOGAE": "TIER3",
    "TOLAN": "TIER3", "TOOLS": "Workshop items", "TORII": "Shinto shrine gates",
    "TRACI": "TIER3", "UDALL": "Late Sen. Mo", "ULNAE": "Forearm bones",
    "UNRRA": "TIER3", "UTHER": "King Arthur's father", "VACUA": "Empty spaces",
    "VICKI": "Singer Lawrence", "VOILA": "\"There it is!\"",
    "WANNA": "Want to, casually", "WOKEN": "Roused from sleep",

    # ---------- length 6 ----------
    "AMTRAK": "U.S. passenger rail service", "ANCIEN": "Old, in French",
    "ANDREI": "Russian author Bely", "ANNULI": "Rings, in geometry",
    "BANDAR": "Persian port prefix", "BARFLY": "Tavern regular",
    "BELOIT": "Wisconsin college town", "BERNIE": "Sen. Sanders",
    "BEULAH": "Old gospel hymn", "BIHARI": "Indian regional language",
    "BREVIS": "Brief, in Latin", "COOMBS": "TIER3", "CRUCES": "Las ___, NM",
    "CURERS": "Smokehouse workers", "DAGMAR": "TIER3", "DARIUS": "Persian king",
    "DECCAN": "Indian plateau", "DICIER": "Riskier", "DUCTED": "Channeled through pipes",
    "DUELED": "Fought one-on-one", "EASIER": "Less difficult",
    "ELISHA": "Biblical prophet", "ESDRAS": "Apocryphal book",
    "FIRTHS": "Scottish inlets", "FORBES": "Business magazine",
    "FRIEDA": "TIER3", "FULANI": "West African people", "GAINST": "Opposed, poetically",
    "GEARED": "Aimed at", "GERALD": "Pres. Ford", "GILROY": "California garlic capital",
    "GOOIER": "Stickier", "GORMAN": "Poet Amanda", "GRADED": "Marked, as essays",
    "GROSSO": "Big, in Italian", "HARING": "Pop artist Keith",
    "HIDERS": "Seekers' opposites", "HOOVES": "Equine feet",
    "HUERTA": "TIER3", "ICEMEN": "Rink workers", "ICIEST": "Most frozen-over",
    "ICKIER": "More disgusting", "INITIO": "Ab ___ (from the start)",
    "INLINE": "Like some skates", "KRESGE": "Old retail name",
    "LENAPE": "Native people of the Delaware", "LEXICA": "Dictionaries, formally",
    "MARGIE": "Old-fashioned name", "MATEYS": "Pirate buddies",
    "MEGHAN": "Duchess of Sussex", "NATURA": "Naturally, in Latin",
    "NICOLO": "TIER3", "NOREEN": "TIER3", "OBEYED": "Followed orders",
    "ODORED": "Smelly, archaically", "OLEATE": "Acid salt",
    "PALOMA": "Picasso's daughter", "PHOOEY": "Disgusted exclamation",
    "PINNAE": "Outer ear parts", "PUERTO": "___ Rico",
    "RAFAEL": "Tennis star Nadal", "REBIDS": "Tries again at auction",
    "RECONS": "Scouting missions, briefly", "REHANG": "Put back on the wall",
    "RINSED": "Cleared with water", "ROADIE": "Concert tour crew member",
    "RUNOUT": "Cricket dismissal", "SALLIE": "TIER3",
    "SANSEI": "Third-generation Japanese American", "SCARPA": "TIER3",
    "SCHONE": "TIER3", "SERENO": "TIER3", "SHOLOM": "TIER3",
    "SIECLE": "Fin de ___", "SILANE": "Silicon hydride",
    "SIRREE": "\"No, ___!\"", "SNYDER": "Filmmaker Zack",
    "SPRATS": "Small herrings", "SPRIER": "More agile",
    "STELAE": "Ancient stone slabs", "STRIAE": "Streaks",
    "TATAMI": "Floor mat in Japan", "TILSIT": "German cheese",
    "TRISHA": "Yearwood of country music", "TUAREG": "Saharan nomadic people",
    "USENET": "Old discussion network", "VEGGES": "TIER3",
    "VERIER": "TIER3", "WEBBED": "Like duck feet",

    # ---------- length 7 ----------
    "ACANTHI": "Architectural ornaments", "AGONIES": "Throes of suffering",
    "ARPANET": "Internet's predecessor", "ARTIEST": "Most pretentious",
    "AVIONIC": "Of aircraft electronics", "BALLSES": "TIER3",
    "BRUSSEL": "TIER3", "CANDIDA": "Yeast genus", "CAPLETS": "Pill shapes",
    "CHICHIS": "Pretentious sorts", "CHIMERS": "Bell-ringers",
    "DESIRED": "Wanted", "DOZIEST": "Most drowsy", "DROOLED": "Slobbered",
    "DUODENA": "Parts of the small intestine, plural", "EDUARDO": "Spanish form of Edward",
    "ENURING": "Becoming accustomed", "ERECTED": "Built up",
    "ESTRADA": "Erik of \"CHiPs\"", "EVELINE": "Joyce story heroine",
    "EVILLER": "More wicked", "EZEKIEL": "Biblical prophet",
    "FRANCIA": "Spanish name for France", "GENESEE": "Upstate NY river",
    "HARDHAT": "Construction site gear", "HISPANO": "Spanish, in compounds",
    "IMAGIST": "Early 20th-century poet", "INSIGNE": "Single badge",
    "KRISTIN": "Chenoweth of Broadway", "LATICES": "Lattices, archaically",
    "LOCARNO": "Swiss treaty city", "MARRING": "Disfiguring",
    "NAPALMS": "Wartime incendiaries", "NAUTILI": "Sea snails, plural",
    "NOODLED": "Improvised musically", "OARSMEN": "Crew members",
    "ONEIDAS": "Iroquois nation members", "PAULINA": "Czech-born model Porizkova",
    "PENSEES": "Pascal's thoughts", "PHILLIP": "Variant spelling of a common name",
    "POOHING": "TIER3", "PRINTED": "Sent to the press",
    "QUORATE": "Having enough members present", "RANDIER": "Hornier",
    "RATTIER": "Shabbier", "REHANGS": "Reinstalls on the wall",
    "RETESTS": "Takes the exam again", "RIGOURS": "Hardships, in British spelling",
    "SCUMBAG": "Lowlife", "SEAMIER": "Sleazier", "SHIFTED": "Moved over",
    "SNOWMEN": "Winter sculptures", "SOLOIST": "Featured musician",
    "SORRIER": "More regretful", "SPANNED": "Bridged",
    "SPARKED": "Set off", "SUBNETS": "Computer network slices",
    "TOOTSIE": "1982 Hoffman film", "UPTREND": "Rising pattern",

    # ---------- length 8 ----------
    "ANTISERA": "Disease-fighting injections", "ASSHOLES": "Rude folks",
    "ASSUREDS": "Insurance policyholders", "BOREALIS": "Aurora ___",
    "BRATTIER": "More spoiled", "CASHMERE": "Luxury wool",
    "CHERUBIM": "Heavenly beings", "CLEANSES": "Detoxes, in spa lingo",
    "CONCERTI": "Orchestral works, plural", "CONTESSA": "Italian countess",
    "DAIRYMEN": "Milk producers", "ENAMELED": "Glossed with finish",
    "ESSENTIA": "TIER3", "FLAPPING": "Waving wildly",
    "FORETOLD": "Predicted", "GODAWFUL": "Truly terrible",
    "GRETCHEN": "Actress Mol", "INBREEDS": "Crosses within a family",
    "MACASSAR": "Old Indonesian port", "MARIANNE": "Symbol of the French Republic",
    "MAUSOLEA": "Burial monuments, plural", "MCDONALD": "Old MacDonald, e.g.",
    "MONTAGUE": "Romeo's family name", "NOISIEST": "Most clamorous",
    "ONONDAGA": "Iroquois nation member", "PAYLOADS": "Cargo amounts",
    "SETTABLE": "Adjustable to a value", "SHOSHONE": "Western U.S. tribe",
    "SPACIEST": "Most absent-minded", "STEPHANE": "French Stephen",
    "TEDESCHI": "Singer Susan", "TELETEXT": "TV info service",
    "THRASHED": "Beat soundly", "TINTYPES": "Old photo prints",
    "TOASTIER": "Warmer", "UROLOGIC": "Of the urinary system",
    "ZESTIEST": "Most lively",

    # ---------- length 9 ----------
    "CANDLELIT": "Romantically illuminated", "CAREERIST": "Ambitious climber",
    "CATHARINE": "Russian empress, var.", "CATHOLICS": "Pope's congregation",
    "CAVALIERI": "TIER3", "CHOCOLATY": "Like a cocoa dessert",
    "CLUMSIEST": "Most awkward", "CONNIVERS": "Schemers",
    "CROPLANDS": "Farming acreage", "ENAMELLER": "Finish applier",
    "FLOWERBED": "Garden patch", "FRANCISCA": "Spanish woman's name",
    "FREDERICA": "Old-fashioned woman's name", "LECTURERS": "Junior faculty",
    "MILLENNIA": "Long stretches of time", "OCEANSIDE": "California beach town",
    "SCALLOPED": "Cooked with breadcrumbs", "SILVESTER": "TIER3",
    "SNAKESKIN": "Snake's shedding", "SNAPPIEST": "Wittiest",
    "SPARKIEST": "Most vivacious", "STEAMPUNK": "Victorian sci-fi genre",
    "SUBSERIES": "Smaller set within a series", "THOMISTIC": "Of Aquinas's philosophy",
    "UNDERTOOK": "Started a task",

    # ---------- length 10 ----------
    "NONNUCLEAR": "Like a fossil fuel plant", "SEASONINGS": "Pantry staples",
    "SUPERSTATE": "Vast political entity",

    # ---------- length 11 ----------
    "ACCENTUATED": "Stressed", "NONALLERGIC": "Free of itchy reactions",
    "PORTRAITIST": "Painter of faces",

    # ---------- length 13 ----------
    "MACROECONOMIC": "Of broad money matters",

    # ---------- length 14 ----------
    "CONFEDERATIONS": "Loose unions of states",
    "PHOTOENGRAVERS": "Image-plate makers",

    # ---------- length 15 ----------
    "ACETYLSALICYLIC": "Aspirin's main acid",
    "ANESTHETIZATION": "Putting under for surgery",
    "CHARLOTTESVILLE": "Virginia college town",
    "INTERVENTIONIST": "One who steps in",
    "RECRYSTALLIZING": "Reforming as a solid",
    "TOASTMISTRESSES": "Ceremony emcees",
}


def main() -> None:
    # Load existing files
    fill = json.load(open(DATA / "fill_clues_ai.json"))
    tier3_text = (DATA / "tier3_force.txt").read_text()
    tier3_set: set[str] = set()
    for line in tier3_text.splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            tier3_set.add(s)

    added_clues = 0
    added_tier3 = 0
    new_tier3: list[str] = []
    for word, decision in DECISIONS.items():
        if decision == "TIER3":
            if word not in tier3_set:
                new_tier3.append(word)
                tier3_set.add(word)
                added_tier3 += 1
        else:
            if word not in fill:
                fill[word] = decision
                added_clues += 1

    # Write fill_clues_ai
    (DATA / "fill_clues_ai.json").write_text(json.dumps(fill, indent=2, sort_keys=True))
    print(f"fill_clues_ai.json: added {added_clues} clues (now {len(fill)} total)")

    # Append to tier3_force.txt
    if new_tier3:
        block = (
            "\n# 15x15 sweep gap triage: junk strings the constructor doesn't want\n"
            + "\n".join(sorted(new_tier3)) + "\n"
        )
        with open(DATA / "tier3_force.txt", "a") as f:
            f.write(block)
    print(f"tier3_force.txt: added {added_tier3} entries")


if __name__ == "__main__":
    main()
