"""
Second pass: triage gaps from the post-pruning 15x15 factory sweep.
Same shape as clue_gaps.py.
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

DECISIONS: dict[str, str] = {
    # ---------- length 3 ----------
    "AET": "TIER3", "ALD": "TIER3", "APH": "TIER3", "AVG": "Stat for a slugger, briefly",
    "BAL": "TIER3", "BBB": "Consumer watchdog, briefly", "BBC": "U.K. broadcaster",
    "BDE": "TIER3", "BRO": "Sibling, briefly", "CCM": "TIER3", "CDT": "Texas time, briefly",
    "CHN": "TIER3", "COE": "TIER3", "CPO": "Navy E-7, briefly", "DHU": "TIER3",
    "EOF": "End-of-file marker, briefly", "FWD": "Email tag", "GCD": "Math abbr.",
    "GHI": "TIER3", "HEB": "Biblical book, briefly", "HOR": "TIER3", "INV": "TIER3",
    "KIM": "Singer Kardashian", "LIQ": "TIER3", "LOE": "TIER3", "LOF": "TIER3",
    "LUD": "TIER3", "LUE": "TIER3", "MIC": "Open ___ night",
    "MME": "Madame, briefly", "MTN": "Big peak, briefly", "NAW": "Nope, casually",
    "NEH": "TIER3", "ODA": "TIER3", "OIK": "Brit's lout", "ONA": "TIER3",
    "ORY": "TIER3", "PDT": "West Coast time, briefly", "PHR": "TIER3",
    "PIR": "TIER3", "PLU": "TIER3", "PPI": "TIER3", "PPR": "TIER3",
    "PUL": "TIER3", "RCA": "Old electronics brand", "RDA": "Nutrition label number, briefly",
    "RIF": "TIER3", "SHR": "TIER3", "SPS": "TIER3", "SUF": "TIER3", "SUI": "___ generis",
    "SVG": "TIER3", "TTY": "Old terminal, briefly", "TYP": "TIER3",
    "UAR": "TIER3", "URB": "TIER3", "USP": "TIER3", "USW": "TIER3",
    "VAI": "TIER3", "VAL": "Actor Kilmer", "VER": "TIER3", "VOC": "TIER3",
    "WER": "TIER3", "WES": "Filmmaker Anderson",

    # ---------- length 4 ----------
    "AFDC": "TIER3", "ALDO": "Shoe brand", "ALEX": "Trebek of Jeopardy!",
    "AMIS": "Novelist Kingsley", "ANNI": "Years, in Rome", "ATTY": "Lawyer, briefly",
    "AULA": "TIER3", "BALA": "TIER3", "BANI": "TIER3", "BIOL": "Lab class, briefly",
    "BOTT": "TIER3", "BOWE": "Boxer Riddick", "BREE": "Soft cheese variant",
    "CAPT": "Ship's commander, briefly", "CARR": "Author Caleb", "CATO": "Roman statesman",
    "CERA": "Actor Michael", "CHGE": "TIER3", "CLAR": "TIER3", "CLOS": "TIER3",
    "COED": "Mixed-gender", "COMR": "TIER3", "CONV": "TIER3", "CORR": "TIER3",
    "CORT": "TIER3", "DELS": "TIER3", "DIPL": "TIER3", "DIST": "TIER3",
    "DOON": "TIER3", "DORA": "TV explorer", "DOSH": "British slang for cash",
    "DUES": "Club fees", "EARP": "Wyatt of Tombstone", "EDUC": "Schooling, briefly",
    "ELEV": "TIER3", "EURE": "TIER3", "FEET": "Twelve-inch units",
    "FINI": "Done, in Paris", "FLOR": "TIER3", "GRAS": "Mardi ___",
    "GRAV": "TIER3", "GREG": "Heffley of 'Diary of a Wimpy Kid'",
    "GYRI": "Brain ridges", "HAEC": "TIER3", "HERS": "Possessive pronoun",
    "HOVE": "Heaved up", "HUNG": "Suspended", "IKEA": "Swedish furniture giant",
    "INCL": "TIER3", "INEZ": "TIER3", "IPSO": "___ facto",
    "JEFE": "Boss, in Spanish", "KANS": "TIER3", "KCAL": "Food-energy unit, briefly",
    "KOTA": "TIER3", "KWAN": "Olympic skater Michelle", "LARS": "Director von Trier",
    "LAUE": "TIER3", "LELA": "TIER3", "LEPT": "TIER3", "LIDA": "TIER3",
    "LULA": "Former Brazil president da Silva", "LYME": "Tick-borne disease",
    "MALO": "TIER3", "MEIN": "Lo ___ (noodle dish)", "MENE": "TIER3",
    "MIMI": "La Boheme heroine", "MOOG": "Synth pioneer Robert",
    "MSGR": "Catholic title, briefly", "MURA": "TIER3", "NEUT": "TIER3",
    "NIUE": "Pacific island nation", "NOIR": "Film genre",
    "NORI": "Sushi seaweed", "OLAF": "Frozen snowman", "OLGA": "Russian name",
    "ORCS": "Tolkien baddies", "ORDO": "Order, in Latin", "ORIN": "TIER3",
    "ORTH": "TIER3", "ORTS": "Table scraps", "OREG": "Beaver State, briefly",
    "OURS": "Belonging to us", "PANI": "TIER3", "PARI": "TIER3",
    "PERL": "Scripting language", "PETE": "Sampras of tennis",
    "PETR": "TIER3", "PHOS": "TIER3", "PISO": "TIER3", "PRET": "TIER3",
    "PRIV": "TIER3", "PRON": "TIER3", "PROV": "TIER3", "PSIA": "TIER3",
    "RAUL": "Cuba's Castro brother", "REDD": "Foxx of comedy", "REPT": "TIER3",
    "ROBT": "TIER3", "ROKU": "Streaming device", "ROTI": "Indian flatbread",
    "SAKS": "Fifth Avenue retailer", "SANT": "TIER3", "SEIF": "TIER3",
    "SERI": "TIER3", "SHIH": "___ Tzu", "SHOR": "TIER3", "SHUL": "Synagogue",
    "SMIT": "TIER3", "SOTO": "Slugger Juan", "STAD": "TIER3",
    "STAN": "Devoted fan, in slang", "STAT": "ASAP, in medicine",
    "SUPT": "School official, briefly", "TECK": "TIER3", "THAD": "TIER3",
    "TIEN": "TIER3", "TOED": "Walked carefully", "TOLA": "TIER3",
    "TORI": "Spelling of TV", "TOTO": "Dorothy's dog", "TRIB": "TIER3",
    "TUAN": "TIER3", "TUTS": "Disapproving sounds", "URAL": "Russian mountains",
    "VERA": "Author Brittain", "VITA": "Curriculum ___", "VOCE": "Sotto ___",
    "WACE": "TIER3", "WETS": "Soaks", "WYSS": "TIER3",

    # ---------- length 5 ----------
    "ACHOO": "Sneeze sound", "ADMIN": "Office worker, briefly",
    "AGNES": "Hurricane of 1972", "AHMED": "Arabic name", "AIMEE": "Singer Mann",
    "AIRED": "Broadcasted", "AKITA": "Japanese dog breed",
    "ALAIN": "Author Robbe-Grillet", "ALDUS": "Publisher Manutius",
    "ALOIS": "Hitler's father", "AMIGA": "Old Commodore computer",
    "ANSEL": "Photographer Adams", "ANTAL": "Conductor Dorati",
    "AROSE": "Got up", "BALER": "Hay-processing machine",
    "BAMBI": "Disney fawn", "BANDE": "TIER3", "BARDO": "Tibetan limbo",
    "BHAJI": "Indian fritter", "BICEP": "Arm muscle, casually",
    "BONED": "Removed fish skeletons", "BOURG": "TIER3", "BUNIN": "Russian Nobel laureate",
    "CACAO": "Chocolate source", "CARPE": "___ diem", "CASAS": "Spanish houses",
    "CHIEN": "Dog, in Paris", "CHITA": "Performer Rivera", "CHLOR": "TIER3",
    "CHRIS": "Actor Pratt", "CLAUS": "Santa's surname", "COLEY": "TIER3",
    "COPIA": "TIER3", "CROCI": "Spring bloomers, formally", "CYANO": "TIER3",
    "DALAI": "___ Lama", "DAMME": "TIER3", "DANAE": "Greek myth princess",
    "DEALT": "Distributed cards", "DEBYE": "Dutch physicist Peter",
    "DEVAS": "Hindu deities", "DIENE": "TIER3", "DWELT": "Lived",
    "EARED": "Listened, archaically", "EPSOM": "Bath salt namesake",
    "ERROL": "Actor Flynn", "EVITA": "Andrew Lloyd Webber musical",
    "FACIE": "Prima ___", "FERRI": "TIER3", "FIBRO": "TIER3",
    "FRIGS": "TIER3", "GEESE": "Honking flock", "GERRY": "Adams of Sinn Fein",
    "GLUED": "Stuck fast", "GNAWN": "TIER3", "GOTHA": "TIER3",
    "GROOT": "Guardian of the Galaxy tree", "HANNA": "Animator Joseph",
    "HEARD": "Listened to", "HIRAM": "Old man's name", "HONAN": "TIER3",
    "HOSEA": "Minor prophet", "HYDRO": "Water-related prefix",
    "INNIT": "Don't you agree?, in British slang",
    "INORG": "TIER3", "INTRA": "Within, in compounds",
    "JANIS": "Singer Joplin", "JANOS": "TIER3", "KARST": "Limestone terrain",
    "KHASI": "TIER3", "LAYNE": "TIER3", "LEBEN": "Life, in German",
    "LEILA": "Old-fashioned name", "LELIA": "TIER3", "LICET": "TIER3",
    "LIEUT": "Officer, briefly", "LIMES": "Margarita garnishes",
    "LINTY": "Like a sweater after laundering", "LIVIA": "Empress of Rome",
    "LORAN": "Old navigation system", "LOTTA": "Plenty, slangily",
    "LUKAS": "Director Lukas Moodysson", "MARCO": "Polo who explored",
    "MASSA": "TIER3", "MATTI": "TIER3", "MCGEE": "Travis ___ of Crockett",
    "MENDE": "TIER3", "MESSE": "TIER3", "MINER": "Hard-hat worker",
    "MISES": "TIER3", "MONGO": "Blazing Saddles big guy", "NIELS": "Physicist Bohr",
    "NOYCE": "Intel co-founder", "OCULI": "Eyes, anatomically",
    "OILER": "Edmonton hockey player", "OOHED": "Expressed amazement",
    "ORTHO": "Lawn-care brand", "OSAKA": "Tennis star Naomi",
    "OSMAN": "Ottoman dynasty founder", "PAMIR": "Central Asian mountain range",
    "PARMA": "Italian ham city", "PARTI": "TIER3", "PENCE": "Former VP Mike",
    "PEROT": "1992 candidate Ross", "PESTE": "Pest, in French",
    "PRIUS": "Toyota hybrid", "RACED": "Sprinted",
    "RAOUL": "Wallenberg of WWII fame", "RECTI": "Abdominal muscles, plural",
    "REDDY": "Singer Helen", "RELIT": "Sparked again",
    "RENDU": "TIER3", "RENEE": "Actress Zellweger", "RERAN": "Showed again",
    "ROSIE": "Riveter of WWII posters", "SADIE": "Hawkins of Li'l Abner",
    "SALTS": "Smelling ___", "SALUS": "TIER3",
    "SEIKO": "Watch brand", "SEPTA": "Membranes, plural", "SHAHI": "TIER3",
    "SHANA": "Tova (Hebrew greeting)", "SHURE": "Microphone brand",
    "SILAS": "Eliot's silent weaver", "SLIER": "Craftier",
    "SNUCK": "Slipped past", "SOLED": "Fitted with footwear bottoms",
    "SONIA": "Sotomayor of SCOTUS", "SONYA": "TIER3", "SOTER": "TIER3",
    "SPUTA": "Saliva samples", "STYLI": "Pen tips, plural",
    "SUPPL": "TIER3", "SUSAN": "Lazy ___", "TAIGA": "Boreal forest",
    "TELOS": "Aim or purpose, in philosophy", "TESTS": "Quizzes",
    "TORSI": "Sculpture trunks, plural", "TOVAR": "TIER3",
    "TREAS": "Cabinet dept., briefly", "UINTA": "Utah mountain range",
    "VOLTE": "Sudden U-turn, fencing term", "WOMEN": "Feminist's focus",
    "YATES": "British Prime Minister mentioned in joke",

    # ---------- length 6 ----------
    "ADAMIC": "Like the first man", "ADOLFO": "Designer to Nancy Reagan",
    "AGASSI": "Tennis great Andre", "AGATHA": "Mystery writer Christie",
    "AIRMEN": "USAF members", "ALCUIN": "Anglo-Saxon scholar",
    "ALEXIS": "Author de Tocqueville", "ALUMNI": "School grads",
    "ANCONA": "Italian port", "ANGLOS": "British-descended folks",
    "ARAMID": "Strong synthetic fiber", "BHUTTO": "Late Pakistan PM Benazir",
    "BLUING": "Laundry whitener", "BURSTS": "Sudden outbreaks",
    "CALLAO": "Peru's main port", "CATLIN": "Painter of the American West",
    "COLEYS": "TIER3", "CURLED": "Coiled up", "DABBED": "Touched lightly",
    "DARERS": "Risk-takers", "DARREN": "Sitcom husband Stephens",
    "DELANO": "FDR's middle name", "DELIAN": "Of an Aegean island",
    "DOPANT": "Semiconductor additive", "DRIEST": "Most arid",
    "DWIGHT": "President Eisenhower", "ELLICE": "TIER3",
    "FAROUK": "Last king of Egypt", "GIRLIE": "Frilly, in slang",
    "GOTCHA": "Trick question", "HAGGAI": "Minor prophet",
    "HAIRED": "Having tresses", "HAROLD": "TV's '___ and Maude'",
    "HENRIK": "Ibsen, the playwright", "INGRID": "Bergman of Casablanca",
    "JESSIE": "Cowgirl in Toy Story 2", "JULIET": "Romeo's love",
    "KRANTZ": "Romance novelist Judith", "KRONOS": "Greek titan",
    "LARVAE": "Caterpillar stage", "LIEDER": "German art songs",
    "LIEFER": "TIER3", "LORENA": "TIER3", "MARCIE": "Peanuts character",
    "MARCOS": "Late Philippine dictator", "MCADAM": "Asphalt-paving pioneer",
    "MILDER": "Less harsh", "MIRIAM": "Aaron's biblical sister",
    "MULDER": "X-Files agent", "NICOLE": "Kidman of film",
    "OCLOCK": "Hour marker", "OOHING": "Expressing wonder",
    "PARDEE": "TIER3", "PHALLI": "TIER3", "PLEBBY": "Common, in British slang",
    "PNEUMA": "Vital breath, in Greek philosophy", "POIRET": "TIER3",
    "POSADA": "Mexican Christmas tradition", "REHUNG": "Put back up on the wall",
    "RELAID": "Set out again", "RELIST": "Put back on the market",
    "RESOLD": "Sold again", "REWOVE": "Threaded again",
    "RIALTO": "Movie theater name", "ROEMER": "TIER3",
    "ROLAND": "Songhai empire conqueror", "RUBATI": "Music tempo variations",
    "SAINTE": "Holy, in French", "SCHULE": "School, in German",
    "SEAMUS": "Irish poet Heaney", "SENECA": "Stoic philosopher",
    "SHAUNA": "TIER3", "SHIEST": "Most timid", "SOLDAT": "Soldier, in German",
    "SOMERS": "Late actress Suzanne", "STANDI": "TIER3",
    "STENOS": "Court reporters, briefly", "SUTTON": "TIER3",
    "TARTED": "Dressed up, briefly", "TATARS": "Mongol descendants",
    "TENTED": "Camped", "TEXACO": "Oil company name",
    "TIERED": "Layered like a cake", "TINPOT": "Small-time, as a dictator",
    "TOTTED": "Added up", "TUDORS": "Henry VIII's family",
    "UMIAKS": "Arctic boats", "WEEDED": "Tended the garden",

    # ---------- length 7 ----------
    "ABETTED": "Aided in a crime", "ADDENDA": "Supplements, plural",
    "ADELINE": "Sweet ___ of song", "AIRBAGS": "Crash safety devices",
    "AIRIEST": "Most ventilated", "ALISTER": "TIER3",
    "ALVEOLI": "Tiny lung sacs", "ANYTIME": "Whenever you'd like",
    "AVERRED": "Stated firmly", "AWARDEE": "Prize recipient",
    "BEEFIER": "More muscular", "BETAKES": "Goes (oneself)",
    "BOATMEN": "Ferry operators", "CAGIEST": "Most evasive",
    "CHOCTAW": "Southeastern U.S. tribe", "CIRCLED": "Drew a ring around",
    "CONCHIE": "Conscientious objector, briefly", "CONTRIB": "TIER3",
    "CRIMEAN": "Of a Black Sea peninsula", "DARRELL": "TIER3",
    "DATESET": "TIER3", "DIMERIC": "Two-molecule, as a polymer",
    "EARNING": "Drawing a salary", "EASIEST": "Most effortless",
    "ENCOMIA": "Words of praise, plural", "FIERIER": "More inflamed",
    "FRANCIS": "Pope Bergoglio", "FUMIEST": "Smelliest",
    "GLIBBER": "Smoother-talking", "GRUNION": "California beach fish",
    "HEADMEN": "Tribal chiefs", "HILLIER": "More undulating",
    "HOMERED": "Knocked it out of the park", "IMAMATE": "Islamic leadership office",
    "INCONNU": "TIER3", "LEGROOM": "Plane seat amenity",
    "LOITERS": "Hangs around", "MIRANDA": "Hamilton creator Lin-Manuel",
    "MUSKEGS": "Northern bogs", "ONBOARD": "Aboard ship",
    "OPCODES": "Machine-instruction parts", "OUTDONE": "Surpassed",
    "OVERSAW": "Supervised", "PAROLED": "Released conditionally",
    "PATINAE": "Bronze sheens, plural", "PERINEA": "Body regions, plural",
    "PETTIER": "More small-minded", "PONYING": "___ up (paying)",
    "PREPPIE": "Ivy League type", "PRIMULA": "Garden primrose",
    "PRIVIER": "More privately informed", "RAPALLO": "TIER3",
    "RATTANS": "Wicker reeds", "REDDEST": "Most crimson",
    "REEDITS": "Goes over the manuscript again", "REHIRES": "Brings back to work",
    "ROSALIE": "Old-fashioned name", "SCHIZOS": "TIER3",
    "SECONDE": "Fencing position", "SHASTRI": "Indian PM Lal Bahadur",
    "SIENESE": "Of an Italian Tuscan city", "SIERRAS": "Mountain ranges",
    "SIGNORI": "Italian gentlemen", "SMARTED": "Stung",
    "SNAPPED": "Took a quick photo", "STEELED": "Hardened",
    "TABITHA": "Bewitched daughter", "TAUNTON": "TIER3",
    "TEAZLES": "TIER3", "TELEXED": "Sent over wire, in old offices",
    "TOKELAU": "New Zealand territory", "TRIANON": "TIER3",
    "UNEATEN": "Left on the plate", "UPTEMPO": "Lively, musically",
    "VALOREM": "Ad ___ (tax type)", "VICOMTE": "French aristocrat",
    "WILLIAM": "Prince of Wales", "ZOUAVES": "French light infantry",

    # ---------- length 8 ----------
    "ALEWIVES": "Small herring relatives", "ALPHONSO": "Mango variety",
    "AMRITSAR": "Punjabi holy city", "ANGRIEST": "Most furious",
    "ANTENNAE": "Insect feelers, plural", "BEERIEST": "Most pub-like",
    "CAESURAE": "Verse pauses, plural", "CARTOONS": "Saturday morning fare",
    "CATALPAS": "Bean trees", "CHRISSIE": "Pretenders frontwoman Hynde",
    "COLLEGIA": "Roman associations, plural", "CORDELIA": "Lear's youngest",
    "DIERESES": "Umlaut marks, plural", "DONENESS": "Steak-cooking degree",
    "DRESSIER": "More formal", "EROSIONS": "Wearings-away",
    "FLAREUPS": "Sudden outbreaks", "FORMULAE": "Math statements, plural",
    "GESTAPOS": "Secret police forces", "GORINESS": "Bloody quality",
    "HOARIEST": "Most ancient", "HUNTSMEN": "Hunters",
    "INTERNED": "Held in custody", "KIELBASA": "Polish sausage",
    "LUCRETIA": "Suffragist Mott", "MEATHEAD": "Lunkhead",
    "MISDEALT": "Distributed cards wrongly", "NIFTIEST": "Coolest",
    "NONISSUE": "Unimportant matter", "OPERANDI": "Modus ___",
    "ORESTEIA": "Aeschylus trilogy", "OROGENIC": "Mountain-forming",
    "PAPILLAE": "Bumps on the tongue", "PEACHIER": "Just dandy, more so",
    "PROSPERO": "Tempest sorcerer", "PROTESTS": "Marches against",
    "RAINIEST": "Most precipitous", "RESTYLES": "Updates the hair",
    "RIVERINE": "Of a flowing waterway", "SASSIEST": "Cheekiest",
    "SCAPULAE": "Shoulder blades, plural", "SHLEPPED": "Lugged around",
    "STRESSED": "Wound up", "SUBPRIME": "Risky, as a mortgage",
    "SULKIEST": "Moodiest", "TERRARIA": "Glass-enclosed gardens",
    "TIMBERED": "Wooded", "TREELINE": "Forest's upper edge",

    # ---------- length 9 ----------
    "ANTIPASTI": "Italian appetizers, plural", "BANQUETED": "Feasted",
    "CATALOGED": "Listed item by item", "CEASEFIRE": "Truce in hostilities",
    "CHERUBIMS": "Heavenly beings, plural", "CORRECTOR": "Teacher with a red pen",
    "DAYDREAMT": "Lost in thought", "ELDERCARE": "Senior services",
    "FEATHERED": "Like a bird's coat", "FILMSTRIP": "Old classroom medium",
    "INTRAORAL": "Inside the mouth", "MADRASSAS": "Islamic schools",
    "OUTBOASTS": "Brags better than", "OUTGUNNED": "Outmatched in firepower",
    "OVERGRAZE": "Strip the pasture", "OVERSLEPT": "Snoozed too long",
    "RELABELED": "Renamed the file", "RELIGIOSE": "Excessively pious",
    "RINGTONES": "Phone alert sounds", "SESTERCES": "Roman coins",
    "SHLEPPING": "Hauling around", "SOLIDNESS": "Firmness",
    "SPOOKIEST": "Most ghostly", "TRICHINAE": "Parasitic worms",

    # ---------- length 10 ----------
    "ALDERWOMAN": "Female city council member", "CABRIOLETS": "Open carriages",
    "CORDILLERA": "Mountain chain", "MINISTERED": "Tended to needs",
    "NONCONTACT": "Not touching", "PHANTASIED": "Imagined wildly",
    "SENTENCING": "Court ruling phase", "TRAVESTIED": "Made a mockery of",

    # ---------- length 11 ----------
    "BACKSLASHES": "Some keyboard keys", "RECYCLABLES": "Curbside bin contents",

    # ---------- length 13 ----------
    "NECROPHILIACS": "TIER3", "NEUROVASCULAR": "Of nerves and vessels",
    "UNWORLDLINESS": "Naivete",

    # ---------- length 14 ----------
    "ANTHROPOLOGIST": "Margaret Mead, e.g.",
    "COUNTERCLAIMED": "Filed an opposing demand",
    "MESDEMOISELLES": "French young ladies, plural",

    # ---------- length 15 ----------
    "BRACHIORADIALIS": "Forearm muscle",
    "CANNIBALIZATION": "Stripping for parts",
    "COUNTERCULTURAL": "Anti-establishment",
    "PREADOLESCENCES": "Tween years, plural",
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
            "\n# 15x15 sweep round-2 gap triage\n"
            + "\n".join(sorted(new_tier3)) + "\n"
        )
        with open(DATA / "tier3_force.txt", "a") as f:
            f.write(block)
    print(f"tier3_force.txt: added {len(new_tier3)}")


if __name__ == "__main__":
    main()
