---
version: 1
date: 2026-05-12
subject: animal
---

# Animal strategy taxonomy

Animals is a wonder-rich subject with five natural pillars. Biological diversity is staggering (8.7M estimated species, ~1M described). The deep timeline goes back 540M years to the Cambrian explosion — five mass extinctions, dinosaurs, Pleistocene megafauna. Humans have lived with domesticated animals for 15,000-40,000 years (dogs first). Animals appear in every mythology, religion, and culture humans have built. And in-game, the player harvests animal corpses for food — practical biology + butchery knowledge matters.

Five pillars:

1. **Animal diversity + biology** — what's *alive* on Earth
2. **Evolution + paleontology** — what *was* alive and how we got here
3. **Domestication + husbandry** — animals humans raise
4. **Hunting, harvest, butchery** — animals humans take
5. **Animals in human culture** — animals in myth, religion, history, partnership

Every animal question carries `_meta.strategy` (the named pedagogical move) and `_meta.strategy_pillar` (which of the five). Target ≥100 questions per tier (firm floor); aim for comprehensive coverage across topics; total bank ~3500-4500 questions.

## Stance summary

| Position | Stance |
|---|---|
| Evolution + deep timeline | Standard biology. Permian extinction = 252M years ago. Whales descended from land mammals. Birds are theropod dinosaur descendants. Theological framings live in the theology bank, not here. |
| Eating animals | Biology, not moral question. Humans are omnivores. The bank doesn't entertain "is eating animals wrong?" — it teaches humane treatment, fair chase, no waste, butchery skill, respect for the animal taken. |
| Humane treatment | Firm position. Cruelty is wrong. Welfare frameworks (Five Freedoms 1965) are real and matter. CAFO concerns are real. Industrial husbandry can be done well or poorly. Specific welfare debates within husbandry are contested. |
| Hunting | Firm: hunting has been part of human life for 200,000+ years and remains a legitimate practice. North American Conservation Model funded modern wildlife restoration. Trophy hunting and indigenous hunting rights are contested topics (presented as debates). |
| Paleontology | Firm: scientific consensus. Pleistocene overkill vs. climate hypothesis IS contested — both sides shown. |
| Animal rights as a movement | Mentioned as a real cultural phenomenon (Henry Bergh ASPCA 1866; Peter Singer 1975; PETA 1980). Singer's utilitarian argument summarized as a position someone holds; bank doesn't endorse "all animal use is wrong." |

## Voice + char budgets (mirroring cooking)

| Tier | Hard cap | Word count guide | Voice |
|---|---:|---|---|
| T1 | ≤ 280 | ~30 words | Symbol-led, single-fact recall. "Largest animal alive today?" |
| T2 | ≤ 480 | ~70 words | One-line scene + question. "Egyptian goddess depicted as a cat..." |
| T3 | ≤ 680 | ~110 words | Scene + biology/history with consequence. Brief setup OK. |
| T4 | ≤ 900 | ~150 words | Multi-sentence setup + chemistry/evolution/history-context. |
| T5 | ≤ 1100 | ~180 words | Wonder-led; deep paleontology; contested debate framing. |

Animal is `chain` mode at 34s/WIS-10 timer. In-game action = harvesting (post-kill processing). Chain depth matters → variation matters.

## Quality gates

| Gate | Configuration |
|---|---|
| schema | required |
| length_parity | **answer-outlier rule (1.6× multiplier)** — same as cooking, registered in `ANSWER_OUTLIER_SUBJECTS` |
| length_budget | per-tier caps above (registered in `SUBJECT_TIER_BUDGETS`) |
| anti_rote | NOT exempted (forces scene-led phrasing) |
| duplicate | 0.85 similarity (standard) |
| **NEW** `validate_animal_facts` | LLM fact-check for species attributions, dates, taxonomic accuracy, religious traditions |
| `validate_balance` | contested-topic both-sides framing (overkill vs. climate for Pleistocene extinctions; trophy hunting; indigenous hunting rights; A2 vs. A1 milk; industrial vs. regenerative husbandry) |

---

## Pillar 1 — Animal diversity + biology

### Vertebrate classes (T1-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `vertebrate_classes_basic` | T1 | The 5 vertebrate classes: fish, amphibian, reptile, bird, mammal |
| `mammal_defining_features` | T2 | Mammary glands, hair/fur, three middle-ear bones, warm-blooded, live-bearing (mostly) |
| `bird_defining_features` | T2 | Feathers, beaks, eggs, warm-blooded, hollow bones, evolved from theropod dinosaurs |
| `reptile_defining_features` | T2 | Scales, cold-blooded, mostly egg-laying, ectothermic, lack feathers/fur |
| `amphibian_defining_features` | T2 | Smooth wet skin, life cycle with aquatic larval phase, cold-blooded |
| `fish_classes_basic` | T3 | Bony fish (most), cartilaginous (sharks/rays), jawless (lampreys/hagfish) |
| `monotremes_special` | T3 | Egg-laying mammals: platypus + 4 echidna species — only 5 living monotremes |
| `marsupials_basic` | T3 | Pouch-bearers: kangaroo, koala, wombat, opossum (only marsupial in N. America) |
| `endotherm_vs_ectotherm` | T3 | More precise than "warm/cold blooded" — internal temperature regulation distinction |

### Invertebrate phyla (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `arthropod_subgroups` | T2 | Insects (6 legs), arachnids (8 legs), crustaceans (mostly aquatic), myriapods (centipede/millipede) |
| `insect_orders_basic` | T3 | Coleoptera (beetles, largest order ~400K species), Lepidoptera (butterflies/moths), Diptera (flies), Hymenoptera (bees/ants/wasps) |
| `mollusk_classes` | T3 | Gastropods (snails), bivalves (clams/oysters), cephalopods (octopus/squid) |
| `cephalopod_intelligence` | T3 | Octopus has 3 hearts, 9 brains (1 central + 8 in arms), can solve mazes + use tools |
| `cnidaria_basic` | T3 | Jellyfish, coral, anemone, hydra — radial symmetry, stinging cells (nematocysts) |
| `echinoderm_examples` | T3 | Sea stars, sea urchins, sand dollars, sea cucumbers — 5-fold radial symmetry |
| `annelid_basic` | T2 | Segmented worms — earthworms, leeches, polychaetes |
| `species_count_total` | T2 | ~8.7 million estimated species on Earth, ~1.4 million described; insects ~75% of described |

### Reproduction strategies (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `oviparous_viviparous` | T2 | Egg-laying vs. live-bearing — the basic distinction |
| `ovoviviparous` | T3 | Eggs hatch inside parent — some sharks, snakes |
| `parthenogenesis_animals` | T3 | "Virgin birth" — some whiptail lizards, some shark species (bonnethead), Komodo dragon |
| `sequential_hermaphrodite` | T3 | Clownfish (born male, dominant becomes female); wrasses (the reverse) |
| `marsupial_pouch_development` | T3 | Joey born very early, completes development in pouch — kangaroo, koala |
| `monotreme_egg_laying` | T3 | Platypus + echidna lay eggs and produce milk (no nipples — milk through skin) |
| `r_vs_k_selection` | T4 | Many offspring with low investment (r) vs. few with high investment (K) |
| `sexual_selection_examples` | T3 | Peacock train, bird-of-paradise displays, deer antlers — Darwin's secondary mechanism |

### Senses + specialized perception (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `echolocation_bats_dolphins` | T2 | Bats and dolphins navigate via ultrasonic echoes |
| `electroreception_basic` | T3 | Sharks (ampullae of Lorenzini), platypus (bill), electric fish |
| `magnetoreception_birds` | T3 | Migratory birds use Earth's magnetic field; mechanism partly cryptochrome in retina |
| `dog_olfaction_extreme` | T2 | Dogs have ~300M olfactory receptors vs. human ~6M; 10,000-100,000× more sensitive |
| `bird_uv_vision` | T3 | Many birds see UV light; flowers + plumage have UV patterns invisible to humans |
| `snake_heat_pits` | T3 | Pit vipers detect infrared via specialized organs between eye and nostril |
| `mantis_shrimp_color` | T3 | 16 types of color photoreceptors (humans have 3) — but actual color discrimination still researched |
| `elephant_infrasound` | T3 | Communicate via sub-20Hz infrasound over miles; detect through feet |
| `cetacean_hearing` | T3 | Whale lower jaws have fat-filled channel that conducts sound to inner ear |
| `electric_eel_voltage` | T3 | Up to 860 volts (recent finding — *Electrophorus voltai*, 2019 discovery) |

### Weird specific animals (T2-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `tardigrade_extremophile` | T3 | Cryptobiosis; survives vacuum, radiation, near-absolute-zero, boiling water |
| `axolotl_regeneration` | T3 | Regrows limbs, heart tissue, parts of brain; neotenic (keeps larval features) |
| `immortal_jellyfish` | T4 | *Turritopsis dohrnii* — reverts to polyp stage; biologically "immortal" if conditions allow |
| `mantis_shrimp_punch` | T3 | Smasher type: punch acceleration faster than a .22 bullet; cavitation creates flash + sound |
| `mimic_octopus` | T4 | *Thaumoctopus mimicus* (1998) — actively imitates 15+ species including lionfish, flatfish, sea snake |
| `glass_frog_transparency` | T4 | Centrolenidae — abdominal skin transparent; recent research on red-blood-cell sequestration during sleep |
| `naked_mole_rat` | T4 | Cancer resistant, eusocial (queen + workers), lives ~30 years (vs. mouse ~3), pain insensitivity |
| `hagfish_slime` | T3 | Releases gel that can fill 5-gallon bucket in seconds; clogs predator gills |
| `pistol_shrimp_snap` | T3 | Snap creates cavitation bubble that briefly reaches 4,700°C (sun's surface ~5,500°C) |
| `peacock_spider` | T3 | Maratus genus, Australia, 0.5cm jumping spiders with iridescent display + dance |
| `blue_whale_largest` | T1 | Largest known animal ever — up to 30m, 200 tonnes; tongue can weigh as much as an elephant |
| `etruscan_shrew_smallest` | T3 | Smallest mammal by mass — 1.8g, heart 1,500 bpm |
| `bee_hummingbird` | T2 | Smallest bird — 5cm, 2g; Cuba |
| `colossal_squid_eyes` | T4 | Largest eyes in animal kingdom — basketball-sized; *Mesonychoteuthis hamiltoni* |
| `lyrebird_mimicry` | T3 | Australian lyrebird mimics chainsaws, car alarms, other birds with extreme accuracy |
| `archerfish_aim` | T3 | Spits water at insects above water, correcting for refraction |

### Behaviors (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `monarch_migration` | T2 | 3,000-mile Mexico-to-Canada multi-generational migration |
| `arctic_tern_migration` | T3 | Pole-to-pole — longest migration on Earth, ~44,000 miles annually |
| `salmon_natal_return` | T3 | Return to natal stream to spawn; magnetic + olfactory navigation |
| `lekking_behavior` | T4 | Males gather + display competitively for female choice — sage grouse, manakins, kakapo |
| `eusociality` | T3 | Reproductive division of labor + cooperative care — ants, bees, termites, naked mole rats |
| `tool_use_crows` | T3 | New Caledonian crows craft hooks from twigs; Aesop's fable test passed |
| `tool_use_octopus` | T3 | Coconut octopus uses shells as portable shelter — first documented invertebrate tool use |
| `elephant_mourning` | T3 | Documented investigation of bones of deceased herd members; grief-like behavior |
| `bee_waggle_dance` | T3 | Karl von Frisch decoded 1947 — dance angle + duration encodes direction + distance to nectar |
| `octopus_camouflage` | T3 | Chromatophores + iridophores + leucophores allow color change — yet octopuses are colorblind |

### Animal cognition (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `mirror_self_recognition` | T3 | Mark test passed by: chimps, dolphins, magpies, elephants, some others |
| `alex_african_grey` | T4 | Irene Pepperberg's research subject — Alex used ~100 words functionally, 1977-2007 |
| `koko_gorilla` | T4 | Francine Patterson's ASL research — Koko (1971-2018) used ~1,000 signs; nuance debated |
| `washoe_chimp` | T4 | Beatrix + Allen Gardner — first cross-fostered chimp ASL, ~350 signs (1965-2007) |
| `dolphin_culture` | T4 | Sponge-tool use transmitted vertically (mother→daughter) in Shark Bay bottlenoses |
| `crow_intelligence` | T4 | Caledonian crows make hooked tools; remember faces; pass tool-making to offspring |

### Defense mechanisms (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `skunk_spray` | T2 | Thiols (sulfur compounds) — distinguishable up to 1 mile |
| `opossum_thanatosis` | T3 | "Playing possum" — involuntary catatonic state with foul-smelling secretion |
| `pufferfish_tetrodotoxin` | T3 | Among most toxic neurotoxins; fugu requires licensed Japanese chef preparation |
| `monarch_milkweed_toxicity` | T3 | Caterpillars sequester cardenolides from milkweed → adults toxic to predators |
| `electric_eel_shock` | T3 | Up to 860V (2019 *E. voltai* finding); shock used to stun prey + defense |
| `bombardier_beetle` | T3 | Chemical defense — hydroquinone + hydrogen peroxide mixed on demand; expels at 100°C |

---

## Pillar 2 — Evolution + paleontology

### Geologic time + early life (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `first_life_3.5_billion` | T4 | Earliest fossil evidence ~3.5 billion years ago (Australian stromatolites) |
| `great_oxygenation_event` | T4 | ~2.4 billion years ago — cyanobacteria photosynthesis fundamentally changed atmosphere |
| `eras_periods_basic` | T3 | Paleozoic (542M-252M) → Mesozoic (252M-66M) → Cenozoic (66M-now) |
| `cambrian_explosion` | T3 | ~540M years ago — most major animal phyla appear in fossil record within ~25M years |
| `burgess_shale_discovery` | T4 | 1909 Walcott — Canadian Rockies — Cambrian fauna including Anomalocaris, Opabinia |

### Major Paleozoic periods (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `devonian_age_of_fishes` | T3 | 419-359M years ago — diversification of fishes; Tiktaalik (375M) first transitional tetrapod |
| `carboniferous_giants` | T3 | 359-299M — coal forests; Meganeura dragonfly 70cm wingspan; high atmospheric O2 |
| `permian_synapsids` | T3 | 299-252M — Dimetrodon NOT a dinosaur (synapsid, mammal ancestor); Gorgonops |
| `tiktaalik_transitional` | T4 | Neil Shubin 2004 Ellesmere Island — fish with proto-limbs; predicted location + age |

### Five mass extinctions (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `mass_extinctions_five` | T3 | The five: Ordovician, Devonian, Permian (worst), Triassic, K-Pg |
| `permian_great_dying` | T3 | 252M years ago — 95% marine + 70% terrestrial species lost; Siberian Traps volcanism |
| `triassic_jurassic_extinction` | T4 | ~200M — opened ecological space for dinosaur radiation |
| `kpg_extinction_dinosaur` | T2 | 66M years ago — Chicxulub asteroid (Yucatán); iridium layer evidence (Alvarez 1980) |
| `chicxulub_evidence` | T4 | 1991 confirmation; 180km crater; debate continued vs. Deccan Traps volcanism contribution |

### Specific dinosaurs (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `t_rex_basic` | T2 | Late Cretaceous (68-66M), North America; ~12m, 9 tonnes; biggest known carnivore on land at time |
| `triceratops_basic` | T2 | Late Cretaceous; three horns + frill; coexisted with T. rex |
| `velociraptor_real` | T2 | 2m long, turkey-sized — Jurassic Park exaggerates; covered in feathers |
| `stegosaurus_plates` | T2 | Plates likely thermoregulation + display, NOT body armor as once thought |
| `brachiosaurus_neck` | T3 | Vertical neck posture debated; recent biomechanics suggests more horizontal |
| `spinosaurus_aquatic` | T3 | 2014 Ibrahim study — first known semi-aquatic dinosaur; recent paddle-tail discovery 2020 |
| `argentinosaurus_largest` | T3 | Largest known dinosaur — ~35m, ~75 tonnes; Cretaceous Argentina |
| `apatosaurus_brontosaurus` | T3 | "Brontosaurus" was sunk into Apatosaurus 1903; reinstated as separate genus 2015 |
| `feathered_dinosaurs_china` | T4 | 1990s+ Liaoning Province discoveries — Microraptor, Sinosauropteryx, definitive feather evidence |
| `archaeopteryx_first_bird` | T3 | 1861 Solnhofen, Germany; transitional theropod-to-bird; 12 specimens known |

### Mammalian + bird origins (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `morganucodon_first_mammal` | T4 | Among earliest known mammals — ~205M years ago; mouse-sized; nocturnal |
| `eutherian_radiation_after_kpg` | T4 | Placental mammals diversified after non-avian dinosaur extinction; "mammal age" Cenozoic |
| `whale_evolution_pakicetus` | T4 | Pakicetus (50M, land mammal, dog-sized) → Ambulocetus → Rodhocetus → modern cetaceans |
| `bird_dinosaur_evidence` | T3 | Feathers, hollow bones, three-fingered hand, semilunate wrist bone — clear lineage |

### Pleistocene megafauna (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `woolly_mammoth` | T2 | Mammuthus primigenius — extinct ~4,000 years ago (Wrangel Island holdouts); Siberia + N. America |
| `mastodon_vs_mammoth` | T3 | Different genus (Mammut), forest dweller, browser (vs. mammoth grazer); teeth distinguish |
| `smilodon_sabertooth` | T2 | Saber-toothed cat — 12-cm canines; hunted in groups; La Brea Tar Pits archive |
| `giant_ground_sloth` | T3 | Megatherium — elephant-sized ground-dweller; survived to 8,000 years ago in Americas |
| `short_faced_bear` | T3 | Arctodus simus — largest predatory mammal ever in N. America; cursorial pursuit hunter |
| `dire_wolf_real` | T3 | *Canis dirus* (recently reassigned to *Aenocyon dirus* 2021) — distinct from gray wolves |
| `glyptodon_armadillo` | T3 | Car-sized armadillo relative — bony domed carapace + tail club; survived to ~10,000 BP |
| `irish_elk_megaloceros` | T3 | "Irish Elk" — actually a deer; antlers up to 3.7m span; not exclusively Irish; extinct ~7,000 BP |
| `pleistocene_overkill_debate` | T4 | Paul Martin's 1967 overkill hypothesis vs. climate-driven extinction — both sides argued |

### Famous paleontologists + fossils (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `mary_anning` | T3 | Self-taught English (1799-1847), Lyme Regis — first complete ichthyosaur 1811, first plesiosaur 1823, first pterosaur 1828 |
| `cope_marsh_bone_wars` | T4 | Edward Cope vs. Othniel Marsh, 1870s-1890s — discovered ~150 dinosaur species, ruined each other |
| `richard_owen_dinosauria` | T4 | Coined "Dinosauria" 1842; founded London Natural History Museum 1881; competed with Darwin |
| `jack_horner_maiasaura` | T4 | 1978 discovered first dinosaur nesting site (Montana); Maiasaura "good mother lizard"; revolutionized dinosaur parenting view |
| `lucy_australopithecus` | T3 | 1974, Hadar Ethiopia, Donald Johanson — 3.2M years old, ~40% complete; named after Beatles song |
| `sue_t_rex` | T3 | 1990 Sue Hendrickson, S. Dakota — largest + most complete T. rex; legal saga; Field Museum Chicago |

### Human evolution timeline (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `sahelanthropus_oldest_hominin` | T4 | ~7M years ago — Chad, possible bipedal; status debated |
| `australopithecus_basic` | T3 | "Lucy" species (afarensis) ~3.2M; clear bipedal walker |
| `homo_habilis` | T3 | First Homo, ~2.4M years ago — first stone tools (Oldowan industry) |
| `homo_erectus_tools_fire` | T3 | ~1.9M-110K BP — Acheulean hand axes; controlled fire ~1M BP; first leave Africa |
| `neanderthal_basic` | T3 | *Homo neanderthalensis* — Europe + W. Asia ~400K-40K BP; ~2% DNA in modern non-African humans |
| `denisovan_discovery` | T4 | 2008 Denisova cave finger bone DNA — separate lineage; contributed DNA especially to Melanesians |
| `homo_sapiens_origin` | T3 | ~300K BP, Africa; Out-of-Africa II ~70K BP coastal route; replaced/interbred archaic humans |
| `human_evolution_no_ladder` | T4 | Bush, not ladder — many hominin species coexisted; common popular misconception |

### The 6th extinction (T4-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `anthropocene_debate` | T5 | Proposed geological epoch (informal/contested formal status); various proposed start dates (mid-20th century plutonium, 1610, etc.) |
| `sixth_extinction_kolbert` | T5 | Elizabeth Kolbert 2014 book + Pulitzer; argues we are in the 6th mass extinction |
| `iucn_red_list` | T4 | International Union for Conservation of Nature — Least Concern → Near Threatened → Vulnerable → Endangered → Critically Endangered → Extinct in Wild → Extinct |

---

## Pillar 3 — Domestication + husbandry

### The founder domesticates (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `dog_first_domesticate` | T2 | ~15,000-40,000 BP — multiple origin debate (one vs. multiple events); from gray wolf |
| `sheep_goat_dates` | T3 | ~11,000 BP, Fertile Crescent — among first agricultural domesticates |
| `cattle_origins_multiple` | T3 | ~10,500 BP — independent domestication: Near East (taurine), Indian subcontinent (zebu), African |
| `pig_domestication_independent` | T3 | ~9,000 BP — Anatolia + East Asia independent; from wild boar (Sus scrofa) |
| `cat_self_domestication` | T3 | ~9,500 BP Cyprus burial + ~7,500 BP Egypt — likely human-tolerant cats moved in with stored grain |
| `horse_botai_5500_bp` | T3 | ~5,500 BP Botai culture Kazakhstan; revolutionized transport + warfare |
| `chicken_red_junglefowl` | T3 | ~5,500 BP Southeast Asia from red junglefowl (Gallus gallus); ~30 billion alive today |
| `domesticate_dates_14_main` | T4 | Jared Diamond's list of 14 major large-animal domesticates and their distribution |
| `reindeer_late_domesticate` | T4 | ~2,000 BP, Siberian Sami + others — most recent large-animal domesticate |
| `honeybee_egyptian` | T3 | ~6,000 BP Egyptian hieroglyphics; managed hives; honey + wax + propolis |

### Cattle breeds + products (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `angus_cattle` | T2 | Scotland — black, polled (hornless), most popular US beef breed |
| `hereford_cattle` | T3 | Herefordshire England — white face, red body; foundational US ranching breed |
| `jersey_cattle` | T2 | Channel Islands — small, fawn-colored, highest butterfat in milk |
| `holstein_milk_production` | T2 | Black-and-white from Friesland — most productive dairy breed (~10,000 gallons/year/cow) |
| `wagyu_kobe_distinction` | T3 | Wagyu = the breed; Kobe = specific brand from Hyogo Prefecture only |
| `brahman_heat_tolerant` | T3 | Indian Zebu origin; humped, heat-tolerant; key in southern US ranching |
| `texas_longhorn_heritage` | T3 | Spanish Andalusian descent; near-extinct ~1900 → restored; iconic American cattle |
| `cattle_estrus_artificial_insem` | T4 | First commercial AI 1936 USDA; revolutionized genetics + production |

### Sheep + wool (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `merino_wool_premium` | T2 | Spanish origin → Australian dominance; finest wool, ~17-22 micrometers |
| `suffolk_sheep_meat` | T3 | English breed — black face/legs, white wool, primary meat breed |
| `dorset_dairy_meat` | T3 | English breed — out-of-season breeder, used for milk + meat + wool |
| `karakul_persian_lamb` | T4 | Central Asia origin; Persian lamb / Astrakhan fur from unborn or newborn lambs (contested practice) |
| `wool_grades_micrometers` | T3 | Superfine (<18µm) → fine → medium → strong; measured by fiber diameter |

### Pig breeds (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `yorkshire_industrial_pork` | T2 | English origin; white, lean; basis for most commercial pork worldwide |
| `berkshire_heritage_pork` | T3 | English heritage; black with white points; favored for charcuterie |
| `tamworth_red` | T3 | Irish/English red ginger-colored heritage breed — bacon pig |
| `iberico_acorn_fed` | T3 | Spanish *Dehesa* oak savanna; *Pata Negra* / *Bellota* grade — acorn-finished |
| `mangalitsa_wooly` | T3 | Hungarian curly-haired "wooly pig"; near-extinct → restored; high fat marbling |

### Chicken breeds (T2)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `leghorn_white_eggs` | T2 | Italian origin; white feathers + white eggs; primary commercial layer worldwide |
| `rhode_island_red` | T2 | American Rhode Island origin 1854; dual purpose; brown eggs |
| `plymouth_rock` | T2 | American 1869; barred plumage; dual purpose; heritage |
| `cornish_broiler_breed` | T3 | English origin; foundation of modern broiler (meat) chicken |
| `silkie_ornamental` | T3 | Chinese origin; fluffy plumage, black skin/bones, 5 toes (most chickens 4) |
| `egg_color_genetics` | T3 | Earlobe color predicts egg color in most breeds (white earlobe → white egg) |

### Dog breeds (T1-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `dog_groups_akc` | T2 | AKC 7 groups: Sporting, Hound, Working, Terrier, Toy, Non-Sporting, Herding |
| `border_collie_intelligence` | T2 | Most intelligent breed per Stanley Coren rankings; herding instinct |
| `german_shepherd_versatility` | T2 | Police, military, service, herding origins — Max von Stephanitz 1899 |
| `belgian_malinois_military` | T3 | Most common modern US military working dog (Cairo on bin Laden raid) |
| `siberian_husky_sled` | T2 | Chukchi origin — Iditarod heritage; thick double coat |
| `labrador_retriever_popularity` | T2 | Most popular AKC breed for 30+ years until 2022 (French Bulldog took #1) |
| `dachshund_badger_dog` | T2 | German "badger dog" — bred to enter setts (badger burrows) |
| `pit_bull_terminology` | T3 | "Pit bull" not single breed — American Pit Bull Terrier, American Staffordshire, Staffordshire Bull |
| `brachycephalic_concerns` | T3 | Bulldogs, pugs — flat-faced breeds with breathing/birthing/health problems from extreme breeding |

### Horse breeds (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `arabian_oldest_registered` | T3 | Bedouin desert origins; oldest documented registered breed; foundation of many modern breeds |
| `thoroughbred_racing` | T2 | English origin 1600s — Arabian crossed with English mares; basis of modern racing |
| `quarter_horse_sprint` | T2 | American — fastest over short distances ("quarter-mile"); cattle work + racing |
| `clydesdale_draft` | T2 | Scottish draft breed; Budweiser association; ~1 tonne |
| `shire_largest_horse` | T3 | English draft; among tallest + heaviest horse breeds; medieval war horse origin |
| `appaloosa_nez_perce` | T3 | American breed selectively bred by Nez Perce tribe; spotted coat |
| `mustang_american_feral` | T3 | Feral descendants of Spanish horses; BLM-managed populations on public lands |

### Milk + dairy (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `milk_species_basic` | T2 | Cow, goat, sheep, buffalo (Indian mozzarella), yak, camel, reindeer all milked |
| `goat_milk_smaller_globules` | T3 | Smaller fat globules → easier to digest; closer to human milk pH |
| `sheep_milk_highest_fat` | T3 | ~7% fat (cow ~3.5%); used for Roquefort, Pecorino, feta historically |
| `buffalo_milk_mozzarella` | T3 | Italian water buffalo (Mediterranea breed) — DOP mozzarella di bufala |
| `camel_milk_diabetic` | T4 | Lower lactose; insulin-like protein researched for diabetic compatibility |
| `a2_milk_debate` | T4 | A1 vs A2 beta-casein hypothesis — proponents claim A2 better tolerated; mainstream research mixed (contested) |

### Egg classifications (T2)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `egg_grade_usda` | T2 | AA / A / B — air cell size, white firmness, yolk centering |
| `cage_free_vs_pasture_raised` | T2 | Cage-free (still indoor) vs. free-range (some outdoor access) vs. pasture-raised (most outdoor) |
| `brown_vs_white_eggs` | T2 | Shell color = breed of hen, no nutritional difference |
| `egg_size_classifications` | T2 | Jumbo → Extra Large → Large → Medium → Small → Peewee (weight per dozen) |

### Welfare frameworks (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `five_freedoms_brambell_1965` | T3 | UK Farm Animal Welfare Council: freedom from hunger, discomfort, pain, fear, expression of normal behavior |
| `animal_welfare_approved` | T3 | Whole Foods / A Greener World — highest welfare certification on most metrics |
| `certified_humane_program` | T3 | Humane Farm Animal Care non-profit; widely-adopted certification |
| `global_animal_partnership_steps` | T3 | Whole Foods 5+1 step ratings (Step 1 → Step 5+, no-cage to pasture-centered) |

### Industrial vs. heritage (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `cafo_concerns` | T3 | Concentrated Animal Feeding Operations — manure runoff, antibiotic use, welfare; real concerns + the cost/food-access tradeoff |
| `joel_salatin_polyface` | T4 | Virginia farm — multispecies rotational grazing; high regenerative practice profile |
| `allan_savory_holistic` | T4 | Holistic Planned Grazing — controversial claims about reversing desertification; research mixed |
| `regenerative_ag_basics` | T4 | Soil-building practices: cover crops, integrated livestock, minimal tillage, biodiversity |
| `heritage_breed_conservation` | T4 | The Livestock Conservancy + SVF Foundation preserve genetic diversity (Mulefoot pig, etc.) |
| `holstein_vs_traditional_dairy` | T4 | Modern Holstein produces ~10x what 1950s cow did; productivity vs. longevity tradeoffs |
| `corn_finished_vs_grass_fed` | T3 | Different omega-6/3 ratios, beta-carotene levels, marbling; production cost differences |

### Working animals + livestock specialties (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `falconry_unesco_intangible` | T3 | UNESCO Intangible Heritage 2016 — joint nomination by 18 countries; ancient sport, modern practice |
| `langstroth_hive_1851` | T3 | Lorenzo Langstroth — movable frames + "bee space" 3/8 inch discovery — revolution in beekeeping |
| `colony_collapse_2006` | T3 | First widely reported 2006 — multifactorial: pesticides (neonicotinoids), Varroa mite, pathogens, nutrition |
| `sheep_dog_border_collie` | T2 | Border Collies — herding via "eye"; Welsh + Scottish/Northumbrian heritage |
| `livestock_guardian_dogs` | T3 | Great Pyrenees, Anatolian Shepherd, Maremma — protect flocks from predators (bonded with sheep from puppyhood) |
| `iditarod_sled_dogs` | T2 | 1,000-mile Anchorage-to-Nome race; founded 1973 by Joe Redington Sr.; commemorates 1925 serum run |
| `mongolian_horse_culture` | T3 | ~3 horses per Mongolian; Genghis Khan's mounted archers — multiple remounts allowed unmatched range |

### Aquaculture (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `salmon_aquaculture_norway` | T3 | Norway invented commercial Atlantic salmon farming 1970s; now 1.5M tons/year |
| `tilapia_most_farmed_fish` | T3 | Most farmed fish globally; native to Nile (one of oldest aquaculture species, Egyptian art shows) |
| `oyster_restoration_chesapeake` | T3 | Chesapeake Bay oyster population <1% of historic; restoration since 1990s |
| `shrimp_mangrove_destruction` | T3 | Southeast Asian shrimp farms cleared ~38% of mangrove forests 1980-2000 (contested practice) |

---

## Pillar 4 — Hunting, harvest, butchery

### Traditional + modern hunting (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `atlatl_spear_thrower` | T3 | Spear-thrower predating bow + arrow; ~30,000 BP; mechanical advantage doubles throw distance |
| `bow_arrow_origins` | T2 | ~70,000 BP earliest evidence (South Africa); revolutionized hunting + warfare |
| `buffalo_jump_pishkun` | T3 | Plains Indian drive-hunting technique; Head-Smashed-In Buffalo Jump (Alberta, UNESCO 1981) |
| `inuit_kayak_seal_hunt` | T3 | Sealskin clothing waterproof; harpoon + float technology; rotation of meat sharing |
| `pit_trap_falling` | T3 | Camouflaged pit + stake; among oldest hunting technologies; depicted in Lascaux cave art |
| `compound_bow_modern` | T2 | Holless Allen 1966 — cam + cable system; lets-off at peak draw; modern hunting standard |

### Conservation model (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `pittman_robertson_1937` | T4 | 11% federal excise tax on firearms + ammo → wildlife restoration; largest single source of conservation funding |
| `duck_stamp_1934` | T4 | Federal Duck Stamp Act — waterfowl hunting license stamp funds wetland conservation |
| `lacey_act_1900` | T4 | First federal wildlife law — banned trafficking of illegally taken wildlife; transformed conservation |
| `boone_crockett_club_1887` | T4 | Founded by Theodore Roosevelt + George Bird Grinnell; conservation through ethical hunting |
| `north_american_conservation_model` | T4 | 7 principles: public ownership, prohibition of commerce in dead wildlife, allocation by law, kill for legit purpose, international resource, science-based management, democracy of hunting |
| `t_roosevelt_230m_acres` | T3 | Established 5 national parks, 18 national monuments, 51 wildlife refuges, ~230M acres total |
| `aldo_leopold_sand_county` | T4 | *A Sand County Almanac* 1949 — "land ethic"; modern environmental philosophy foundation |

### Famous extinctions from hunting (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `dodo_extinction_1681` | T3 | Mauritius — flightless, fearless; sailors, dogs, pigs; ~80 years from discovery to extinction |
| `passenger_pigeon_martha_1914` | T3 | Once billions ("blot out the sky"); last died 1914 Cincinnati Zoo (Martha); commercial hunting + habitat loss |
| `great_auk_1844` | T3 | Last pair killed Eldey Iceland 1844 — collected for museum specimens; commercial feather hunting |
| `carolina_parakeet_1918` | T4 | Last died Cincinnati Zoo 1918 (Incas); only North American native parrot |
| `thylacine_1936` | T3 | Tasmanian tiger — last (Benjamin) died Hobart Zoo 1936; government bounties + sheep-killing reputation |
| `steller_sea_cow_1768` | T4 | Sirenian, 27 years from European discovery (1741) to extinction; hunted by fur traders for meat |
| `western_black_rhino_2011` | T4 | Declared extinct 2011 — poaching for horn; 4 black rhino subspecies, only 3 remain |
| `cecil_lion_2015` | T4 | Zimbabwe — illegal trophy hunting case; renewed trophy-hunting debate |

### Wildlife restoration success (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `white_tailed_deer_restoration` | T3 | <500,000 in 1900 → ~30M today via conservation funding + harvest regulations |
| `wild_turkey_restoration` | T3 | <200,000 in 1930 → ~7M today (trap-and-transfer programs) |
| `american_bison_recovery` | T3 | ~30M pre-1800 → <1,000 in 1884 → ~500,000 today (mostly conservation herds) |
| `wood_duck_restoration` | T4 | Near-extinct 1900 → restored via Migratory Bird Treaty Act 1918 + nest boxes |
| `wolf_yellowstone_reintroduction` | T4 | 1995 reintroduction; trophic cascade research (Ripple + Beschta); contested elk-population effects |

### Whaling history (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `basque_medieval_whaling` | T4 | Earliest documented commercial whaling — Bay of Biscay 11th century onward |
| `american_yankee_whaling` | T3 | 1700s-1800s peak; Nantucket + New Bedford fleets; Moby Dick reflects this era |
| `petroleum_replaces_whale_oil` | T4 | 1859 Drake well, Pennsylvania — kerosene from petroleum displaced sperm whale oil for lighting |
| `iwc_1986_moratorium` | T3 | International Whaling Commission halt on commercial whaling; exemptions for aboriginal subsistence + "scientific" |
| `makah_whaling_treaty_rights` | T4 | Washington State Makah Nation — 1855 treaty hunting right; contested 1999 hunt; ongoing legal debate |

### Butchery primals + cuts (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `beef_primals_8` | T2 | Chuck, rib, loin, round, brisket, plate, flank, shank — 8 main US primals |
| `pork_primals_basic` | T2 | Shoulder, loin, belly, ham, side ribs, jowl |
| `lamb_primals_basic` | T2 | Shoulder, rib, loin, leg + breast, neck |
| `venison_field_dressing` | T3 | Gut removal within hours; hanging to age 7-14 days at proper temp; quartering for transport |
| `dry_aging_beef` | T3 | 14-45 days controlled humidity + temp; enzymes tenderize; concentrates flavor; weight loss |
| `wet_aging_basic` | T3 | Vacuum-sealed; cheaper than dry-aging; faster turnover; less flavor concentration |
| `charcuterie_traditions` | T3 | Prosciutto (Italian), jamón Ibérico (Spanish), salami varieties, headcheese, blood sausage, mortadella |
| `nose_to_tail_movement` | T3 | Fergus Henderson *Nose to Tail Eating* 1999 — using whole animal (tongue, kidney, heart, marrow, brain) |

### Religious slaughter (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `kosher_schechita` | T3 | Trained shochet; chalaf knife (smooth, sharp, no nicks); single cut severs trachea + esophagus + carotid arteries + vagus nerve |
| `halal_dhabihah` | T3 | Similar single-cut method; name of Allah invoked; animal facing Mecca traditionally |
| `stunning_debate` | T4 | EU/UK debate — required pre-stunning vs. religious exemptions; contested |

### Hunting ethics + contested topics (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `fair_chase_doctrine` | T3 | Animal must have realistic chance to escape; no high-fence canned hunts; Boone & Crockett standard |
| `quick_kill_ethical_hunting` | T3 | Shot placement, weapon selection, knowing limits — minimize suffering |
| `no_waste_principle` | T3 | Take what you use, use what you take; cultural across hunting traditions |
| `trophy_hunting_debate` | T4 | Funds conservation in some African models (CAMPFIRE Zimbabwe) vs. ethical concerns |
| `indigenous_whaling_rights` | T4 | Makah, Inuit, Faroe Islanders — cultural rights vs. species protection (contested) |
| `fur_trade_history` | T3 | Hudson's Bay Company 1670; North American beaver (~200M trapped 1600-1900); Siberian sable expansion |
| `modern_fur_debate` | T4 | PETA campaigns vs. trapping traditions + indigenous economies; faux-fur environmental concerns |

---

## Pillar 5 — Animals in human culture

### Egyptian animal gods (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `anubis_jackal` | T2 | Embalming + afterlife god; jackal-headed; oversaw weighing of the heart |
| `bastet_cat` | T2 | Protection + home + cats; cat-headed (originally lioness); Bubastis cult center |
| `horus_falcon` | T2 | Kingship + sky god; falcon-headed; Eye of Horus protective symbol |
| `sobek_crocodile` | T3 | Nile + military; crocodile-headed; Faiyum cult center |
| `sekhmet_lioness` | T3 | War + healing + plagues; lion-headed; balance to Bastet |
| `thoth_ibis` | T3 | Writing + wisdom + moon; ibis-headed (sometimes baboon); recorded weighing of heart |
| `apis_bull` | T3 | Sacred bull of Memphis; living incarnation, mummified at death |
| `egyptian_cat_mummies` | T3 | Millions of cat mummies; Bastet temple sacrifices; cats so revered killing one was capital crime |

### Greek + Roman myth (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `pegasus_winged_horse` | T2 | Greek; born from Medusa's blood; Bellerophon rode him to slay Chimera |
| `cerberus_three_headed` | T2 | Greek; three-headed dog guarding Hades' entrance |
| `minotaur_crete` | T2 | Bull-headed; King Minos's labyrinth; Theseus killed him |
| `centaur_half_horse` | T2 | Human torso + horse body; mostly savage in myth except Chiron the wise tutor |
| `nemean_lion` | T3 | First labor of Heracles; impervious hide → he wore its skin |
| `roman_haruspicy` | T3 | Etruscan-derived divination from animal entrails (esp. liver); state-religion practice |
| `roman_eagle_aquila` | T3 | Standard of Roman legions; sacred to Jupiter; loss in battle was supreme disgrace |

### Norse myth (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `sleipnir_8_legged_horse` | T2 | Odin's eight-legged steed; born of Loki + the stallion Svaðilfari |
| `huginn_muninn_ravens` | T2 | Odin's ravens — "Thought" + "Memory" — fly the world and report back |
| `fenrir_wolf_son_of_loki` | T3 | Bound until Ragnarök, when he will kill Odin; the Aesir tricked him into the binding |
| `jormungandr_world_serpent` | T3 | Loki's son; encircles the world biting his own tail; Thor's eternal enemy |
| `ratatoskr_squirrel` | T3 | Squirrel carrying insults between eagle atop Yggdrasil and dragon at root |
| `audhumla_primordial_cow` | T3 | Primordial cow that licked the first god (Buri) from salt ice |

### Hindu animal symbolism (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `hanuman_monkey_god` | T2 | Strength + devotion; helped Rama recover Sita; sometimes seen as ideal devotee |
| `ganesha_elephant_headed` | T2 | Remover of obstacles, patron of arts + sciences; vahana (vehicle) is the mouse Mushika |
| `nandi_shivas_bull` | T3 | Shiva's vahana; always faces the Shiva linga in temples |
| `garuda_vishnus_eagle` | T3 | Vishnu's mount; enemy of serpents; appears in Indonesian + Thai national symbols |
| `cow_sacred_mother` | T2 | *Gau mata* — Mother Cow; protection of cows central to Hindu practice; affects modern Indian politics |
| `naga_serpent_deities` | T3 | Serpent beings; protect water + treasures; depicted with multi-headed cobra hoods |

### Chinese zodiac + symbolism (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `chinese_zodiac_12` | T2 | Rat, ox, tiger, rabbit, dragon, snake, horse, goat, monkey, rooster, dog, pig |
| `jade_emperor_race_legend` | T3 | Origin myth — Jade Emperor's race; rat tricked ox to win; cat fell in river (cats not in zodiac) |
| `chinese_dragon_benevolent` | T2 | Lung/long — bringing rain + prosperity (vs. Western dragon = evil); imperial symbol |
| `phoenix_fenghuang_china` | T3 | Female counterpart to dragon; symbol of empress + virtue |
| `chinese_tiger_four_directions` | T3 | White Tiger of the West — one of Four Symbols (Azure Dragon East, Vermilion Bird South, Black Tortoise North) |

### Native American animal symbolism (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `thunderbird_widespread` | T3 | Supernatural bird across many North American tribes; thunder = wing beats |
| `raven_pacific_northwest` | T3 | Trickster + creator; Tlingit, Haida, Tsimshian; stole sun from chief to give light to world |
| `coyote_trickster_southwest` | T3 | Plains + Southwest — wise fool, both creator + chaos-bringer |
| `eagle_plains_tribes` | T3 | Sacred to most tribes; feathers ceremonial; Eagle Feather Law allows federally recognized tribes to possess |
| `bear_medicine` | T3 | Many tribes — bear represents healing, introspection; bear medicine societies |
| `buffalo_plains_nations` | T2 | Center of Plains life — food, shelter (tipis), tools, clothing; ~30M to ~1,000 by 1884 |

### Christian animal symbolism (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `lamb_of_god_agnus_dei` | T2 | Christ as sacrifice; Passover lamb fulfillment; John 1:29 |
| `dove_holy_spirit` | T2 | Baptism of Jesus — Spirit descends as dove; Noah's flood end (olive branch) |
| `lion_of_judah` | T2 | Tribal symbol of Judah → Christ as conquering king (Revelation 5:5) |
| `fish_ichthys_early_christian` | T3 | Acrostic ΙΧΘΥΣ = "Jesus Christ God's Son Savior"; secret-identification symbol under persecution |
| `four_evangelists_creatures` | T3 | Matthew/man, Mark/lion, Luke/ox, John/eagle (Ezekiel + Revelation tetramorph) |
| `serpent_sin_devil` | T3 | Genesis serpent in Eden; brass serpent of Moses (Numbers 21) as type of Christ |
| `peacock_resurrection` | T3 | Early Christian symbol — incorruptible flesh + many-eyed tail = all-seeing God |
| `pelican_eucharist` | T4 | Medieval belief pelicans pierced their breast to feed young → symbol of Christ's sacrifice |

### Famous historical animals (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `bucephalus_alexander` | T3 | Alexander's horse — tamed at age 12 by noting it feared its own shadow; carried him through Persia |
| `hannibal_war_elephants` | T3 | 218 BC crossed Alps with ~37 elephants; most died en route; surviving few terrified Romans |
| `caligula_incitatus` | T4 | Emperor's horse — fed gold-flecked oats; consul rumor uncertain (Suetonius reported as scandal) |
| `marengo_napoleon` | T3 | Arabian stallion; carried Napoleon at Marengo (1800), Austerlitz, Jena, Wagram, Waterloo |
| `trigger_roy_rogers` | T3 | Palomino stallion; "Smartest Horse in the Movies"; stuffed + mounted in Roy Rogers Museum |
| `sergeant_stubby_wwi` | T3 | Most decorated dog of WWI; captured German spy; saved unit from gas attack via early warning |
| `hachiko_loyalty` | T2 | Akita who waited 9 years at Shibuya Station after master's death (1925-1935) |
| `laika_first_space_dog` | T3 | Soviet Sputnik 2 (Nov 1957); died within hours of launch; first living being in orbit |
| `cher_ami_pigeon_wwi` | T4 | Carrier pigeon — saved 194 of "Lost Battalion"; flew 25 miles with bullet wound, lost eye + leg |
| `wojtek_polish_army_bear` | T4 | Brown bear (1942 Iran orphan); officially enlisted in Polish 22nd Artillery Supply Co.; carried ammo at Monte Cassino |
| `smoky_wwii_terrier` | T4 | 4-lb Yorkie pulled communication wire through 70-ft conduit; therapy dog precedent |
| `balto_togo_serum_run` | T3 | 1925 — diphtheria serum to Nome Alaska via dogsled relay; Togo did longest leg, Balto got fame |

### Pet history (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `egyptian_pet_cats` | T2 | Earliest documented cat-human pet relationship; mummified cats; killing cat = capital crime |
| `roman_dog_companionship` | T3 | "Cave Canem" mosaics; small lapdogs documented in Pompeii; companion species established |
| `chinese_koi_carp_breeding` | T3 | Selective breeding for color ~1000 BP from common carp; modern koi varieties Edo-period Japan refinement |
| `victorian_cat_fancy` | T3 | First Crystal Palace Cat Show 1871; Harrison Weir established breed standards; modern fancy origin |
| `westminster_dog_show_1877` | T3 | Second-longest continuously held US sporting event (after Kentucky Derby) |
| `crufts_1891_uk` | T3 | Charles Cruft, dog food salesman; largest dog show in the world; held at NEC Birmingham |
| `modern_pet_industry_size` | T3 | ~$140B/year US pet industry (2023); ~67% US households own pets |

### Animal welfare history (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `martins_act_1822_uk` | T4 | First animal cruelty law — UK Cruel Treatment of Cattle Act; Richard Martin "Humanity Dick" |
| `rspca_1824_founded` | T4 | World's first animal welfare charity; royal patronage 1840; predates child welfare orgs |
| `henry_bergh_aspca_1866` | T3 | New York — observed dog being beaten; founded ASPCA; got first US anti-cruelty law passed |
| `animal_welfare_act_1966_us` | T4 | Federal regulation of treatment in research + commercial transport; multiple amendments since |
| `peter_singer_animal_liberation_1975` | T4 | Utilitarian argument from suffering; popularized "speciesism"; founded modern animal-rights philosophy |
| `peta_1980_founded` | T4 | Founded by Ingrid Newkirk + Alex Pacheco; Silver Spring monkey case sparked movement |

### Bullfighting + animal sports (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `bullfighting_spain` | T3 | Spanish corrida — six stages; banned in Catalonia 2010, Balearics 2017; ongoing political debate |
| `portuguese_bullfighting_distinction` | T4 | Cavaleiro on horseback; bull NOT killed in arena (slaughtered after if killed at all) |
| `cockfighting_global_history` | T3 | Ancient Greek/Persian roots; modern Philippine *sabong* legal industry; banned across US |
| `dog_fighting_us_felony` | T4 | Felony all 50 states (2007); Animal Welfare Act covers; Vick case 2007 raised awareness |
| `fox_hunting_uk_ban` | T4 | Hunting Act 2004 banned hunting wild mammals with dogs; traditional drag-hunting continues |

### Equestrian + animal sports (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `kentucky_derby_1875` | T3 | Oldest continuously held US sporting event; "Run for the Roses"; first Saturday in May |
| `triple_crown_horse_racing` | T3 | Kentucky Derby + Preakness + Belmont Stakes; 13 horses won 1919-2018 |
| `secretariat_1973` | T3 | Won Triple Crown by 31 lengths at Belmont; record stands; 132 lbs heart (3x normal) |
| `polo_persian_origin` | T3 | Originated ~6th century BC Persia (chovgan); spread India → British India → world |
| `dressage_olympic` | T3 | "Highest expression of horse training"; Olympic since 1912; FEI governance |
| `iditarod_1973_redington` | T3 | Joe Redington Sr. founded; ~1,000 miles Anchorage-Nome; honors 1925 serum run |
| `falconry_status_symbol` | T3 | Medieval European rank: emperor=eagle, king=gyrfalcon, prince=peregrine, baron=buzzard |

### Working partnerships (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `cavalry_history_world` | T3 | Mongols revolutionized via composite recurve bow from horseback; Western European knights via stirrup |
| `medieval_warhorse_destrier` | T3 | Heavy warhorse — Shire/Percheron ancestors; carried knight in full plate armor |
| `mongol_horse_archery` | T3 | Each warrior had 3-5 mounts; ate horsemilk yogurt; could fire 12 arrows/minute at gallop |
| `british_imperial_camel_corps` | T4 | WWI Egyptian + Palestinian theaters; ~4,150 men + 4,800 camels; disbanded 1919 |
| `pony_express_1860_61` | T3 | 18 months operational St. Louis-Sacramento; transcontinental telegraph 1861 ended it |
| `military_working_dogs_modern` | T3 | Belgian Malinois + German Shepherds dominant; military rank (above handler); Cairo on bin Laden raid |
| `guide_dog_origins_1916` | T3 | First German guide dog training school after WWI for blinded veterans; Seeing Eye 1929 US (Morris Frank) |
| `search_rescue_dogs_avalanche` | T3 | Saint Bernards Swiss origin (Great St. Bernard Pass monks); modern Belgian Malinois popular |
| `medical_detection_dogs` | T4 | Cancer detection (Penn Vet, Medical Detection Dogs UK); seizure alert; diabetic alert; COVID detection |
| `service_animal_ada_1990` | T3 | Americans with Disabilities Act — service animal definition; emotional support animals NOT covered same way |

---

## Per-tier targets

| Tier | Pillar 1 (Biology) | Pillar 2 (Evolution) | Pillar 3 (Husbandry) | Pillar 4 (Hunt/Butcher) | Pillar 5 (Culture) | **Total** |
|---|---:|---:|---:|---:|---:|---:|
| T1 | 150 | 50 | 150 | 100 | 150 | **600** |
| T2 | 200 | 150 | 200 | 150 | 200 | **900** |
| T3 | 200 | 250 | 200 | 200 | 250 | **1100** |
| T4 | 100 | 200 | 150 | 150 | 200 | **800** |
| T5 | 50 | 150 | 100 | 100 | 100 | **500** |
| **Total** | **700** | **800** | **800** | **700** | **900** | **~3900** |

Every tier ≥100 floor (well above). Pillar 5 (culture/myth) heaviest since it spans T2-T5 evenly. Evolution + paleontology pillar 2 heaviest at T3-T5 (deep timeline is naturally upper-tier wonder).

## Generation approach

Same hybrid as cooking:

1. **Deterministic Python generators (~25%)**: cuisine-style attribution (animal → class, breed → species, dish → cuisine pattern), taxonomic-class identification, breed names, famous-animal attributions, geologic-period dates. ~1000 questions.
2. **LLM agents (~75%)**: biology depth, evolution, husbandry, hunting + butchery, culture, mythology + religious symbolism. ~3000 questions.
3. **Fact-check gate**: `validate_animal_facts.md` LLM job — species attributions, dates, taxonomic accuracy, religious traditions.
4. **Standard gates remain in full effect**: schema, length_parity (animal answer-outlier 1.6×), length_budget (animal per-tier), anti_rote, duplicate (0.85).

## What success looks like

- A T1 question helps a kid recognize what they just harvested (mammal vs. bird vs. reptile; a cow vs. a deer; chicken parts).
- A T2 question reveals a "didn't know that" — Lucy was named after a Beatles song; Hachiko waited 9 years; cats were so sacred in Egypt that killing one was capital crime.
- A T3 question makes the player respect an animal — naked mole rats live 30 years cancer-resistant; the mantis shrimp punches faster than a bullet; Mary Anning was self-taught.
- A T4 question shows the depth — Permian extinction wiped 95% of marine life; Pittman-Robertson 1937 funded the wildlife you hunt today; Singer's utilitarian animal-rights argument has specific claims one can engage with.
- A T5 question makes the player want to read Aldo Leopold or visit La Brea Tar Pits or see whether the K-Pg iridium layer is visible in a roadcut they pass.
- Humane treatment is threaded through husbandry + hunting + welfare-history questions — *consistent moral framing across the bank*.

## Anti-patterns specific to animals

- **No anthropomorphizing as if facts** — "the elephant cried" should be "the elephant displayed grief-like behavior"
- **No fabricated species names** — every binomial cited must be real
- **No outdated taxonomy** — Apatosaurus/Brontosaurus reinstated; dire wolf reassigned to *Aenocyon* 2021; pluto'd whales as land mammals not aquatic from start
- **No "all hunting is wrong"** framing — bank does not adopt that frame; presents the actual ethical principles practiced
- **No "all eating animals is wrong" framing** — bank teaches humane treatment, not vegetarianism
- **No genitive-Latin errors** — "T. rex" or "*Tyrannosaurus rex*"; not "*Tyrannosaurus Rex*"
- **No popular-myth perpetuation** — Marco-Polo-style errors (Brontosaurus is real now, etc.)
