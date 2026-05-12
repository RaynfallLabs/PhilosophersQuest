---
version: 1
date: 2026-05-12
subject: cooking
---

# Cooking strategy taxonomy

Cooking is the only subject that's *simultaneously* practical (skills you use this weekend), values-laden (what goes in your kids' bodies), historically rich (food traces human migration, conflict, technology), and **culturally formative** — meals together are how families and communities transmit values across generations. Five pillars:

1. **Practical kitchen skills** — what to *do* with food
2. **Nutrition** — what to *put* in your body
3. **World cuisines** — what humans *eat* across the globe
4. **Food history & wonder** — how food *traces humanity*
5. **Family meals + food ceremonies** — how food *binds communities*

Every cooking question carries `_meta.strategy` (the named move it teaches) and `_meta.pillar` (which of the five). Goal: ≥500 questions per tier, ~4000 total, all pillars represented at every tier. Coverage is the priority; quality gates (length, parity, fact-check, anti-rote, clarity) remain in full effect — bigger does not mean looser.

## Stance on contested topics (hybrid)

The bank takes **firm positions where evidence is strong** and **presents the debate where the science is genuinely contested**:

| Firm position (state as fact) | Contested (present the debate) |
|---|---|
| Reused fryer oil produces aldehydes that are bad for you | "All seed oils are inflammatory" — present the omega-6/omega-3 hypothesis + the mainstream view |
| Trans fats are harmful (banned in many places) | Saturated fat — old guidance vs. current research |
| Ultra-processed foods (NOVA-4) correlate with poor health | Raw milk benefits/risks — proponents vs. FDA |
| Fermented foods provide probiotics + bioavailable nutrients | "Organic is nutritionally superior" — pesticide reduction is firm, nutritional advantage is mixed |
| The danger zone (40–140°F) is real and matters | Ancestral / paleo / keto — present as one school among several |
| Cross-contamination from raw chicken can sicken you | Cholesterol revisionism — modern research vs. old USDA framing |
| Maillard reaction creates flavor (good) and AGEs at high temp (mixed) | Bone broth nutritional density — debated |
| Whole foods > ultra-processed | Gluten for non-celiacs |
| Nixtamalization unlocks B3 in corn (prevents pellagra) | |

The bank's voice for contested topics: "**X school argues Y because Z**; **the mainstream view says A because B**" — let the kid see the disagreement.

## Voice + char budgets

| Tier | Char budget | Voice |
|---|---|---|
| T1 | ≤ 280 | Symbol-led, single-fact recall. "What temperature kills salmonella?" |
| T2 | ≤ 480 | One-line scene + question. "A chef arranges all chopped ingredients before turning on heat. This French term is ___?" |
| T3 | ≤ 680 | Scene + technique-with-consequence. Brief setups OK. |
| T4 | ≤ 900 | Multi-sentence setup + judgment / chemistry / history-context required. |
| T5 | ≤ 1100 | Wonder-led, deep history, contested-topic debate framing, science detail. |

Cooking is `escalator_chain` mode at 42s/WIS-10 timer — questions get harder each round in a chain. Variation matters because chain depth matters.

## Pillar 1 — Practical kitchen skills

### Knife + heat (T1-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `knife_safety_basics` | T1 | Sharp > dull; cut away; rolled fingers ("the claw"); never catch a falling knife |
| `knife_cuts_basic` | T2 | Dice, mince, slice, chop |
| `knife_cuts_advanced` | T3 | Julienne, brunoise, chiffonade, batonnet — French names + sizes |
| `heat_methods_basic` | T1-T2 | Boil, simmer, sauté, pan-fry — what each looks/sounds like |
| `heat_methods_advanced` | T3 | Braise, sweat, blanch, deglaze, reduce |
| `sear_vs_saute` | T2-T3 | When to use each; the don't-crowd-the-pan rule |
| `dry_vs_wet_heat` | T2 | Roast/grill/sear (dry) vs braise/stew/poach (wet) — which for what cut |
| `pan_choice` | T3 | Cast iron, stainless, nonstick, carbon steel — each pan's job |
| `oil_smoke_points` | T3 | Olive vs. avocado vs. butter vs. peanut — what to use when |

### Food safety + cleanliness (T1-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `handwash_basics` | T1 | When, how long (20 sec), why |
| `temperature_danger_zone` | T2 | 40–140°F bacteria zone |
| `raw_chicken_protocol` | T2 | Separate board, no rinse, sanitize after |
| `cross_contamination` | T2 | Raw meat → ready-to-eat surfaces is how outbreaks happen |
| `sanitize_vs_clean` | T2 | Clean removes dirt, sanitize kills bacteria |
| `meat_doneness_temps` | T3 | Chicken 165, ground beef 160, beef MR 130, pork 145 |
| `foodborne_pathogens_basic` | T3 | Salmonella (chicken/eggs), E. coli (ground beef/leafy greens), Listeria (deli/cheese), Norovirus |
| `best_by_vs_expiration` | T2 | Best-by = quality; use-by = safety; sniff/look first |
| `food_storage_basics` | T2 | What goes in fridge vs. counter; tomatoes off-fridge |
| `safe_thawing` | T3 | Fridge / cold water / microwave — never countertop |

### Pantry + scaling (T1-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `mise_en_place` | T2 | "Everything in its place" before heat |
| `fifo_storage` | T2 | First in, first out — rotate pantry |
| `recipe_double_halve` | T1-T2 | Scaling 2x / 0.5x; the gotcha — baking times don't scale linearly |
| `recipe_scaling_thirds` | T3 | Awkward fractions; conversion between units |
| `vinaigrette_ratio` | T2 | 3:1 oil:vinegar (and the variations) |
| `rice_water_ratio` | T1 | Long grain 1:2, short grain 1:1.25; ratios vary |
| `pasta_water_salt` | T2 | "Salty like the sea"; pasta water as sauce binder |
| `bread_ratio_basics` | T3 | 5:3 flour:water for basic dough; baker's percentages |
| `knife_sharpening` | T3 | Stones vs. honing rod (alignment vs. removal of metal) |

### Doneness + sensory cues (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `visual_doneness_bread` | T2 | Golden brown; hollow tap on bottom |
| `texture_doneness_meat` | T2-T3 | The finger test for steak doneness |
| `doneness_pasta_al_dente` | T2 | Firm to the bite, white core just disappearing |
| `temperature_doneness_meat` | T3 | The thermometer is the only reliable test |
| `caramelization_color_cues` | T3 | Pale → amber → mahogany → burnt; seconds matter |
| `proof_cues_dough` | T3 | Poke test — slow rebound = ready |
| `doneness_eggs` | T2 | Soft / medium / hard / over-easy / scrambled curd size |
| `fond_recognition` | T3 | The brown stuff left in the pan IS the flavor — deglaze it |

## Pillar 2 — Nutrition

### Macros + micros (T1-T3, firm)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `macros_basic` | T1 | Protein / fat / carb — name + main function |
| `macros_function` | T2 | Protein builds, fat insulates + cell membranes, carbs fuel |
| `micros_basic` | T2 | Vit C (citrus), iron (red meat/leafy), calcium (dairy/leafy) — pair food to nutrient |
| `fiber_basic` | T2 | Soluble vs. insoluble — gut and digestion |
| `protein_complete` | T3 | Essential amino acids; complete (animal, soy, quinoa) vs. incomplete |
| `fat_types` | T3 | Saturated, mono, poly; omega-3 vs. omega-6 |
| `gut_microbiome_basic` | T3 | What lives in there and why diversity matters |

### Food classifications (T2-T3, firm)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `nova_classification` | T3 | Unprocessed → minimally → processed → ultra-processed (NOVA) |
| `ultra_processed_examples` | T2 | Soda, packaged snacks, fast food — ingredient lists with 20+ items, additives |
| `whole_food_examples` | T2 | Apple, egg, fish — single-ingredient identification |
| `seasonal_eating` | T2 | What's in season when; why local-and-seasonal often tastes better |

### Cooking effects on nutrition (T3-T4, mixed firmness)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `maillard_health` | T4 | Maillard makes flavor; very high temp produces AGEs — moderation |
| `raw_vs_cooked_veggies` | T3 | Lycopene goes up cooked; vit C goes down; spinach iron more bioavailable cooked |
| `fermented_food_basics` | T3 | Probiotics, predigestion, K2 production |
| `bone_broth_basics` | T3 | Collagen, gelatin, minerals — nutritional details debated |

### Contested topics (T3-T5, present the debate)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `seed_oils_debate` | T3-T4 | The omega-6 / inflammation hypothesis vs. mainstream view that polyunsaturated fats are heart-healthy |
| `raw_milk_debate` | T4 | Proponents (probiotics, fewer allergies) vs. FDA position (pathogen risk) |
| `saturated_fat_debate` | T4 | "Heart-attack-causing" old guidance vs. 2010s+ research nuance |
| `organic_health_claims` | T3 | Pesticide reduction is firm; nutritional improvement is contested |
| `ancestral_diet_debate` | T4 | Paleo / keto / carnivore vs. balanced traditional vs. plant-forward — present arguments |
| `cholesterol_revisionism` | T4 | Dietary cholesterol's small effect on blood cholesterol; the 2015 USDA reversal |
| `gluten_non_celiac` | T4 | Celiac is firm; non-celiac gluten sensitivity is contested |
| `artificial_sweeteners` | T4 | Generally regarded as safe, but recent research raising questions on gut microbiome |

### Strong-evidence avoids (T2-T4, firm)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `reused_fryer_oil_aldehydes` | T3 | Why specifically bad — lipid peroxidation produces aldehydes; multiple uses compound |
| `trans_fats_history` | T4 | Why banned; partial hydrogenation history; the Crisco arc |
| `sugar_quantity_who` | T2 | WHO recommends < 5% calories from added sugar |
| `deep_frying_concerns` | T3 | Beyond the oil — high temp + breaded surface + reused oil is the cluster |

### Dietary patterns + traditions (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `mediterranean_diet` | T3 | Olive oil, fish, vegetables, moderate wine — Greek/Italian roots |
| `blue_zones` | T4 | Okinawa, Sardinia, Loma Linda — diet patterns of long-lived communities |
| `traditional_food_principles` | T4 | Weston A. Price / Sally Fallon school — fermented, organ meats, bone broth, whole-fat dairy |
| `intermittent_fasting_basics` | T4 | Time-restricted eating overview — research direction |

## Pillar 3 — World cuisines

### French (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `mother_sauces` | T3 | Béchamel, velouté, espagnole, tomato, hollandaise — Carême + Escoffier |
| `brigade_system_basics` | T3 | Chef de cuisine → sous chef → station chefs (saucier, poissonnier, etc.) |
| `bistro_classics` | T2 | Coq au vin, boeuf bourguignon, cassoulet, ratatouille |
| `french_pastry_basics` | T4 | Croissant lamination, mille-feuille, choux paste, pâte brisée |
| `french_cheese_diversity` | T3 | "A country with one cheese for every day" — de Gaulle quip |
| `terroir_concept` | T4 | Soil + climate + tradition — Champagne example, AOC system |

### Italian (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `italian_regional_basics` | T2-T3 | North uses butter/egg-pasta; south uses oil/durum |
| `ragu_vs_bolognese` | T3 | Authentic Bolognese (Bologna; meat-heavy, milk, white wine) vs. ragù umbrella term |
| `pizza_origins_naples` | T2 | Pizza Margherita = 1889 Naples, queen visit, red/white/green tricolor |
| `gnocchi_potato_origin` | T3 | Potato gnocchi only post-Columbian; pre-Columbian gnocchi were semolina |
| `balsamic_aged` | T3 | Traditional Aceto Balsamico Tradizionale di Modena DOP — 12-25 year aging |
| `pasta_water_starch` | T3 | Why "save some pasta water" matters; emulsification with sauce |

### Japanese (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `dashi_basics` | T2 | Kombu (kelp) + bonito (dried tuna) = foundation broth |
| `umami_discovery` | T3 | Ikeda 1908 — isolated glutamate from kombu, named "umami" |
| `kaiseki_tradition` | T4 | Multi-course haute cuisine from tea ceremony |
| `sushi_history` | T3 | Originated as preservation (narezushi) — fermented rice + fish; modern nigiri = Edo period |
| `knife_styles_japan` | T3 | Yanagiba (sashimi), deba (fish), gyuto (chef's), nakiri (vegetables) |
| `wabi_sabi_cooking` | T4 | Asymmetry, simplicity, transient beauty in plating |

### Chinese (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `wok_hei` | T3 | "Breath of the wok" — high heat + agitation, slight smoky char |
| `regional_chinese` | T3 | Sichuan (numb-spicy), Cantonese (steaming, fresh seafood), Hunan (clear spicy), Shandong, Jiangsu, Zhejiang |
| `five_spice` | T2 | Star anise, cloves, cinnamon, Sichuan pepper, fennel |
| `noodle_traditions_china` | T3 | Hand-pulled (la mian), knife-cut (dao xiao), wonton, dan dan |
| `chopsticks_history` | T2 | Han Dynasty; Confucian "no blade at table" influence |
| `tea_ceremony_china` | T4 | Gong fu cha; cultural depth of tea preparation |

### Mexican + pre-Columbian (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `nixtamalization` | T3 | Soaking corn in alkali (lime/wood ash) unlocks niacin (B3) — preventing pellagra |
| `three_sisters` | T2 | Corn + beans + squash — companion planting + nutritional complement |
| `mole_regional` | T3 | Mole poblano vs. mole negro vs. mole verde — Puebla vs. Oaxaca vs. fresh herbs |
| `chiles_basic` | T2 | Jalapeño (mid), poblano (mild), serrano (sharper), habanero (very hot), chipotle (smoked jalapeño) |
| `mexico_columbian_exchange` | T3 | Mexico → world: chiles, tomatoes, corn, vanilla, chocolate, avocado, turkey |
| `masa_corn_culture` | T3 | Tortilla, tamale, sope, gordita — corn central to identity |

### Indian (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `spice_tempering_tadka` | T3 | Blooming spices in hot oil/ghee — releases fat-soluble flavors |
| `dal_basics` | T2 | Lentil-based — toor, masoor, chana, urad |
| `regional_indian` | T3 | North (wheat, dairy, tandoor); South (rice, coconut, sambar); Bengal (fish, mustard); Gujarat (sweet-veg-balanced) |
| `spices_indian_basics` | T2 | Turmeric, cumin, coriander, cardamom, garam masala |
| `ghee_history` | T3 | Clarified butter; Vedic-period antiquity; Ayurvedic ranking |
| `chai_tradition` | T2 | Spiced milk tea — black tea + cardamom + ginger + clove + cinnamon |

### Middle Eastern (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `tahini_basics` | T2 | Sesame paste — base for hummus, halva, dressings |
| `flatbreads_world` | T2 | Pita, naan, lavash, tortilla, injera, roti — flatbread families across cultures |
| `sumac_zaatar` | T3 | Sumac (lemony red), za'atar (thyme/sesame/sumac blend) |
| `pomegranate_molasses` | T3 | Reduced juice — sweet-sour balance in Lebanese/Iranian dishes |
| `hummus_origin_debate` | T3 | Levantine origin debated — Egypt, Lebanon, Syria, Palestine all claim |

### Thai + Southeast Asian (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `four_tastes_balance_thai` | T3 | Sweet/sour/salty/spicy — each dish balances all four |
| `fish_sauce_global` | T3 | Nam pla (Thai) / nuoc mam (Vietnamese) / garum (Roman) — same idea across cultures |
| `pho_history` | T3 | Vietnamese; emerged early 1900s in Hanoi; French + Chinese influences |
| `curry_paste_regional` | T3 | Thai green / red / yellow / massaman — different chiles, lemongrass, galangal |

### American regional (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `bbq_traditions` | T3 | Texas (beef, brisket); KC (sweet sauce); Memphis (dry rub, ribs); Carolina (pork, vinegar) |
| `gumbo_origins` | T3 | West African (okra), French (roux), Cajun + Creole evolution in Louisiana |
| `chowder_types` | T2 | New England (cream) vs. Manhattan (tomato) — and the Maine-vs-Mass feud |
| `jambalaya_paella_parallel` | T3 | Spanish paella → Cajun jambalaya — rice + protein + smoked meat |
| `soul_food_origins` | T3 | African American Southern cooking — collards, cornbread, black-eyed peas, chitlins |

## Pillar 4 — Food history & wonder

### Prehistory + early (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `cooking_made_us_human` | T4 | Richard Wrangham — fire + cooked food enabled brain expansion |
| `fire_history` | T3 | Earliest controlled fire ~1M years ago; cooked starches changed digestion |
| `agricultural_revolution` | T3 | 10,000 BC Fertile Crescent — wheat, barley, peas, lentils, chickpeas, flax, vetch (the founding 8) |
| `domestication_animals` | T3 | Dog (first), sheep, goat, cattle, pig, chicken — order matters |
| `first_breads` | T4 | Natufian flatbreads ~14,000 BP — predate agriculture |

### Preservation pre-refrigeration (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `salting_history` | T2 | Salting meat / fish for long voyages; salt wars; "salary" etymology |
| `smoking_preservation` | T3 | Cold vs. hot smoke; preserves AND flavors |
| `drying_techniques` | T2 | Jerky, dried fruit, dried fish — water-activity reduction |
| `fermentation_pre_modern` | T3 | Sauerkraut (Germany), kimchi (Korea), miso (Japan), cheese (Eurasia), beer/bread (Mesopotamia) |
| `pickling_traditions` | T3 | Acid (vinegar) vs. lacto-fermentation pickles |
| `canning_history` | T4 | Nicolas Appert 1809; Napoleon's 12,000 franc prize for an army-food preservation method |

### Trade routes (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `silk_road_food` | T3 | Noodles, soy, spices, citrus moved east-west; influence on Persian + Italian cuisines |
| `spice_trade_routes` | T3 | Nutmeg, cloves (Maluku/Banda Islands), pepper (India), cinnamon (Sri Lanka) — drove European exploration |
| `columbian_exchange` | T3 | The big one — Americas → Europe: chiles, tomatoes, potatoes, corn, beans, chocolate, vanilla, tobacco, turkey. Europe → Americas: wheat, sugarcane, coffee, citrus, cattle, horses, smallpox |
| `triangle_trade_sugar` | T4 | Sugar plantations + African slave trade + European demand — the dark intertwining |
| `coffee_history` | T3 | Ethiopia (legend of Kaldi) → Yemen (Sufi monasteries) → Mecca → Constantinople → Vienna (1683 siege) → Europe |
| `tea_history` | T3 | China (Shennong) → Japan → Britain (East India Company) → Boston Tea Party |
| `chocolate_history` | T3 | Mesoamerican (Olmec → Maya → Aztec) — sacred bitter drink → Spanish sweet European chocolate |

### Industrial revolution (T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `appert_canning` | T4 | 1809 — Nicolas Appert, the "father of canning" |
| `refrigeration_revolution` | T4 | 1870s+ — meatpacking centralizes in Chicago; transcontinental cold chain |
| `pasteurization` | T3 | Pasteur 1864 — milk + wine safety; foundation of food microbiology |
| `food_dyes_history` | T4 | Early adulterants (lead, copper salts in pickles); pure food acts |
| `wonder_bread_packaging` | T4 | 1921 — first sliced + wrapped + pre-fresh-kept bread; cultural impact |
| `Birdseye_frozen` | T4 | Clarence Birdseye, 1924 — flash-freezing revolution |

### Cuisine + chef culture (T4-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `careme_grand_cuisine` | T5 | Marie-Antoine Carême — first celebrity chef; cooked for Talleyrand, Tsar Alexander, Rothschilds; haute cuisine codifier |
| `escoffier_brigade` | T4 | Brigade de cuisine — kitchen hierarchy + the simplification of French cuisine |
| `brillat_savarin_aphorisms` | T5 | *Physiology of Taste* 1825 — "Tell me what you eat..."; philosophy of food |
| `mfk_fisher_writing` | T5 | American food essayist — *How to Cook a Wolf*, WWII food writing |
| `julia_child_revolution` | T4 | *Mastering the Art of French Cooking* + PBS — French technique to American home cooks |
| `alice_waters_chez_panisse` | T4 | Chez Panisse 1971 — California cuisine, farm-to-table movement, seasonal/local revolution |
| `modernist_cuisine` | T5 | Ferran Adrià (elBulli), Heston Blumenthal (Fat Duck), Nathan Myhrvold (*Modernist Cuisine*) — molecular gastronomy |
| `noma_new_nordic` | T5 | René Redzepi — foraging, fermentation, Nordic terroir |

### Science of cooking (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `maillard_reaction_1912` | T4 | Louis-Camille Maillard — amino acids + reducing sugars + heat → flavor compounds + brown color |
| `ikeda_umami_1908` | T4 | Kikunae Ikeda — isolated glutamate; named "umami"; founded Ajinomoto |
| `harold_mcgee_food_chemistry` | T4 | *On Food and Cooking* (1984) — bridged science to cooks |
| `gluten_chemistry` | T4 | Two proteins (gliadin + glutenin); water + kneading → elastic network |
| `emulsions_basic` | T3 | Hollandaise, mayonnaise, vinaigrette — water + fat held together by emulsifier |
| `gelatin_chemistry` | T4 | Collagen → gelatin via slow heat + water; mouthfeel transformation |
| `caramelization_vs_maillard` | T4 | Sugar alone vs. sugar + amino acid — distinct chemical pathways |
| `sous_vide_basics` | T4 | Precise temperature control via water bath; popularized by Bruno Goussault + Joël Robuchon + Heston Blumenthal |

### Food + politics + revolutions (T4-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `irish_potato_famine` | T3 | 1845-49 — Phytophthora infestans + monoculture + British policy + 1M deaths + 1M emigrants |
| `bread_french_revolution` | T4 | Bread price rises + "let them eat cake" myth + flour shortages → 1789 storming of Bastille |
| `boston_tea_party` | T3 | 1773 — tax on tea + dumping crates — opening act of American Revolution |
| `spice_wars_dutch` | T3 | Banda Islands massacre 1621 — VOC monopolizing nutmeg |
| `bengal_famine_1943` | T4 | 2-3 million deaths under British WWII rule — Churchill's role contested |
| `holodomor_ukraine` | T4 | 1932-33 — Soviet collectivization + grain requisition + 3.5-5M Ukrainian deaths |
| `great_leap_forward_famine` | T4 | 1959-61 — Mao's policies + 15-45M deaths (deadliest famine in history) |
| `green_revolution_borlaug` | T4 | Norman Borlaug — wheat varieties + dwarf cultivars; estimated 1 billion lives saved |
| `WWII_rationing` | T4 | Sugar, butter, meat rationing in US/UK; victory gardens; spam cuisine |

### Food origin stories (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `pizza_margherita_history` | T2 | Pizza Margherita = 1889 Naples, Queen Margherita visit, red/white/green tricolor |
| `caesar_salad_tijuana` | T3 | Caesar Cardini, Hotel Caesar, 1924 Tijuana — invented during Prohibition tourism |
| `buffalo_wings_origin` | T2 | 1964 Anchor Bar, Buffalo NY — Teressa Bellissimo improvising late-night snack |
| `apple_pie_english_origin` | T3 | Not American originally — Chaucer mentions apple pie 1381; American legend later |
| `croissant_vienna_origin` | T3 | Vienna kipferl shape (1683 siege commemoration) → Marie Antoinette → French refinement |
| `sandwich_earl_origin` | T2 | John Montagu, 4th Earl of Sandwich, 1762 — gambling all night, didn't want to leave table |
| `hot_dog_coney_island` | T3 | Charles Feltman 1867; Nathan Handwerker 1916 Nathan's Famous |
| `banh_mi_french_vietnam` | T3 | French baguette + Vietnamese fillings — 1950s emergence in Saigon after French departure |
| `tiramisu_treviso_origin` | T3 | 1960s Treviso, Italy — Roberto Linguanotto / Le Beccherie restaurant generally credited |
| `carbonara_origin_debate` | T4 | American GI WWII Roman trattoria theory vs. coal-miner ("carbonari") theory |
| `cobb_salad_brown_derby` | T3 | 1937 Hollywood — Robert H. Cobb of Brown Derby, midnight fridge-clean-out story |
| `eggs_benedict_origin_debate` | T3 | Multiple NYC claims, 1894 most likely — Delmonico's vs. Waldorf vs. Mrs. Benedict story |
| `chicago_deep_dish_history` | T3 | 1943 Uno's Pizzeria, Ike Sewell — Chicago vs. New York pizza debate |
| `philly_cheesesteak_origin` | T3 | Olivieri brothers, Pat's King of Steaks, 1930s South Philly |
| `bagel_history_polish_jewish` | T3 | Krakow 1610 origin (gift to women after childbirth); Eastern European Jewish immigration to NYC |
| `chinese_food_in_america` | T4 | Chop suey, General Tso, fortune cookies — American-Chinese cuisine evolution |
| `taco_americanization` | T3 | Hard-shell taco (1940s LA) → Glen Bell → Taco Bell 1962 — divergence from Mexican original |
| `french_dip_origin` | T4 | 1918 LA — Philippe's vs. Cole's competing claims |
| `marco_polo_pasta_myth` | T3 | Pasta in Italy predates Marco Polo's return; myth perpetuated by Macaroni Journal in 1929 |
| `coffee_battle_of_vienna_1683` | T3 | Ottoman retreat → coffee beans abandoned → Kolschitzky first Viennese coffeehouse |

### Industrial / modern food history (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `pure_food_drug_act_1906` | T4 | Sinclair's *The Jungle* → Roosevelt → first US food safety legislation |
| `prohibition_cocktail_evolution` | T4 | 1920-1933 — speakeasy, mixers to mask bathtub gin, cocktail recipes that survived |
| `tv_dinner_swanson_1953` | T3 | Swanson aluminum tray, post-Thanksgiving turkey surplus, Gerry Thomas innovation |
| `spam_history_hormel` | T3 | 1937 Hormel; WWII Allied rations; Hawaiian + Korean cuisine adoption (musubi, budae jjigae) |
| `microwave_oven_history` | T3 | Percy Spencer 1945 Raytheon — radar-tube melted candy bar in pocket |
| `mcdonalds_franchise_history` | T3 | McDonald brothers Speedee Service System + Ray Kroc franchising 1955 |
| `slow_food_movement_petrini` | T4 | Carlo Petrini 1986 — protest against McDonald's at Spanish Steps Rome, snail symbol |
| `bourdain_kitchen_confidential` | T4 | 2000 NY Times article → book → *No Reservations* — cultural shift in food media |
| `food_network_rise` | T4 | 1993 launch — Emeril → Bobby Flay → Iron Chef America → cultural impact on home cooking |
| `frozen_food_birdseye` | T4 | Clarence Birdseye 1924 flash-freezing — Inuit fishing inspiration |
| `pasteur_milk_1864` | T3 | Louis Pasteur — pasteurization founding food microbiology |
| `whiskey_rebellion_1791` | T4 | Western Pennsylvania farmers vs. federal tax — Washington's enforcement |
| `boston_tea_party_1773` | T3 | Tax on tea + dumped 342 crates — opening act of American Revolution |

### Food science wonder (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `onions_crying_chemistry` | T3 | Syn-propanethial-S-oxide — sulfur enzyme released when cells broken |
| `capsaicin_heat_perception` | T3 | TRPV1 receptor — same as actual heat, no thermal change in tissue |
| `lactose_intolerance_genetics` | T4 | LCT gene mutation 7,500 years ago — European/African pastoralists kept producing lactase into adulthood |
| `sourdough_microbiome` | T4 | Wild yeast + lactobacillus — local microflora makes regional differences (San Francisco sourdough) |
| `bread_yeast_biology` | T3 | *Saccharomyces cerevisiae* — CO₂ trapped in gluten network |
| `cheese_aging_microbes` | T4 | Microbial succession — rind ecology, *Penicillium roqueforti* in blue cheese |
| `pasta_salty_water_science` | T3 | Boiling point elevation is tiny; flavor + starch-sauce binding is the real reason |
| `bell_pepper_sweetening` | T3 | Pectin breakdown + sugar concentration when cooked |
| `bone_broth_collagen_science` | T3 | Collagen triple-helix → gelatin via slow heat + water |
| `world_hottest_pepper` | T3 | Carolina Reaper (2 million SHU) then Pepper X (2.6M SHU, 2023) on Scoville scale |
| `durian_smell_chemistry` | T4 | 50+ volatile compounds — sulfur + ester combination unique |
| `saffron_most_expensive` | T3 | 150-200 *Crocus sativus* flowers per gram, hand-harvested stigmas |
| `vanilla_hand_pollination` | T4 | Melipona bee co-evolved in Mexico; Edmond Albius (12yo enslaved boy, 1841) discovered hand-pollination — now standard everywhere |
| `truffle_market_white_alba` | T4 | *Tuber magnatum pico* — Piedmont autumn — pigs/dogs hunt — $4000+/lb |
| `wagyu_kobe_classification` | T4 | Tajima bloodline cattle — marbling grade (BMS 1-12); Kobe trademark restrictions |
| `iberico_pig_acorn_diet` | T3 | Spanish *Dehesa* oak savanna; *Bellota* grade — acorn-finished pigs, oleic acid in fat |
| `parmigiano_24_month_minimum` | T3 | DOP certification — 24-month minimum, must use specific milk + region — vs. generic "parmesan" |
| `roquefort_cave_aging` | T3 | Combalou caves Soulzon, sheep's milk, *Penicillium roqueforti* — protected denomination |
| `champagne_methode_traditionnelle` | T4 | Secondary fermentation in bottle, riddling, disgorgement — Dom Pérignon refined |
| `single_estate_chocolate` | T4 | Bean-to-bar movement; criollo/forastero/trinitario varieties; cacao origins |

### Food + politics + revolutions (T4-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `irish_potato_famine` | T3 | 1845-49 — *Phytophthora infestans* + monoculture + British policy + 1M deaths + 1M emigrants |
| `bread_french_revolution` | T4 | Bread price rises + flour shortages → 1789 Bastille storming; "let them eat cake" likely apocryphal |
| `boston_tea_party_food_revolt` | T3 | (See "Industrial / modern" — overlapping content) |
| `spice_wars_dutch_banda` | T3 | 1621 Banda Islands massacre — VOC monopolizing nutmeg, ~15,000 islanders killed |
| `bengal_famine_1943` | T4 | 2-3 million deaths under British WWII rule — Churchill's role in grain diversion contested |
| `holodomor_ukraine_1932` | T4 | Soviet collectivization + grain requisition + 3.5-5M Ukrainian deaths — recognized as genocide by many states |
| `great_leap_forward_famine` | T4 | 1959-61 — Mao's "Four Pests" + steel quotas + grain misreporting → 15-45M deaths, deadliest famine ever |
| `green_revolution_borlaug` | T4 | Norman Borlaug — dwarf wheat + Mexico/India deployment → estimated 1 billion lives saved |
| `WWII_rationing_victory_gardens` | T4 | US/UK sugar, butter, meat rationing; victory gardens; spam cuisine; Eleanor Roosevelt's WH garden |
| `food_aid_modern_politics` | T5 | USAID, USDA food aid programs, dumping criticism + dependency debate |
| `genocide_food_weaponization` | T5 | Famine as policy — Holodomor, North Korea, Tigray; food as warfare |
| `ag_subsidies_history_corn` | T5 | US 1973 Earl Butz "get big or get out" — high-fructose corn syrup era |

### Religious + ritual food traditions (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `kosher_basics` | T3 | Kashrut — no pork, no shellfish, no mixing meat + dairy, schechita slaughter |
| `halal_basics` | T3 | Dhabihah slaughter, no pork, no alcohol, name of Allah invoked |
| `lent_fasting_fish` | T3 | Christian fasting traditions — meatless Fridays explain Catholic-region fish dishes |
| `ramadan_iftar` | T3 | Fasting sunrise to sunset; dates first (Prophet's tradition); family + mosque dinners |
| `kitchen_god_china_lunar` | T4 | Lunar New Year — Kitchen God reports to Jade Emperor; sweet treats "sweeten his tongue" |
| `feast_days_christian` | T4 | Christmas + Easter + saint days — food as ritual marker; cured meats, fish, lambs |
| `hindu_vegetarianism_ahimsa` | T3 | *Ahimsa* (non-harm) principle; cow sacredness; vegetarian fraction of population |
| `eucharist_communion_christian` | T3 | Last Supper → bread + wine sacrament; transubstantiation vs. symbolism varies by tradition |
| `hindu_prasad_offering` | T3 | Food offered to deity, blessed, then distributed — concept of sanctified eating |
| `bahai_19_day_fast` | T4 | Sunrise to sunset, 19 days before Naw-Rúz (New Year) |
| `buddhist_meal_chants` | T4 | Five Reflections (Zen) — gratitude before eating, considering the labor and origins |
| `mormon_fast_sunday` | T4 | Monthly fast Sunday — skip two meals, donate meal cost as fast offering |

## Pillar 5 — Family meals + food ceremonies

This pillar centers Western family meal traditions (with the user's emphasis) and food ceremonies across cultures and history. Food is how humans mark **time** (holidays, seasons), **transitions** (birth, marriage, death, coming-of-age), and **belonging** (the daily family table).

### Western family meal traditions (T1-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `family_dinner_tradition_western` | T2 | The daily family meal — table conversation, screen-free, generational anchor |
| `sunday_dinner_tradition` | T2-T3 | Italian-American Sunday gravy / UK Sunday roast / Polish-American kielbasa Sunday — generational ritual |
| `family_meal_decline_data` | T4 | Sociological data — family meal frequency dropped sharply 1970s-2010s; correlation with adolescent outcomes |
| `family_meal_benefits_research` | T4 | Research on child outcomes: language, vocabulary, eating habits, mental health markers |
| `saying_grace_blessing` | T2 | Christian table-blessing tradition — gratitude as ritual; secular variations |
| `breaking_bread_etymology` | T3 | "Companion" from Latin *com* + *panis* (with + bread); to share bread is to be a companion |
| `birthday_cake_candles` | T1 | Origins (ancient Greek moon-offering to Artemis → German Kinderfest 18th century → wishes on candles) |
| `napkin_in_lap_etiquette` | T1 | Most basic Western dining etiquette — napkin in lap on sitting, on chair when leaving |
| `wait_for_host_etiquette` | T1 | Don't start until everyone served + host begins |
| `please_pass_etiquette` | T1 | Reach across-the-table-no, ask politely-yes |
| `continental_vs_american_fork` | T3 | Continental (fork in left, never switches) vs. American "zigzag" (switch fork to right) |
| `table_setting_basics` | T2 | Fork left, knife/spoon right, glass upper right, plate centered |
| `formal_table_setting_courses` | T3 | Multiple forks/knives from outside in; bread plate upper left |
| `cookbook_grandmas_recipe` | T3 | Family recipes as inherited knowledge; oral tradition of measurement-by-feel |
| `joy_of_cooking_1931` | T3 | Irma Rombauer self-published — American kitchen bible across generations |
| `betty_crocker_brand_history` | T3 | Fictional brand-character 1921; cookbook published 1950 — convenience cooking era |
| `fannie_farmer_measurement_1896` | T4 | First standardized cup/teaspoon measurements — Boston Cooking-School Cook Book |

### Western banquets, feasts, balls (NEW emphasis, T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `medieval_banquet_structure` | T4 | Trenchers (stale-bread plates), hierarchy seating "above/below the salt," peacock + swan + boar's head centerpiece |
| `medieval_subtleties` | T4 | Sugar sculptures between courses depicting allegory, royal arms, religious scenes |
| `tudor_feast_traditions` | T4 | Henry VIII's banquets, marchpane (marzipan sculpture), boar's head Christmas |
| `service_a_la_francaise` | T4 | 18th-century "French service" — all dishes on table at once, guests serve themselves |
| `service_a_la_russe_1810` | T4 | Russian Ambassador Kurakin in Paris — course-by-course service revolution that became modern dining |
| `court_banquet_versailles` | T4 | Louis XIV public dining as theater; le grand couvert; French haute cuisine origin |
| `victorian_dinner_party_codes` | T4 | Elaborate course structure, dressing for dinner, seating arrangements, conversation rules |
| `victorian_dinner_evolution` | T5 | 1850s-1900s — the high-Victorian dinner with 10+ courses simplified post-WWI |
| `20th_century_simplification` | T4 | Servantless kitchens + war rationing + women's labor changes → smaller dinner parties |
| `first_restaurant_boulanger_1765` | T3 | A.B. Boulanger's "restorative" bouillons (Latin *restaurare* = restore) — Paris pre-Revolution |
| `restaurant_post_revolution_diaspora` | T4 | French Revolution dispersed aristocratic chefs into public restaurants — birth of modern dining |
| `delmonicos_nyc_origin` | T4 | 1827 first fine-dining restaurant in America; à la carte menus; Eggs Benedict birthplace |
| `state_dinner_us_presidential` | T4 | Diplomatic protocol meal; chef + butler + menu selection; honoring foreign heads of state |
| `inauguration_luncheon_tradition` | T4 | 1953 first formal lunch (Eisenhower); Statuary Hall; symbolism of regional foods |
| `royal_banquet_diplomacy` | T4 | Royal banquets as soft power — UK state dinners, menu cards as historical record |
| `charity_ball_black_tie` | T3 | Black-tie origin (1880s Tuxedo Club NY); charity ball tradition; debutante presentation |
| `debutante_ball_cotillion` | T4 | Coming-out tradition — French *cotillon*, Vienna Opera Ball, Mayflower Ball NY, English Season |
| `harvest_feast_traditions` | T3 | English Harvest Home; German Erntedankfest; American Thanksgiving descended from these |
| `hunt_dinner_tradition` | T4 | English hunt breakfast/dinner; American Thanksgiving's wild game roots; the hunt as social ritual |
| `school_formal_dinner` | T3 | Oxbridge formal hall, high table, grace, gowns — academic banquet tradition |
| `business_banquet_evolution` | T4 | Power lunch tradition (NYC 1970s+); corporate retreat banquets; modern hybrid forms |

### Wedding food traditions (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `wedding_cake_roman_origin` | T3 | Ancient Roman *confarreatio* — cake-breaking over bride's head for fertility + prosperity |
| `white_wedding_cake_victoria_1840` | T3 | Queen Victoria's wedding to Albert — white royal icing as wealth display (sugar was expensive) |
| `three_tier_wedding_cake_symbolism` | T3 | Bottom for guests, middle for absent friends, top saved for first anniversary |
| `royal_wedding_fruit_cake_tradition` | T4 | UK royal wedding fruit cake — preserved well, top tier christening of first child |
| `wedding_cake_cutting_ceremony` | T2 | Bride + groom cut together — sharing first meal as symbol of unity |
| `top_tier_anniversary_freeze` | T2 | Save top tier, eat on first anniversary or at first child's christening |
| `wedding_toast_champagne` | T2 | Champagne tradition; "clinking" history (Roman superstition about hearing as 5th sense) |
| `bridal_shower_origins_us` | T3 | American 1890s origin — friends "showering" bride with gifts; Dutch dowry-replacement legend |
| `rehearsal_dinner_origin` | T3 | American 20th-century tradition — practice + thank-you meal for wedding party |
| `engagement_party_traditions` | T3 | Family introductions through food; pre-wedding celebration |
| `wedding_breakfast_uk` | T3 | UK "wedding breakfast" — first meal after the ceremony (regardless of time of day) |
| `garter_bouquet_toss_food` | T3 | American reception traditions during dancing/eating |
| `groom_cake_southern` | T3 | American Southern tradition — second cake (often dark, chocolate, or themed) for the groom |
| `wedding_favors_history` | T3 | Italian *confetti* (sugar-coated almonds); Jordan almonds 5-for-good-luck tradition |

### Life milestone celebrations (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `quinceanera_15_food` | T3 | Latin American 15th birthday celebration — multi-tier cake, formal meal |
| `sweet_16_traditions_us` | T3 | American 16th birthday — cake, traditions varying by community |
| `bar_bat_mitzvah_food` | T3 | Jewish 13yo (boy) / 12yo (girl) — challah, kiddush wine, full kosher banquet |
| `baptism_feast_traditions` | T3 | Christian celebration — cake, family meal, godparents tradition |
| `first_communion_meal` | T3 | Catholic 7-8yo first Eucharist — white-themed cake + family lunch |
| `confirmation_feast` | T4 | Christian rite of passage; food differs by tradition |
| `graduation_party_traditions` | T3 | American open-house party tradition, regional variations |
| `coming_of_age_meals_global` | T4 | Apache Sunrise Ceremony; African age-set ceremonies; Japanese Seijin Shiki; cross-cultural patterns |

### Funeral + memorial food (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `american_funeral_casserole` | T3 | Community brings food to grieving family — practical compassion tradition |
| `english_funeral_baked_meats` | T3 | "Funeral baked meats" (Hamlet, "the funeral baked meats did coldly furnish forth the marriage tables") |
| `irish_wake_traditions` | T3 | Vigil with body, food + whiskey, storytelling — pre-funeral gathering |
| `sit_shiva_meal_consolation` | T3 | Jewish 7-day mourning — community brings meals (eggs, lentils as round = continuity) |
| `repast_post_burial` | T3 | African American + Catholic + many traditions — meal after burial as community closure |
| `funeral_cake_west_indies` | T3 | Caribbean traditions — black cake (heavy fruit cake) shared with mourners |
| `ancestor_offerings_cross_cultural` | T4 | Mexican Day of the Dead, Chinese Qingming, Japanese Obon — feeding ancestors |

### Holiday + seasonal feasts (Western emphasis, T1-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `thanksgiving_history` | T2 | 1621 Plymouth harvest celebration; Lincoln 1863 proclamation; FDR fixed date 1941 |
| `thanksgiving_menu_evolution` | T3 | Original menu (likely venison, fowl, corn, seafood); 19th-century rebranding to turkey-centric |
| `christmas_dinner_western` | T2 | Roast goose/turkey/ham; UK Christmas pudding (flaming brandy); plum pudding history |
| `12_days_christmas_feast` | T4 | Medieval 12 days; feasts on each (St. Stephen, Holy Innocents, Epiphany) |
| `saturnalia_roman_origin` | T4 | Pre-Christian Roman December feast; influence on Christmas dating + traditions |
| `boars_head_christmas` | T4 | Medieval English Yuletide centerpiece — Queen's College Oxford boar's head carol still sung |
| `plum_pudding_mince_pie` | T4 | English Christmas — mince pies originally meat-based (mincemeat etymology) |
| `bûche_de_noel` | T3 | French Yule log cake — burning Yule log → cake symbolism |
| `panettone_italy_christmas` | T3 | Milan-origin tall sweet bread — Christmas + New Year tradition |
| `easter_lamb_tradition` | T3 | Christian Easter lamb — Passover roots, symbolism of Lamb of God |
| `easter_ham_tradition` | T3 | Christian Easter ham (US/UK distinctive) — preservation through winter, fresh by spring |
| `hot_cross_buns` | T3 | Good Friday tradition — spiced sweet bun with cross |
| `paska_easter_bread` | T3 | Eastern European Easter bread — yeast, decorated, blessed |
| `mardi_gras_carnival_feast` | T3 | Pre-Lent indulgence — Fat Tuesday, king cake, beads, New Orleans tradition |
| `kings_cake_galette_des_rois` | T3 | Twelfth Night cake — hidden bean/figurine, finder is king/queen for the day |
| `valentines_day_dinner_origin` | T3 | 14th-century chivalric love → 19th-century commercialization; chocolate + roses |
| `mothers_day_brunch_tradition` | T2 | Anna Jarvis 1908; commercialization criticism; brunch ritual emergence |
| `fathers_day_grilling` | T2 | American mid-20th-century — paired with summer grilling masculine imagery |
| `new_years_eve_dinner_western` | T3 | Spanish 12 grapes at midnight; Italian lentils for prosperity; Southern hoppin' john |
| `hogmanay_scotland` | T4 | Scottish New Year — first-footing, black bun, whisky |
| `burns_night_haggis` | T4 | January 25 — Robert Burns birthday; haggis with "Address to a Haggis"; Scotch + neeps |
| `st_patricks_day_feast` | T3 | Irish-American tradition — corned beef + cabbage (more American than Irish) |
| `oktoberfest_munich` | T3 | 1810 Bavarian royal wedding; beer + sausage + pretzel; lederhosen/dirndl tradition |
| `bastille_day_french` | T4 | July 14 — French national day; feast traditions; revolutionary commemoration |
| `independence_day_4th_july` | T2 | American BBQ tradition; hot dogs + burgers + apple pie + watermelon |
| `juneteenth_food_traditions` | T3 | African American June 19th emancipation celebration — red foods (strawberry soda, red velvet, watermelon) |
| `kwanzaa_food_traditions` | T4 | 1966 founded — African American/Pan-African; Karamu feast Dec 31 with African dishes |
| `chinese_lunar_new_year_food` | T3 | Dumplings (wealth), noodles (longevity), fish (surplus), nian gao (rising prosperity) |
| `passover_seder_14_elements` | T3 | Matzah, bitter herbs (maror), charoset, four cups of wine, afikomen tradition |
| `hanukkah_oil_foods` | T3 | Latkes + sufganiyot — oil-fried foods commemorating Temple oil miracle |

### Cross-cultural food ceremonies (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `japanese_tea_ceremony_chanoyu` | T4 | Sen no Rikyu 16th c. formalization; wabi-cha; matcha preparation; tea house architecture |
| `chinese_gongfu_cha` | T4 | Multi-infusion tea preparation; small pots; appreciation of tea evolution across pours |
| `ethiopian_coffee_ceremony` | T3 | Jebena (clay pot); three rounds (Abol/Tona/Baraka); women's hospitality tradition |
| `korean_kimjang_unesco` | T4 | Communal kimchi-making before winter; UNESCO Intangible Heritage 2013 |
| `indian_thali_eating` | T3 | Multi-bowl meal on platter; right-hand eating; banana leaf in South |
| `jewish_shabbat_dinner` | T3 | Friday sundown — challah braiding (6 strands = 12 tribes), kiddush wine, candle lighting, family |
| `italian_la_pranzo_domenica` | T3 | Sunday lunch — multi-hour family gathering, multiple courses, generational ritual |
| `french_meal_progression` | T3 | Aperitif → entrée → plat → fromage → dessert → café/digestif |
| `spanish_sobremesa` | T3 | Post-meal conversation tradition — staying at table after eating |
| `spanish_tapas_culture` | T2 | Bar-hopping small plates; *tapa* = "cover" (placed on glass to keep flies out) |
| `mexican_day_of_dead_food` | T3 | Pan de muerto, ofrendas, favorite foods of deceased ancestors |
| `russian_zakuski_vodka` | T4 | Appetizer table + vodka pairing — tradition of small bites with drinks |
| `greek_philotimo_hospitality` | T4 | Honor through giving food generously; hospitality as cultural value |
| `german_kaffeeklatsch` | T2 | Afternoon coffee + cake + conversation — German social institution |
| `british_tea_time_anna_bedford` | T2 | Anna Duchess of Bedford 1840s — afternoon tea to bridge long gap between meals |
| `british_cream_tea` | T3 | Scones with clotted cream + jam; Devon (cream first) vs. Cornwall (jam first) debate |
| `high_tea_vs_afternoon` | T3 | Afternoon tea = aristocratic mid-afternoon snack; high tea = working-class evening meal |
| `viennese_coffeehouse_culture` | T4 | UNESCO recognized; intellectual culture; Vienna circle Stammtisch tradition |
| `parisian_cafe_culture` | T3 | Sidewalk cafes; flâneurs; existentialist Cafe de Flore + Les Deux Magots |

## Pillar tier-totals (target — coverage-first)

| Tier | Practical | Nutrition | Cuisine | History/Wonder | Family/Ceremony | **Total** |
|---|---:|---:|---:|---:|---:|---:|
| T1 | 150 | 100 | 150 | 100 | 100 | **600** |
| T2 | 200 | 200 | 200 | 150 | 150 | **900** |
| T3 | 250 | 200 | 250 | 250 | 250 | **1200** |
| T4 | 150 | 200 | 150 | 250 | 200 | **950** |
| T5 | 50 | 150 | 100 | 150 | 100 | **550** |
| **Total** | **800** | **850** | **850** | **900** | **800** | **~4200** |

Every tier ≥ 500 floor. ~4200 total — roughly 8x the current cooking bank (538). Family/Ceremony pillar reaches 800 questions reflecting your emphasis. History/Wonder reaches 900 with the new origin stories, food science, food revolutions, and ag history. Coverage-first: gates are *not* relaxed — bigger does not mean looser.

## Generation approach

Unlike math, cooking can't use sympy-style correctness validation — most facts need a fact-check LLM gate. Hybrid:

1. **Deterministic Python generators (~25%)**: recipe scaling, "what's this knife cut called?", "which cuisine claims this dish?", flatbread family, basic safety temps, basic ratios, table-setting recognition, simple etiquette identification. ~1000 questions.
2. **LLM agents (~75%)**: nutrition + history + cuisine + family/ceremony + contested-topic debate framing + chef + science wonder + holiday/feast/wedding traditions. ~3200 questions.
3. **New validator: `validate_cooking_facts.md`** — LLM job that fact-checks nutrition + history + ceremonial-tradition claims. Especially important for contested-topic framing (both sides represented honestly) AND for attributions (don't credit the wrong chef, year, or country).
4. **Standard gates remain in full effect**: schema, length_parity (NOT exempted for cooking — choices must be parallel in form AND length), length_budget per tier, anti_rote (NOT exempted — forces scene-led phrasing), duplicate (threshold 0.85 — cooking doesn't benefit from the math template-exposure relaxation).

## Anti-rote — special handling for cooking

Cooking's vocabulary-heavy nature would trigger anti-rote definition-shells ("What is mise en place?") at high rates. Two responses:

1. **Scene-led phrasing**: "A chef arranges all chopped ingredients before turning on the heat. The French term for this is ___?" — scene + question, bypasses the regex AND is more pedagogical.
2. **Don't exempt cooking from anti-rote** (unlike math/grammar). The discipline forces better question design.

## What success looks like

- A T1 cooking question teaches a basic move *or* a basic name in one breath.
- A T2 question reveals a "huh, didn't know that" beat about why a technique works.
- A T3 question makes the player respect an ingredient or technique they'd previously taken for granted.
- A T4 question shows the science or history behind a familiar dish.
- A T5 question makes the player want to read a chef's memoir or visit a country for its food.

Distractor design across pillars:

- **Practical**: distractors are common confused techniques (sauté vs. sweat — both pan-fried but different intent)
- **Nutrition**: distractors are competing schools (low-fat 1990s vs. low-carb 2010s vs. balanced traditional)
- **Cuisine**: distractors are adjacent-but-wrong dishes/cuisines (a Cantonese dish offered as Sichuan)
- **History**: distractors are plausibly-confused dates, places, attributions
- **Family/Ceremony**: distractors are adjacent-but-wrong traditions (Easter ham vs. Easter lamb across denominations; afternoon tea vs. high tea confusion)
