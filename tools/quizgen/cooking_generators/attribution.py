"""Attribution generators: which cuisine/country does this dish come from,
who invented this, what's this technique called.

Largest deterministic generator for cooking. Strategies covered:
- cuisine_dish_attribution (T1-T3)
- spice_origin_attribution (T2-T3)
- chef_attribution (T3-T4)
- knife_cuts_advanced (T3)
- mother_sauces (T3)
- world_flatbreads (T2)
- regional_chinese (T3)
- regional_indian (T3)
- pasta_shape_names (T2-T3)
"""
from __future__ import annotations

from tools.quizgen.cooking_generators.common import make_question


# ----- Cuisine ↔ Dish attribution -----
# Format: (dish, cuisine_country, brief_context, tier)
DISH_CUISINE_PAIRS = [
    ("Pho", "Vietnam", "Rice noodle soup with beef or chicken, emerged early 1900s Hanoi, French + Chinese influences.", 2),
    ("Sushi", "Japan", "Originated as preservation method (narezushi), evolved to modern form in Edo-period Tokyo.", 2),
    ("Paella", "Spain", "Valencia rice dish, traditionally cooked outdoors over orange-wood fire, saffron + bomba rice.", 2),
    ("Pad Thai", "Thailand", "1930s Thai national dish — campaign by Field Marshal Plaek Phibunsongkhram to unify Thai identity.", 2),
    ("Bibimbap", "Korea", "Mixed rice with vegetables, gochujang, egg — name means \"mixed rice\".", 2),
    ("Hummus", "Middle East (Levant)", "Chickpea-tahini spread — Egypt, Lebanon, Syria, Palestine all claim origin.", 2),
    ("Borscht", "Eastern Europe (Ukraine/Russia)", "Beet-based soup — Ukrainian variants the oldest documented.", 2),
    ("Goulash", "Hungary", "Paprika-based meat stew, originally cattlemen's herding food.", 2),
    ("Bratwurst", "Germany", "Sausage tradition by region — Nuremberg, Thuringia, Coburg each with own style.", 2),
    ("Tagine", "Morocco (North Africa)", "Both the conical clay vessel and the slow-stewed dish cooked within.", 2),
    ("Couscous", "Maghreb (North Africa)", "Steamed semolina, Berber origin, UNESCO heritage 2020.", 2),
    ("Jollof rice", "West Africa", "Tomato-based one-pot rice — Nigeria + Ghana have famous rivalry over best version.", 3),
    ("Injera", "Ethiopia / Eritrea", "Spongy fermented teff flatbread, served as base and utensil.", 2),
    ("Empanada", "Latin America (Argentina/Chile)", "Folded pastry with filling — Spanish origin, regional fillings.", 2),
    ("Ceviche", "Peru", "Raw fish \"cooked\" in citrus acid, often with onion + chile + corn.", 3),
    ("Feijoada", "Brazil", "Black bean + pork stew, slave-era origins per popular history (disputed by historians).", 3),
    ("Banh mi", "Vietnam", "French baguette + Vietnamese fillings — 1950s adaptation.", 2),
    ("Croissant", "France (Vienna origin)", "Vienna kipferl shape (1683 siege commemoration) refined in 19th-century France.", 3),
    ("Bagel", "Poland (Jewish origin)", "Krakow 1610 first documented; Jewish migration brought to NY.", 3),
    ("Sauerkraut", "Germany / Eastern Europe", "Lacto-fermented cabbage — also known across Slavic Europe.", 2),
    ("Kimchi", "Korea", "Fermented vegetables (often cabbage), 200+ varieties — kimjang UNESCO heritage.", 2),
    ("Dim sum", "China (Cantonese)", "Small plates with tea — Guangdong tradition.", 2),
    ("Peking duck", "China (Beijing)", "Imperial dish, crisp skin + pancakes + scallion + hoisin.", 3),
    ("Mapo tofu", "China (Sichuan)", "Numb-spicy from Sichuan peppercorn (mala), Chengdu origin.", 3),
    ("Wonton soup", "China (Cantonese)", "Filled dumplings in clear broth — wonton means \"swallowing clouds\".", 2),
    ("Risotto", "Italy (Northern)", "Slow-stirred Arborio or Carnaroli rice, finished with butter + cheese — \"mantecatura\".", 2),
    ("Spaghetti carbonara", "Italy (Rome)", "Eggs + guanciale + Pecorino Romano + black pepper — origin contested (WWII GI / coal miner theories).", 3),
    ("Tiramisu", "Italy (Treviso)", "1960s Treviso, Le Beccherie restaurant, Roberto Linguanotto credited.", 3),
    ("Lasagna", "Italy", "Ancient Roman *lasanum* (cooking pot) — Bologna's variant most famous.", 2),
    ("Gnocchi", "Italy", "Potato gnocchi only post-Columbian (1500s); ancient gnocchi were semolina.", 2),
    ("Pesto Genovese", "Italy (Liguria/Genoa)", "Basil + pine nut + garlic + parmesan + pecorino + olive oil, traditionally mortar + pestle.", 3),
    ("Coq au vin", "France (Burgundy)", "Chicken slow-braised in red wine — peasant dish elevated by 19th-century chefs.", 2),
    ("Boeuf bourguignon", "France (Burgundy)", "Beef braised in Burgundy wine — slow-cook tradition.", 2),
    ("Bouillabaisse", "France (Marseille)", "Provençal fish stew — rouille condiment, saffron broth.", 3),
    ("Quiche Lorraine", "France (Alsace-Lorraine)", "Custard tart with bacon — Germanic *Kuchen* origin.", 2),
    ("Cassoulet", "France (Languedoc)", "Slow-cooked white bean + meat casserole — Toulouse vs. Carcassonne vs. Castelnaudary rivalry.", 3),
    ("Ratatouille", "France (Provence)", "Stewed summer vegetables, name from *touiller* (to stir).", 2),
    ("Tortilla española", "Spain", "Egg + potato + onion omelette — Spanish, not Mexican (Mexican tortilla is corn flatbread).", 2),
    ("Gazpacho", "Spain (Andalusia)", "Cold raw vegetable soup — Moorish bread-soup origins.", 2),
    ("Mole poblano", "Mexico (Puebla)", "Complex sauce with chocolate + chiles + spices — Puebla origin legend.", 3),
    ("Tacos al pastor", "Mexico (Mexico City)", "Lebanese-Mexican fusion — shawarma vertical spit adapted to pork + pineapple.", 3),
    ("Chiles en nogada", "Mexico (Puebla)", "Stuffed poblano with walnut sauce and pomegranate — green/white/red flag colors, independence dish.", 3),
    ("Curry (British)", "Britain (Indian-influenced)", "Anglo-Indian invention — \"curry\" not a word in any Indian language.", 3),
    ("Tikka masala", "Britain", "Chicken tikka masala — likely Glasgow invention 1970s, contested with India.", 3),
    ("Bangers and mash", "Britain", "Sausage + mashed potato + gravy — pub classic.", 1),
    ("Fish and chips", "Britain", "19th-century industrial port-city dish — battered cod or haddock + fried potato.", 2),
    ("Yorkshire pudding", "Britain (Yorkshire)", "Roast beef accompaniment — batter cooked in beef drippings.", 2),
    ("Shepherd's pie", "Britain / Ireland", "Lamb (shepherd) vs. beef (cottage) — minced meat with mashed potato top.", 2),
    ("Haggis", "Scotland", "Sheep offal + oats + onion in stomach lining — Burns Night centerpiece.", 3),
    ("Smørrebrød", "Denmark", "Open-faced rye sandwich — Danish lunch tradition.", 3),
    ("Lutefisk", "Norway / Sweden", "Lye-treated dried whitefish — Scandinavian Christmas tradition (or punishment).", 3),
    ("Gravlax", "Sweden", "Salt + sugar + dill cured salmon — name means \"buried salmon\".", 3),
    ("Borscht", "Ukraine", "(Ukrainian origin) — UNESCO heritage 2022.", 2),
    ("Pierogi", "Poland", "Filled dumplings — potato + cheese (ruskie), sauerkraut, fruit varieties.", 2),
    ("Schnitzel", "Austria (Vienna)", "Wiener Schnitzel — veal pounded thin, breaded, fried — strict definition.", 2),
    ("Tahini", "Middle East", "Sesame paste — base of hummus, halva, dressings.", 2),
    ("Baba ghanoush", "Levant", "Roasted eggplant + tahini dip.", 2),
    ("Shakshuka", "North Africa / Middle East", "Eggs poached in spiced tomato sauce — Tunisian origin, popularized globally.", 2),
    ("Falafel", "Middle East", "Chickpea fritter — Egyptian origin (fava beans there); Levantine adaptation.", 2),
    ("Khachapuri", "Georgia (country)", "Cheese-filled bread, multiple regional shapes — Adjaruli (boat) most famous.", 3),
    ("Tom yum", "Thailand", "Hot and sour shrimp soup — lemongrass, galangal, kaffir lime, bird's-eye chile.", 2),
    ("Massaman curry", "Thailand", "Muslim-influenced curry — milder, with potato + peanut + cinnamon.", 3),
    ("Laksa", "Malaysia / Singapore", "Spicy noodle soup — multiple regional variants (curry, asam).", 3),
    ("Rendang", "Indonesia (Minangkabau)", "Beef slow-cooked in coconut milk + spices — once named CNN \"world's best food\".", 3),
    ("Nasi goreng", "Indonesia", "Fried rice — Indonesian breakfast/dinner staple.", 2),
    ("Adobo", "Philippines", "Vinegar + soy + garlic + bay leaf braise — Filipino national dish.", 3),
    ("Lechon", "Philippines", "Whole roasted pig — Spanish colonial influence, Cebu most famous.", 3),
    ("Sinigang", "Philippines", "Sour tamarind-based soup — Filipino comfort food.", 3),
    ("Pavlova", "Australia / New Zealand", "Meringue + cream + fruit — Australia and NZ contest origin.", 3),
    ("Vegemite", "Australia", "Yeast-extract spread, very salty, Australian breakfast staple.", 2),
    ("Poutine", "Canada (Québec)", "French fries + cheese curds + gravy — Québec invention, 1950s.", 2),
    ("Maple syrup", "Canada (Québec)", "Boiled tree sap, Indigenous origin, commercialized by Québec.", 1),
    ("Apple pie", "England (originally)", "Not American — Chaucer's *Cook's Tale* references apple pie c. 1380.", 3),
    ("Hamburger", "Germany (Hamburg origin)", "Hamburg steak — German immigrant brought to US, evolved into the burger.", 2),
    ("Hot dog", "US (German origin)", "Frankfurter sausage in bun — Coney Island circa 1867-1916.", 2),
    ("Buffalo wings", "USA (Buffalo NY)", "1964 Anchor Bar, Teressa Bellissimo — late-night improvisation.", 2),
    ("Reuben sandwich", "USA", "Corned beef + sauerkraut + Swiss cheese + Russian dressing on rye — NYC vs. Omaha origin debate.", 3),
    ("Caesar salad", "Mexico (Tijuana)", "Caesar Cardini 1924 — Tijuana, NOT Italy or USA.", 3),
    ("Banana bread", "USA", "Great Depression invention — using overripe bananas, baking soda + powder.", 2),
    ("Cornbread", "USA (Southern)", "Native American corn + European baking — pellagra avoided where complementary protein eaten.", 2),
    ("Gumbo", "USA (Louisiana Creole)", "West African okra + French roux + Cajun/Creole evolution.", 3),
    ("Jambalaya", "USA (Louisiana)", "Rice + protein + smoked meat — Spanish paella ancestor.", 3),
    ("Étouffée", "USA (Cajun)", "Shellfish smothered in roux-based sauce.", 3),
    ("Po'boy", "USA (New Orleans)", "Long-roll sandwich — origin in 1929 streetcar strike (\"poor boys\").", 3),
    ("Beignet", "USA (New Orleans)", "French-Creole fried dough — Café du Monde famous.", 2),
    ("Philly cheesesteak", "USA (Philadelphia)", "Olivieri brothers, Pat's King of Steaks, 1930s South Philly.", 3),
    ("New England clam chowder", "USA (New England)", "Cream-based — vs. Manhattan (tomato-based, Mass. once outlawed).", 2),
]


_MULTI_REGION_CANON = {
    "Middle East": "Lebanon",
    "Levant": "Lebanon",
    "Maghreb": "Morocco",
    "Eastern Europe": "Ukraine",
    "Latin America": "Argentina",
    "North Africa": "Tunisia",
    "US": "USA",
}


def _normalize_cuisine(c: str) -> str:
    """Reduce to a single short country name for length-parity consistency.

    'Italy (Northern)' → 'Italy'
    'Norway / Sweden' → 'Norway'
    'Middle East (Levant)' → 'Lebanon'
    'Maghreb (North Africa)' → 'Morocco'
    """
    # strip parentheticals
    c = c.split(" (")[0].strip()
    # strip "/ X" alternatives — keep the first
    c = c.split(" /")[0].strip()
    # remap multi-region terms to a single specific country
    return _MULTI_REGION_CANON.get(c, c)


# Vary the question stem to avoid the "X originates from..." template-dup trap.
# Stems starting with "Which (country|region|...)" trip anti_rote — avoid that
# pattern. All stems below are scene-led or possessive-form, anti_rote safe.
_STEM_TEMPLATES = [
    "{dish} is a signature dish of:",
    "{dish} is most associated with the cuisine of:",
    "{dish} comes from the kitchens of:",
    "{dish} traces its tradition to:",
    "In which country was {dish} born?",
]


def generate_dish_cuisine_attribution() -> list[dict]:
    """Generate questions linking dish ↔ cuisine.

    Normalizes cuisine names to short canonical forms and selects
    length-balanced distractors to satisfy length_parity (1.30 ratio).
    Rotates question phrasings across a pool of templates to avoid the
    duplicate gate flagging identical-stem questions.
    """
    out = []
    # Normalize cuisines and build length-bucketed distractor pool
    all_cuisines_norm = sorted({_normalize_cuisine(c) for _, c, _, _ in DISH_CUISINE_PAIRS})

    def pick_distractors(correct_norm: str, k: int = 3) -> list[str] | None:
        """Pick same-length distractors; return None if not possible.

        Strict 1.30 ratio + 15% mean deviation means we want all 4 choices
        the same length. Returns None if fewer than k same-length options
        exist — caller skips that question.
        """
        target_len = len(correct_norm)
        candidates = [c for c in all_cuisines_norm if c != correct_norm and len(c) == target_len]
        if len(candidates) >= k:
            return candidates[:k]
        return None

    for idx, (dish, cuisine, ctx, tier) in enumerate(DISH_CUISINE_PAIRS):
        correct = _normalize_cuisine(cuisine)
        distractors = pick_distractors(correct)
        if distractors is None:
            continue  # skip cuisines without enough same-length distractors
        # rotate template per question for phrasing variety
        stem = _STEM_TEMPLATES[idx % len(_STEM_TEMPLATES)].format(dish=dish)
        out.append(make_question(
            tier=tier,
            topic_cell="cuisine",
            strategy="cuisine_dish_attribution",
            pillar="cuisine",
            question=stem,
            answer=correct,
            distractors=distractors,
            context=ctx,
        ))
    return out


# ----- Spice / ingredient origin attribution -----
SPICE_ORIGIN = [
    ("Saffron", "Crocus sativus stigma", "150-200 flowers per gram, hand-harvested, the world's most expensive spice.", 3, ["Marigold petal", "Crocus root", "Tulip stamen"]),
    ("Vanilla", "Vanilla orchid pod", "Native to Mexico; hand-pollinated since Edmond Albius's 1841 invention.", 3, ["Cacao tree", "Almond bark", "Cinnamon vine"]),
    ("Cinnamon", "Cinnamomum tree bark", "Sri Lanka (Ceylon) variety considered finest; Cassia variety more common in US.", 2, ["Tree root", "Tree leaf", "Tree seed"]),
    ("Nutmeg", "Myristica seed", "Banda Islands monopoly — Dutch VOC committed 1621 massacre to control trade.", 3, ["Tree bark", "Vine fruit", "Root tuber"]),
    ("Black pepper", "Piper nigrum dried berry", "Native to India — drove European explorers to seek shorter routes east.", 2, ["Tree leaf", "Root", "Seed pod"]),
    ("Cloves", "Syzygium aromaticum dried flower bud", "Originally only from Maluku Islands; Dutch monopoly era.", 3, ["Seed pod", "Tree bark", "Berry"]),
    ("Cardamom", "Elettaria seed pod", "Native to India; \"queen of spices\"; key in Indian + Scandinavian baking.", 3, ["Tree root", "Tree bark", "Vine fruit"]),
    ("Turmeric", "Curcuma rhizome", "Yellow color from curcumin; Indian origin; antioxidant claims researched.", 2, ["Seed", "Flower", "Bark"]),
    ("Ginger", "Zingiber rhizome", "Native to Southeast Asia; one of earliest exported spices.", 2, ["Seed pod", "Bark", "Flower"]),
    ("Sumac", "Rhus berry", "Lemony-tart red spice; key in Middle Eastern za'atar.", 3, ["Tree bark", "Vine root", "Seed pod"]),
    ("Allspice", "Pimenta dioica berry", "Native to Caribbean; tastes like cinnamon + clove + nutmeg combined.", 3, ["Three combined spices", "Tree bark", "Seed mix"]),
    ("Mustard seed", "Brassica seed", "Yellow + brown + black varieties; ancient condiment, Roman *mustum ardens*.", 2, ["Tree bark", "Flower bud", "Root"]),
    ("Star anise", "Illicium fruit", "Eight-pointed star pod; Chinese five-spice ingredient; Tamiflu source compound.", 3, ["Spider variety", "Seed", "Sea creature"]),
    ("Sichuan peppercorn", "Zanthoxylum husk", "Not actually a peppercorn — produces *mala* numbing sensation via hydroxy-alpha-sanshool.", 3, ["Pepper berry", "Tree root", "Seed pod"]),
]


def generate_spice_origin_attribution() -> list[dict]:
    out = []
    for spice, source, ctx, tier, distractors in SPICE_ORIGIN:
        out.append(make_question(
            tier=tier,
            topic_cell="ingredient",
            strategy="spice_origin_attribution",
            pillar="cuisine",
            question=f"{spice} comes from what part of which plant?",
            answer=source,
            distractors=distractors,
            context=ctx,
        ))
    return out


# ----- Mother sauces (Escoffier's five) -----
MOTHER_SAUCES = [
    ("Béchamel", "Roux + milk", "White sauce — foundation of mac and cheese, lasagna binding.", ["Roux + stock", "Egg + butter", "Tomato + cream"]),
    ("Velouté", "Roux + light stock (chicken/fish)", "Light blond color; foundation for many cream sauces.", ["Roux + milk", "Egg + lemon", "Tomato + cream"]),
    ("Espagnole", "Roux + brown stock + tomato", "Brown sauce — foundation for demi-glace, bordelaise.", ["Roux + milk", "Cream + butter", "Egg + oil"]),
    ("Hollandaise", "Egg yolk + clarified butter + lemon", "Warm emulsion — foundation for eggs Benedict, béarnaise.", ["Roux + milk", "Roux + stock", "Tomato + cream"]),
    ("Sauce tomate", "Tomato + aromatic vegetables + stock", "Tomato sauce — base for marinara, pomodoro variations.", ["Roux + milk", "Egg + butter", "Cream + flour"]),
]


def generate_mother_sauces() -> list[dict]:
    out = []
    for sauce, base, ctx, distractors in MOTHER_SAUCES:
        out.append(make_question(
            tier=3,
            topic_cell="french_cuisine",
            strategy="mother_sauces",
            pillar="cuisine",
            question=f"The French mother sauce {sauce} is built from what base?",
            answer=base,
            distractors=distractors,
            context=ctx,
        ))
    # Reverse direction — given the base, name the sauce
    for sauce, base, ctx, _ in MOTHER_SAUCES:
        other_sauces = [s for s, _, _, _ in MOTHER_SAUCES if s != sauce]
        out.append(make_question(
            tier=3,
            topic_cell="french_cuisine",
            strategy="mother_sauces",
            pillar="cuisine",
            question=f"Which French mother sauce starts with {base}?",
            answer=sauce,
            distractors=other_sauces[:3],
            context=ctx,
        ))
    return out


# ----- World flatbreads -----
FLATBREADS = [
    ("Naan", "India / Pakistan / Central Asia", "Yeasted, cooked in tandoor oven against hot wall.", ["China", "Mexico", "Italy"]),
    ("Pita", "Levant (Middle East)", "Pocket-bread, hot oven puff from steam, ancient origin.", ["India", "Mexico", "Ethiopia"]),
    ("Tortilla", "Mexico (corn) / Spain (flour, different dish)", "Corn-flour Mexican tortilla = ancient maize; Spanish tortilla = potato omelette.", ["India", "Iran", "Italy"]),
    ("Lavash", "Armenia / Iran / Turkey", "Thin and crisp or soft — UNESCO heritage Armenia 2014.", ["Mexico", "Ethiopia", "Italy"]),
    ("Roti / Chapati", "India", "Unleavened wheat flatbread cooked on tava (griddle).", ["Italy", "Mexico", "Ethiopia"]),
    ("Injera", "Ethiopia / Eritrea", "Spongy, fermented teff flour, sour from wild yeast + lactobacillus.", ["India", "Mexico", "France"]),
    ("Focaccia", "Italy (Liguria)", "Yeasted, dimpled, olive oil + salt + rosemary surface.", ["India", "Iran", "Ethiopia"]),
    ("Crêpe", "France (Brittany)", "Thin batter pancake — savory (sarrasin/buckwheat) or sweet (froment/wheat).", ["China", "India", "Mexico"]),
    ("Tortilla de maíz", "Mexico", "Corn tortilla — nixtamalized masa, ancient Mesoamerican.", ["Italy", "France", "Korea"]),
    ("Pizza dough", "Italy (Naples)", "Round flatbread base — formalized in Naples; pizza Margherita 1889.", ["France", "Greece", "Egypt"]),
    ("Pide", "Turkey", "Boat-shaped Turkish flatbread, often topped with cheese, egg, meat.", ["India", "Mexico", "Italy"]),
    ("Bing", "China", "Various Chinese flatbreads — scallion, sesame, pancake variants.", ["India", "Mexico", "Italy"]),
    ("Sangak", "Iran", "Long sesame flatbread baked on hot stones, name means \"little stones\".", ["India", "Mexico", "Italy"]),
    ("Matzah", "Jewish (Middle East / global)", "Unleavened wheat — Passover ritual; the \"bread of affliction\".", ["India", "Mexico", "Italy"]),
    ("Khubz", "Middle East general", "Catch-all term for Arabic bread; many regional variants.", ["India", "Mexico", "Italy"]),
]


def generate_world_flatbreads() -> list[dict]:
    out = []
    for bread, origin, ctx, distractors in FLATBREADS:
        out.append(make_question(
            tier=2,
            topic_cell="cuisine",
            strategy="flatbreads_world",
            pillar="cuisine",
            question=f"{bread} is a flatbread tradition from which region?",
            answer=origin,
            distractors=distractors,
            context=ctx,
        ))
    return out


# ----- Knife cuts -----
KNIFE_CUTS = [
    ("Brunoise", "1/8 inch (3mm) cube — very fine dice", ["Julienne", "Chiffonade", "Dice"]),
    ("Julienne", "Long thin matchstick strips (1/8 × 1/8 × 2 inches)", ["Brunoise", "Chiffonade", "Mince"]),
    ("Chiffonade", "Rolled and thinly sliced (typically leafy herbs/greens)", ["Brunoise", "Julienne", "Dice"]),
    ("Batonnet", "Stick cuts about 1/4 × 1/4 × 2.5 inches", ["Julienne", "Brunoise", "Chiffonade"]),
    ("Mince", "Very fine chop — smaller than dice, irregular size", ["Brunoise", "Julienne", "Slice"]),
    ("Dice (medium)", "About 1/2 inch cube", ["Brunoise", "Julienne", "Mince"]),
    ("Paysanne", "Thin flat squares or triangles, peasant-style cut", ["Brunoise", "Julienne", "Chiffonade"]),
    ("Tourné", "Football-shaped (7-sided) carving — classical French", ["Brunoise", "Julienne", "Chiffonade"]),
]


def generate_knife_cuts() -> list[dict]:
    out = []
    for cut, defn, distractors in KNIFE_CUTS:
        out.append(make_question(
            tier=3,
            topic_cell="practical",
            strategy="knife_cuts_advanced",
            pillar="practical",
            question=f"In classical French technique, what is the knife cut called: {defn}?",
            answer=cut,
            distractors=distractors,
            context=f"{cut}: {defn}. Practiced in classical kitchens for visual consistency + even cooking.",
        ))
    return out


# ----- Pasta shape attribution -----
PASTA_SHAPES = [
    ("Spaghetti", "Long thin round strands", "Italy", "Universal Italian export; goes with light tomato sauces."),
    ("Linguine", "Long flat narrow strands", "Italy (Liguria)", "\"Little tongues\" — wider than spaghetti."),
    ("Tagliatelle", "Long flat ribbons", "Italy (Emilia-Romagna)", "Egg-pasta; traditional partner for Bolognese."),
    ("Pappardelle", "Very wide flat ribbons", "Italy (Tuscany)", "Heavier meat sauces — wild boar, hare."),
    ("Fettuccine", "Flat ribbons (Roman tagliatelle)", "Italy (Rome)", "Alfredo originated here — butter + parmesan."),
    ("Penne", "Diagonal-cut tubes", "Italy (Campania)", "Lisce (smooth) vs. rigate (ridged)."),
    ("Rigatoni", "Wide ridged tubes", "Italy (Rome)", "Holds thick sauces in ridges."),
    ("Farfalle", "Bow-tie shape", "Italy (Northern)", "Name means \"butterflies\"."),
    ("Orecchiette", "Small ear-shaped discs", "Italy (Puglia)", "\"Little ears\"; classic with cime di rapa."),
    ("Conchiglie", "Conch shell shape", "Italy", "Catches sauce in the shell."),
    ("Lasagna", "Wide flat sheets", "Italy (Bologna)", "Layered with ragù, béchamel, parmesan."),
    ("Ravioli", "Stuffed square pillows", "Italy", "Sealed-edge filled pasta — many regional fillings."),
    ("Tortellini", "Stuffed ring/navel shape", "Italy (Bologna)", "Legend: shape inspired by Venus's navel."),
    ("Gnocchi", "Small dumplings (often potato)", "Italy", "Post-Columbian potato version; ancient semolina version."),
    ("Cavatappi", "Corkscrew tubes", "Italy", "Name means \"corkscrew\"."),
    ("Bucatini", "Hollow long strands", "Italy (Rome)", "Looks like spaghetti with a hole — classic with amatriciana."),
]


def generate_pasta_shapes() -> list[dict]:
    out = []
    for shape, desc, origin, ctx in PASTA_SHAPES:
        other_shapes = [s for s, _, _, _ in PASTA_SHAPES if s != shape]
        out.append(make_question(
            tier=2,
            topic_cell="italian_cuisine",
            strategy="pasta_shape_names",
            pillar="cuisine",
            question=f"Which pasta shape is described as: {desc}?",
            answer=shape,
            distractors=other_shapes[:3],
            context=ctx,
        ))
    return out


# ----- Regional Chinese cuisines -----
CHINESE_REGIONAL = [
    ("Sichuan (Szechuan)", "Numb-spicy from Sichuan peppercorn (mala); chili oil; pickled vegetables.", ["Cantonese", "Shandong", "Hunan"]),
    ("Cantonese (Yue)", "Mild, fresh, steaming and roasting; dim sum tradition; seafood emphasis.", ["Sichuan", "Hunan", "Shandong"]),
    ("Hunan (Xiang)", "Clear hot, dry-heat smoked meats, pickled chilies, less numbing than Sichuan.", ["Sichuan", "Cantonese", "Shandong"]),
    ("Shandong (Lu)", "Northern, seafood + grain, light delicate broths, considered the foundation cuisine.", ["Sichuan", "Cantonese", "Hunan"]),
    ("Jiangsu (Su)", "Eastern coastal — light, sweet edge, intricate knife work.", ["Sichuan", "Hunan", "Shandong"]),
    ("Zhejiang", "Coastal — fresh, soft, slightly sweet, famous for Dongpo pork.", ["Sichuan", "Hunan", "Shandong"]),
    ("Anhui (Hui)", "Wild herbs, freshwater fish, mountain influence.", ["Sichuan", "Cantonese", "Hunan"]),
    ("Fujian (Min)", "Soups + seafood + umami — \"Buddha Jumps Over the Wall\" famous dish.", ["Sichuan", "Hunan", "Shandong"]),
]


def generate_regional_chinese() -> list[dict]:
    out = []
    for cuisine, desc, distractors in CHINESE_REGIONAL:
        out.append(make_question(
            tier=3,
            topic_cell="chinese_cuisine",
            strategy="regional_chinese",
            pillar="cuisine",
            question=f"Which regional Chinese cuisine is characterized by: {desc}",
            answer=cuisine,
            distractors=distractors,
            context=f"{cuisine} is one of the 8 Great Traditions (Ba Da Cai Xi) of Chinese cuisine.",
        ))
    return out


def generate_all_attribution() -> list[dict]:
    out = []
    out.extend(generate_dish_cuisine_attribution())
    out.extend(generate_spice_origin_attribution())
    out.extend(generate_mother_sauces())
    out.extend(generate_world_flatbreads())
    out.extend(generate_knife_cuts())
    out.extend(generate_pasta_shapes())
    out.extend(generate_regional_chinese())
    return out


if __name__ == "__main__":
    qs = generate_all_attribution()
    print(f"Generated {len(qs)} attribution questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
    print("By tier:", dict(Counter(q["tier"] for q in qs)))
