"""Generate ingredient data for batches C (levels 7-10) and D (levels 10-20+)."""
import json, os

# Helper to build a recipe set thematically
def make_recipes(name_0, name_1, name_2, name_3, name_4, name_5,
                 sp1, sp2, sp3, sp4, sp5,
                 bt3, bt4, bt5, ba3, ba4, ba5,
                 bs3='', bs3_effect='', bs4='', bs4_effect='', bs5='', bs5_effect=''):
    def make(name, sp, bt, ba, bs='', beff=''):
        r = {'name': name, 'sp': sp, 'bonus_type': bt, 'bonus_amount': ba}
        if bt == 'stat' and bs:
            r['bonus_stat'] = bs
        if bt == 'status' and beff:
            r['bonus_effect'] = beff
        return r
    return {
        '0': {'name': name_0, 'sp': 0, 'bonus_type': 'none', 'bonus_amount': 0},
        '1': make(name_1, sp1, 'none', 0),
        '2': make(name_2, sp2, 'none', 0),
        '3': make(name_3, sp3, bt3, ba3, bs3, bs3_effect),
        '4': make(name_4, sp4, bt4, ba4, bs4, bs4_effect),
        '5': make(name_5, sp5, bt5, ba5, bs5, bs5_effect),
    }

BATCH_C = {
    "komodo_venom_gland": {
        "name": "komodo venom gland",
        "symbol": ",", "color": [100, 160, 80], "weight": 2.0, "min_level": 7, "source_monster": "komodo_brute",
        "recipes": make_recipes(
            "burst venom sac", "detoxified venom broth", "komodo essence soup",
            "paralytic venom reduction", "komodo hunter's draught", "apex predator's elixir",
            40, 75, 110, 155, 200,
            "stat", "stat", "two_stats", 1, 2, 2, "DEX", "", "DEX")
    },
    "lion_meat": {
        "name": "lion meat",
        "symbol": ",", "color": [220, 160, 80], "weight": 8.0, "min_level": 7, "source_monster": "dire_lion",
        "recipes": make_recipes(
            "ruined lion chunks", "roasted lion flank", "hearty lion stew",
            "lion-heart roast", "pride's glory feast", "apex lion king's banquet",
            42, 78, 115, 160, 205,
            "stat", "combat_stat", "two_stats", 1, 2, 2, "STR")
    },
    "roc_egg_fragment": {
        "name": "roc egg fragment",
        "symbol": ",", "color": [240, 230, 200], "weight": 3.0, "min_level": 7, "source_monster": "roc_chick",
        "recipes": make_recipes(
            "cracked roc egg mess", "roc egg broth", "sky giant omelette",
            "great roc egg poached", "roc-heart soufflé", "sky sovereign's egg feast",
            45, 80, 120, 165, 210,
            "stat", "two_stats", "all_stats", 1, 1, 1, "STR")
    },
    "redcap_blood": {
        "name": "redcap blood",
        "symbol": ",", "color": [200, 40, 40], "weight": 1.5, "min_level": 7, "source_monster": "redcap",
        "recipes": make_recipes(
            "coagulated redcap ichor", "blood-iron tonic", "fae blood reduction",
            "redcap rage potion", "iron-dyed essence draught", "redcap warlord's elixir",
            40, 75, 112, 155, 200,
            "stat", "combat_stat", "two_stats", 1, 2, 2, "STR")
    },
    "elemental_air_core": {
        "name": "elemental air core",
        "symbol": ",", "color": [200, 230, 255], "weight": 0.5, "min_level": 7, "source_monster": "air_elemental",
        "recipes": make_recipes(
            "dissipated wind essence", "zephyr extract", "sky core infusion",
            "swiftwind reduction", "gale force elixir", "tempest heart draught",
            38, 72, 108, 152, 198,
            "stat", "stat", "status", 2, 2, 30, "DEX", "", "DEX", "", "", "haste")
    },
    "peryton_antler": {
        "name": "peryton antler",
        "symbol": ",", "color": [170, 200, 140], "weight": 4.0, "min_level": 7, "source_monster": "peryton",
        "recipes": make_recipes(
            "ruined antler splinters", "antler broth", "skyhorn reduction",
            "shadow-deer essence stew", "peryton hunter's feast", "winged-stag grand banquet",
            42, 78, 115, 160, 208,
            "stat", "two_stats", "two_stats", 1, 1, 2, "DEX")
    },
    "giant_marrow": {
        "name": "giant marrow",
        "symbol": ",", "color": [200, 180, 140], "weight": 6.0, "min_level": 7, "source_monster": "hill_giant",
        "recipes": make_recipes(
            "split giant bone mush", "giant marrow broth", "hillborn marrow soup",
            "giant-strength reduction", "titan marrow pottage", "hill lord's marrow feast",
            45, 82, 122, 168, 215,
            "stat", "combat_stat", "two_stats", 2, 2, 2, "STR")
    },
    "yuan_ti_venom_sac": {
        "name": "yuan-ti venom sac",
        "symbol": ",", "color": [80, 160, 80], "weight": 2.0, "min_level": 7, "source_monster": "yuan_ti_pureblood",
        "recipes": make_recipes(
            "burst serpent sac", "neutralised venom broth", "yuan-ti essence soup",
            "serpent-blood reduction", "yuan-ti ritual draught", "pureblood serpent essence",
            42, 78, 115, 162, 210,
            "stat", "two_stats", "two_stats", 1, 1, 2, "DEX")
    },
    "winged_mane": {
        "name": "winged mane",
        "symbol": ",", "color": [230, 220, 200], "weight": 2.0, "min_level": 8, "source_monster": "pegasus_hostile",
        "recipes": make_recipes(
            "tangled sky-mane mess", "sky-mane broth", "winged essence soup",
            "pegasus mane reduction", "celestial flight draught", "sky sovereign's mane elixir",
            48, 88, 128, 175, 225,
            "stat", "two_stats", "all_stats", 2, 1, 1, "DEX")
    },
    "lindworm_skin": {
        "name": "lindworm skin",
        "symbol": ",", "color": [80, 140, 80], "weight": 7.0, "min_level": 8, "source_monster": "lindworm",
        "recipes": make_recipes(
            "ruined worm-hide scraps", "lindworm skin broth", "serpent-hide stock",
            "nordic wyrm reduction", "lindworm power pottage", "world-serpent kin feast",
            50, 92, 135, 182, 232,
            "stat", "combat_stat", "two_stats", 1, 2, 2, "CON")
    },
    "embalming_resin": {
        "name": "embalming resin",
        "symbol": ",", "color": [200, 180, 100], "weight": 1.5, "min_level": 8, "source_monster": "anubis_guardian",
        "recipes": make_recipes(
            "rancid embalming paste", "purified resin tincture", "golden resin reduction",
            "divine preservation broth", "anubis-blessed essence", "eternal guardian's draught",
            48, 88, 130, 178, 228,
            "stat", "status", "two_stats", 1, 20, 2, "CON", "", "", "regenerating")
    },
    "each_uisce_mane": {
        "name": "each uisce mane",
        "symbol": ",", "color": [60, 140, 200], "weight": 3.0, "min_level": 8, "source_monster": "each_uisce",
        "recipes": make_recipes(
            "drowned mane slurry", "water-horse mane broth", "ocean mane essence",
            "fae water-horse reduction", "each uisce power draught", "water king's supreme elixir",
            48, 88, 130, 178, 228,
            "stat", "status", "two_stats", 2, 25, 2, "CON", "", "", "cold_shield")
    },
    "ugallu_claw": {
        "name": "ugallu claw",
        "symbol": ",", "color": [140, 80, 40], "weight": 3.0, "min_level": 8, "source_monster": "ugallu_demon",
        "recipes": make_recipes(
            "crumbled demon talon", "ugallu essence broth", "mesopotamian claw soup",
            "storm-demon reduction", "ugallu power draught", "lion-eagle demon feast",
            50, 90, 133, 180, 230,
            "stat", "combat_stat", "two_stats", 2, 2, 2, "STR")
    },
    "kusarikku_horn": {
        "name": "kusarikku horn",
        "symbol": ",", "color": [160, 130, 90], "weight": 4.0, "min_level": 8, "source_monster": "kusarikku",
        "recipes": make_recipes(
            "splintered bull-man horn", "kusarikku horn broth", "bull-scorpion essence",
            "ancient warrior reduction", "kusarikku strength draught", "mesopotamian bull-god feast",
            50, 92, 135, 182, 233,
            "stat", "combat_stat", "two_stats", 2, 2, 2, "STR")
    },
    "grell_tentacle": {
        "name": "grell tentacle",
        "symbol": ",", "color": [120, 160, 80], "weight": 2.5, "min_level": 8, "source_monster": "grell",
        "recipes": make_recipes(
            "rubbery tentacle mess", "grell tentacle broth", "lightning-infused calamari",
            "grell electrode reduction", "shock-tentacle essence draught", "lightning brain feast",
            46, 86, 128, 175, 225,
            "status", "status", "two_stats", 15, 28, 2,
            "", "lightning_resist", "", "lightning_resist")
    },
    "infernal_perfume": {
        "name": "infernal perfume",
        "symbol": ",", "color": [200, 100, 200], "weight": 0.3, "min_level": 8, "source_monster": "incubus",
        "recipes": make_recipes(
            "corrupted perfume residue", "demonic scent tincture", "infernal aromatic reduction",
            "charisma draught", "devil's charm elixir", "infernal seduction essence",
            45, 85, 128, 175, 225,
            "stat", "stat", "two_stats", 1, 2, 2, "WIS", "", "WIS")
    },
    "devil_glaive_shard": {
        "name": "devil glaive shard",
        "symbol": ",", "color": [200, 80, 60], "weight": 2.0, "min_level": 8, "source_monster": "bearded_devil",
        "recipes": make_recipes(
            "corroded glaive dust", "infernal metal broth", "devil-iron essence",
            "hellforged blade reduction", "nine hells weapon draught", "bearded devil's feast",
            50, 90, 133, 182, 233,
            "stat", "combat_stat", "two_stats", 2, 2, 2, "STR")
    },
    "lurker_skin": {
        "name": "lurker skin",
        "symbol": ",", "color": [80, 80, 60], "weight": 5.0, "min_level": 8, "source_monster": "lurker_above",
        "recipes": make_recipes(
            "ruined ceiling-hide scraps", "lurker membrane broth", "camouflage-skin essence",
            "ambush predator reduction", "lurker shadow draught", "ceiling master's feast",
            48, 88, 130, 178, 228,
            "stat", "status", "two_stats", 2, 20, 2, "DEX", "", "", "invisible")
    },
    "mineral_shard": {
        "name": "mineral shard",
        "symbol": ",", "color": [200, 200, 160], "weight": 4.0, "min_level": 8, "source_monster": "xorn",
        "recipes": make_recipes(
            "crumbled mineral dust", "mineral crystal broth", "xorn-essence stone soup",
            "earth-devourer reduction", "mineral power pottage", "deep earth lord's feast",
            48, 88, 132, 180, 230,
            "stat", "combat_stat", "all_stats", 2, 2, 1, "STR")
    },
    "hook_horror_hook": {
        "name": "hook horror hook",
        "symbol": ",", "color": [160, 140, 100], "weight": 4.0, "min_level": 8, "source_monster": "hook_horror",
        "recipes": make_recipes(
            "blunted hook pulp", "chitinous hook broth", "deep crawler carapace soup",
            "hook-edge reduction", "hook horror slayer draught", "master hook-beast feast",
            50, 90, 133, 182, 233,
            "stat", "combat_stat", "two_stats", 2, 2, 2, "STR")
    },
    "strigoi_fang": {
        "name": "strigoi fang",
        "symbol": ",", "color": [200, 180, 160], "weight": 1.0, "min_level": 8, "source_monster": "strigoi",
        "recipes": make_recipes(
            "dissolved vampire fang", "strigoi essence tincture", "blood-fang reduction",
            "vampire hunter's draught", "strigoi lord's elixir", "ancient blood-fang essence",
            46, 86, 128, 175, 225,
            "status", "status", "two_stats", 20, 35, 2,
            "", "poison_resist", "", "poison_resist")
    },
    "death_mage_phylactery": {
        "name": "death mage phylactery",
        "symbol": ",", "color": [120, 80, 160], "weight": 1.0, "min_level": 8, "source_monster": "death_mage",
        "recipes": make_recipes(
            "shattered phylactery dust", "arcane death tincture", "necromantic essence broth",
            "lich's minor draught", "death mage power elixir", "phylactery-bound essence",
            48, 88, 130, 178, 228,
            "stat", "two_stats", "all_stats", 2, 1, 1, "INT")
    },
    "mohrg_organ": {
        "name": "mohrg organ",
        "symbol": ",", "color": [160, 80, 80], "weight": 3.0, "min_level": 8, "source_monster": "mohrg",
        "recipes": make_recipes(
            "putrid mohrg viscera", "undead organ broth", "animate flesh reduction",
            "mohrg vitality stew", "undying essence draught", "mohrg master's essence",
            46, 86, 128, 175, 225,
            "status", "stat", "two_stats", 20, 2, 2,
            "", "regenerating", "CON")
    },
    "death_beetle_ichor": {
        "name": "death beetle ichor",
        "symbol": ",", "color": [60, 40, 80], "weight": 1.5, "min_level": 8, "source_monster": "death_beetle",
        "recipes": make_recipes(
            "poisonous ichor mess", "detoxified beetle extract", "death-carapace essence",
            "darkness-infused reduction", "death beetle draught", "doom-beetle essence feast",
            46, 86, 128, 175, 225,
            "status", "status", "two_stats", 15, 28, 2,
            "", "poison_resist", "", "death_ward")
    },
    "lycanthrope_blood": {
        "name": "lycanthrope blood",
        "symbol": ",", "color": [180, 100, 60], "weight": 1.5, "min_level": 8, "source_monster": "werewolf",
        "recipes": make_recipes(
            "coagulated wolf blood", "lycanthrope blood tonic", "moon-touched reduction",
            "beastblood power brew", "lycanthrope strength elixir", "alpha wolf's blood essence",
            48, 90, 133, 182, 233,
            "stat", "combat_stat", "two_stats", 2, 2, 2, "STR")
    },
    "hag_eye": {
        "name": "hag eye",
        "symbol": ",", "color": [100, 200, 80], "weight": 1.0, "min_level": 8, "source_monster": "green_hag",
        "recipes": make_recipes(
            "ruined witch organ", "hag-sight tincture", "green hag essence",
            "witch's eye reduction", "hag-craft elixir", "green hag coven essence",
            46, 86, 128, 175, 225,
            "stat", "stat", "two_stats", 2, 2, 2, "WIS", "", "PER")
    },
    "elemental_water_core": {
        "name": "elemental water core",
        "symbol": ",", "color": [80, 160, 220], "weight": 1.0, "min_level": 8, "source_monster": "water_elemental",
        "recipes": make_recipes(
            "dissipated water essence", "water core infusion", "tidal essence broth",
            "ocean core reduction", "abyssal water draught", "deep sea elemental elixir",
            46, 86, 128, 175, 226,
            "status", "status", "two_stats", 20, 35, 2,
            "", "cold_shield", "", "cold_shield")
    },
    "troll_regeneration_gland": {
        "name": "troll regeneration gland",
        "symbol": ",", "color": [80, 180, 80], "weight": 3.0, "min_level": 8, "source_monster": "ice_troll",
        "recipes": make_recipes(
            "burst regen gland mess", "troll regen broth", "ice-troll essence stock",
            "regenerative troll reduction", "ice troll vitality feast", "frost troll's supreme elixir",
            50, 92, 135, 183, 235,
            "status", "status", "stat", 25, 40, 2,
            "", "regenerating", "", "regenerating", "CON")
    },
    "minotaur_horn": {
        "name": "minotaur horn",
        "symbol": ",", "color": [180, 140, 90], "weight": 5.0, "min_level": 8, "source_monster": "minotaur_warrior",
        "recipes": make_recipes(
            "cracked minotaur horn", "labyrinth horn broth", "bull-warrior reduction",
            "minotaur strength stew", "labyrinth master's feast", "maze-lord's grand banquet",
            52, 95, 140, 190, 240,
            "stat", "combat_stat", "two_stats", 2, 2, 2, "STR")
    },
    # Level 9
    "sphinx_mane": {
        "name": "sphinx mane",
        "symbol": ",", "color": [220, 190, 100], "weight": 3.0, "min_level": 9, "source_monster": "sphinx",
        "recipes": make_recipes(
            "tangled sphinx mane", "sphinx mane broth", "riddle-guardian essence",
            "sphinx wisdom reduction", "oracle sphinx draught", "great sphinx's grand elixir",
            55, 100, 148, 200, 255,
            "stat", "two_stats", "all_stats", 2, 2, 1, "INT")
    },
    "frost_giant_bone": {
        "name": "frost giant bone",
        "symbol": ",", "color": [200, 220, 240], "weight": 10.0, "min_level": 9, "source_monster": "frost_giant",
        "recipes": make_recipes(
            "crumbled frost giant bone", "giant bone marrow broth", "frost giant essence stock",
            "coldsoul giant reduction", "frost giant warlord's feast", "jotun frost lord's banquet",
            58, 105, 155, 210, 268,
            "stat", "combat_stat", "two_stats", 2, 3, 3, "CON")
    },
    "corruption_scale": {
        "name": "corruption scale",
        "symbol": ",", "color": [80, 60, 40], "weight": 4.0, "min_level": 9, "source_monster": "nidhoggr_brood",
        "recipes": make_recipes(
            "crumbled corruption dust", "world-serpent scale broth", "nidhoggr essence soup",
            "world-root corruption stew", "nidhoggr power draught", "yggdrasil's bane elixir",
            55, 100, 148, 200, 255,
            "stat", "two_stats", "all_stats", 2, 2, 1, "CON")
    },
    "sphinx_dust_gold": {
        "name": "sphinx dust gold",
        "symbol": ",", "color": [240, 210, 80], "weight": 0.5, "min_level": 9, "source_monster": "egyptian_sphinx",
        "recipes": make_recipes(
            "scattered gold dust", "golden sphinx infusion", "solar riddle-dust broth",
            "pharaoh's golden reduction", "sphinx gold draught", "eternal sphinx gold elixir",
            55, 100, 148, 200, 255,
            "stat", "two_stats", "all_stats", 2, 1, 1, "INT")
    },
    "thoth_ink": {
        "name": "thoth ink",
        "symbol": ",", "color": [60, 80, 160], "weight": 0.5, "min_level": 9, "source_monster": "thoth_construct",
        "recipes": make_recipes(
            "corrupted divine ink", "thoth ink tincture", "divine scribe essence",
            "knowledge-infused reduction", "thoth's blessing draught", "divine wisdom elixir",
            52, 95, 142, 195, 248,
            "stat", "stat", "two_stats", 2, 2, 2, "INT", "", "WIS")
    },
    "fomorian_bone": {
        "name": "fomorian bone",
        "symbol": ",", "color": [140, 120, 100], "weight": 8.0, "min_level": 9, "source_monster": "fomorian",
        "recipes": make_recipes(
            "twisted giant bone", "fomorian bone broth", "cursed giant marrow",
            "evil eye reduction", "fomorian warlord's stew", "ancient giant curse elixir",
            55, 100, 148, 200, 255,
            "stat", "combat_stat", "two_stats", 2, 3, 3, "STR")
    },
    "cath_palug_claw": {
        "name": "cath palug claw",
        "symbol": ",", "color": [200, 180, 160], "weight": 4.0, "min_level": 9, "source_monster": "cath_palug",
        "recipes": make_recipes(
            "shattered fae cat claw", "celtic cat-beast broth", "cath palug essence",
            "lake-cat power reduction", "cath palug hunter's draught", "arthurian beast feast",
            55, 100, 148, 200, 255,
            "stat", "combat_stat", "two_stats", 2, 2, 2, "DEX")
    },
    "primordial_clay": {
        "name": "primordial clay",
        "symbol": ",", "color": [160, 130, 100], "weight": 5.0, "min_level": 9, "source_monster": "lahamu",
        "recipes": make_recipes(
            "dried primordial mud", "lahamu clay broth", "ancient clay essence",
            "primordial reduction", "first-mother's pottage", "lahamu's creation elixir",
            52, 95, 142, 195, 248,
            "stat", "all_stats", "all_stats", 2, 1, 2, "CON")
    },
    "brain_lobe": {
        "name": "brain lobe",
        "symbol": ",", "color": [220, 180, 160], "weight": 2.0, "min_level": 9, "source_monster": "intellect_devourer",
        "recipes": make_recipes(
            "digested brain pulp", "cerebral lobe broth", "psionic brain reduction",
            "mind-devourer essence", "intellect maximiser draught", "psionic brain supreme elixir",
            52, 95, 142, 195, 248,
            "stat", "stat", "two_stats", 2, 2, 2, "INT", "", "WIS")
    },
    "cloaker_hide": {
        "name": "cloaker hide",
        "symbol": ",", "color": [40, 40, 60], "weight": 5.0, "min_level": 9, "source_monster": "cloaker",
        "recipes": make_recipes(
            "ruined cloaker membrane", "shadow-hide broth", "manta ray-kin essence",
            "darkness cloak reduction", "cloaker shadow draught", "abyss cloak supreme feast",
            52, 95, 142, 195, 248,
            "stat", "status", "two_stats", 2, 25, 2, "DEX", "", "", "invisible")
    },
    "enchanted_clay": {
        "name": "enchanted clay",
        "symbol": ",", "color": [180, 160, 130], "weight": 6.0, "min_level": 9, "source_monster": "clay_golem",
        "recipes": make_recipes(
            "crumbled golem clay", "enchanted clay broth", "golem essence stock",
            "divine clay reduction", "clay golem vitality stew", "maker's clay elixir",
            52, 95, 142, 195, 248,
            "stat", "combat_stat", "two_stats", 2, 2, 2, "CON")
    },
    "displacer_hide": {
        "name": "displacer hide",
        "symbol": ",", "color": [60, 40, 100], "weight": 5.0, "min_level": 9, "source_monster": "displacer_beast",
        "recipes": make_recipes(
            "ruined phase-hide scraps", "displacer membrane broth", "blink-skin essence",
            "phase-shift reduction", "displacer master draught", "panther void supreme elixir",
            55, 100, 148, 200, 255,
            "stat", "status", "two_stats", 2, 25, 2, "DEX", "", "", "invisible")
    },
    "black_ooze": {
        "name": "black ooze",
        "symbol": ",", "color": [30, 30, 30], "weight": 4.0, "min_level": 9, "source_monster": "black_pudding",
        "recipes": make_recipes(
            "failed ooze experiment", "black pudding extract", "dark ooze reduction",
            "void-black essence stew", "abyss pudding draught", "black ooze supreme elixir",
            50, 92, 138, 190, 242,
            "status", "status", "all_stats", 20, 35, 1,
            "", "poison_resist", "", "death_ward")
    },
    "trapper_membrane": {
        "name": "trapper membrane",
        "symbol": ",", "color": [120, 110, 80], "weight": 6.0, "min_level": 9, "source_monster": "trapper",
        "recipes": make_recipes(
            "ruined cave-beast hide", "trapper membrane broth", "ambush creature essence",
            "deep trapper reduction", "ceiling predator draught", "cave master's membrane feast",
            50, 92, 138, 190, 242,
            "stat", "stat", "two_stats", 2, 2, 2, "DEX", "", "CON")
    },
    "revenant_heart": {
        "name": "revenant heart",
        "symbol": ",", "color": [180, 60, 60], "weight": 2.0, "min_level": 9, "source_monster": "revenant",
        "recipes": make_recipes(
            "stillborn revenant organ", "undying heart broth", "revenge-bound essence",
            "revenant will reduction", "undying vengeance draught", "revenant's deathless elixir",
            52, 95, 142, 195, 248,
            "status", "stat", "two_stats", 25, 2, 2,
            "", "regenerating", "CON")
    },
    "tomb_stone_fragment": {
        "name": "tomb stone fragment",
        "symbol": ",", "color": [160, 150, 140], "weight": 5.0, "min_level": 9, "source_monster": "tomb_guardian",
        "recipes": make_recipes(
            "crumbled tomb stone", "grave stone mineral broth", "tomb guardian essence",
            "eternal guardian reduction", "pharaoh's tomb draught", "ancient death ward elixir",
            50, 92, 138, 190, 242,
            "status", "status", "two_stats", 20, 35, 2,
            "", "death_ward", "", "death_ward")
    },
    "elemental_ice_core": {
        "name": "elemental ice core",
        "symbol": ",", "color": [180, 220, 240], "weight": 1.0, "min_level": 9, "source_monster": "ice_elemental",
        "recipes": make_recipes(
            "melted ice core puddle", "cryo elemental extract", "glacial core broth",
            "absolute cold reduction", "ice elemental draught", "glacial heart supreme elixir",
            50, 92, 138, 190, 242,
            "status", "status", "two_stats", 22, 38, 2,
            "", "cold_shield", "", "cold_shield")
    },
    "mound_mulch": {
        "name": "mound mulch",
        "symbol": ",", "color": [80, 120, 60], "weight": 5.0, "min_level": 9, "source_monster": "shambling_mound",
        "recipes": make_recipes(
            "rotten plant mulch", "shambling mound essence", "plant-matter broth",
            "animated mound reduction", "shambling life draught", "great swamp lord's feast",
            50, 92, 138, 190, 242,
            "stat", "status", "two_stats", 2, 20, 2,
            "CON", "", "", "regenerating")
    },
    "corrupted_wing_feather": {
        "name": "corrupted wing feather",
        "symbol": ",", "color": [120, 80, 160], "weight": 1.0, "min_level": 9, "source_monster": "corrupted_pegasus",
        "recipes": make_recipes(
            "crumbling corrupted feather", "tainted sky-feather broth", "dark pegasus essence",
            "shadow-flight reduction", "corrupted sky draught", "void-pegasus supreme elixir",
            50, 92, 138, 190, 242,
            "stat", "two_stats", "all_stats", 2, 1, 1, "DEX")
    },
    "nue_tail_quill": {
        "name": "nue tail quill",
        "symbol": ",", "color": [80, 80, 80], "weight": 1.0, "min_level": 9, "source_monster": "nue",
        "recipes": make_recipes(
            "broken chimeric quill", "nue essence broth", "japanese chimera reduction",
            "ill-omen reduction", "nue spirit draught", "yokai chimera supreme elixir",
            50, 92, 138, 190, 242,
            "random_stat", "two_stats", "all_stats", 1, 2, 1)
    },
    "drow_poison_extract": {
        "name": "drow poison extract",
        "symbol": ",", "color": [80, 40, 120], "weight": 0.5, "min_level": 9, "source_monster": "drow_warrior",
        "recipes": make_recipes(
            "corrupted drow extract", "neutralised drow poison", "underdark essence broth",
            "spider-queen venom reduction", "drow elite draught", "Lolth-blessed elixir",
            52, 95, 142, 195, 248,
            "stat", "stat", "two_stats", 2, 2, 2, "DEX", "", "INT")
    },
    # Level 10
    "ember_ash": {
        "name": "ember ash",
        "symbol": ",", "color": [240, 100, 40], "weight": 1.0, "min_level": 10, "source_monster": "fire_giant",
        "recipes": make_recipes(
            "worthless grey ash", "fire giant ember broth", "volcanic ash essence",
            "firestorm reduction", "fire giant warlord's draught", "surtr's ember elixir",
            60, 110, 165, 225, 288,
            "stat", "status", "two_stats", 2, 35, 3,
            "STR", "", "", "fire_shield")
    },
    "spectral_essence": {
        "name": "spectral essence",
        "symbol": ",", "color": [200, 200, 240], "weight": 0.2, "min_level": 10, "source_monster": "valkyrie_shade",
        "recipes": make_recipes(
            "dissipated ghost remnant", "spectral essence tincture", "valkyrie shade broth",
            "spirit warrior reduction", "valkyrie's blessing draught", "warrior-spirit supreme elixir",
            58, 106, 158, 218, 280,
            "stat", "two_stats", "all_stats", 2, 2, 1, "STR")
    },
    "sea_serpent_oil": {
        "name": "sea serpent oil",
        "symbol": ",", "color": [60, 160, 200], "weight": 2.0, "min_level": 10, "source_monster": "norse_sea_serpent",
        "recipes": make_recipes(
            "rancid sea serpent fat", "ocean serpent oil broth", "sea-dragon essence soup",
            "jormungandr oil reduction", "world-sea draught", "norse sea sovereign's elixir",
            60, 110, 165, 225, 288,
            "stat", "two_stats", "all_stats", 2, 2, 1, "CON")
    },
    "anzu_feather": {
        "name": "anzu feather",
        "symbol": ",", "color": [200, 160, 60], "weight": 1.5, "min_level": 10, "source_monster": "anzu_bird",
        "recipes": make_recipes(
            "crumbled storm feather", "anzu feather broth", "mesopotamian storm-bird essence",
            "tablet of destiny reduction", "anzu's storm draught", "divine storm-bird feast",
            58, 106, 158, 218, 280,
            "stat", "status", "two_stats", 2, 30, 2,
            "STR", "", "", "lightning_resist")
    },
    "eyestalk": {
        "name": "eyestalk",
        "symbol": ",", "color": [200, 180, 160], "weight": 1.5, "min_level": 10, "source_monster": "beholder_spawn",
        "recipes": make_recipes(
            "burst beholder eye", "eye ray essence broth", "antimagic eye reduction",
            "beholder gaze stew", "tyrant eye draught", "great eye's omniscient elixir",
            58, 106, 158, 218, 280,
            "stat", "two_stats", "all_stats", 2, 2, 1, "PER")
    },
    "devil_chain_link": {
        "name": "devil chain link",
        "symbol": ",", "color": [160, 60, 60], "weight": 2.0, "min_level": 10, "source_monster": "chain_devil_spawn",
        "recipes": make_recipes(
            "corroded hell chain", "infernal iron broth", "chain devil essence",
            "hell-chain reduction", "chain devil warden's draught", "nine hells chain feast",
            58, 106, 158, 218, 280,
            "stat", "combat_stat", "two_stats", 2, 2, 2, "STR")
    },
    "shield_core": {
        "name": "shield guardian core",
        "symbol": ",", "color": [180, 180, 200], "weight": 5.0, "min_level": 10, "source_monster": "shield_guardian",
        "recipes": make_recipes(
            "cracked guardian core", "arcane guardian broth", "golem-shield essence",
            "protection core reduction", "guardian's aegis draught", "shield-master's elixir",
            58, 106, 158, 218, 280,
            "stat", "status", "two_stats", 2, 30, 3,
            "CON", "", "", "arcane_shield")
    },
    "roper_strand": {
        "name": "roper strand",
        "symbol": ",", "color": [180, 160, 120], "weight": 2.0, "min_level": 10, "source_monster": "roper",
        "recipes": make_recipes(
            "useless sticky strand", "roper essence broth", "deep cave adhesive reduction",
            "roper paralytic stew", "deep-earth lure draught", "roper master cave feast",
            56, 102, 152, 210, 270,
            "status", "stat", "two_stats", 20, 2, 2,
            "", "poison_resist", "DEX")
    },
    "elder_vampire_blood": {
        "name": "elder vampire blood",
        "symbol": ",", "color": [160, 20, 40], "weight": 1.0, "min_level": 10, "source_monster": "nosferatu",
        "recipes": make_recipes(
            "coagulated elder blood", "vampire blood tonic", "ancient blood reduction",
            "nosferatu vitality brew", "elder vampire draught", "primordial blood supreme elixir",
            60, 110, 165, 225, 288,
            "stat", "status", "two_stats", 2, 30, 3,
            "CON", "", "", "regenerating")
    },
    "pale_master_essence": {
        "name": "pale master essence",
        "symbol": ",", "color": [200, 200, 220], "weight": 0.5, "min_level": 10, "source_monster": "pale_master",
        "recipes": make_recipes(
            "faded necromantic residue", "pale essence tincture", "death-touched broth",
            "pale master reduction", "death-master draught", "supreme pale master's elixir",
            58, 106, 158, 218, 280,
            "stat", "two_stats", "all_stats", 2, 2, 1, "INT")
    },
    "wight_essence": {
        "name": "wight essence",
        "symbol": ",", "color": [120, 140, 160], "weight": 0.5, "min_level": 10, "source_monster": "wight_lord",
        "recipes": make_recipes(
            "dissipated wight fragment", "wight lord essence tincture", "undead lord reduction",
            "barrow lord broth", "wight drain draught", "wight lord supreme essence",
            56, 102, 152, 208, 268,
            "status", "stat", "two_stats", 22, 2, 2,
            "", "death_ward", "CON")
    },
    "dread_plate": {
        "name": "dread plate fragment",
        "symbol": ",", "color": [80, 60, 100], "weight": 4.0, "min_level": 10, "source_monster": "dread_knight",
        "recipes": make_recipes(
            "crumbled cursed metal", "dread iron broth", "infernal plate essence",
            "dread knight reduction", "dark paladin's feast", "void-knight supreme elixir",
            58, 106, 158, 218, 280,
            "stat", "combat_stat", "two_stats", 2, 3, 3, "CON")
    },
    "soul_fragment": {
        "name": "soul fragment",
        "symbol": ",", "color": [160, 160, 220], "weight": 0.2, "min_level": 10, "source_monster": "soul_eater_spawn",
        "recipes": make_recipes(
            "scattered soul dust", "soul fragment tincture", "spirit essence broth",
            "soul-force reduction", "soul eater draught", "essence of devoured souls",
            56, 102, 152, 210, 270,
            "stat", "two_stats", "all_stats", 2, 2, 1, "INT")
    },
    "storm_feather": {
        "name": "storm feather",
        "symbol": ",", "color": [180, 200, 240], "weight": 1.0, "min_level": 10, "source_monster": "lesser_thunderbird",
        "recipes": make_recipes(
            "singed storm feather", "thunderbird feather broth", "lightning-touched essence",
            "storm feather reduction", "thunderbird flight draught", "lightning sovereign's elixir",
            58, 106, 158, 218, 280,
            "status", "stat", "two_stats", 28, 2, 2,
            "", "lightning_resist", "DEX")
    },
    "sovereign_spore_cap": {
        "name": "sovereign spore cap",
        "symbol": ",", "color": [200, 220, 180], "weight": 2.0, "min_level": 10, "source_monster": "myconid_sovereign",
        "recipes": make_recipes(
            "burst sovereign spore", "sovereign spore broth", "myconid colony essence",
            "hive mind reduction", "myconid sovereign's feast", "fungal king's grand elixir",
            58, 106, 158, 218, 280,
            "stat", "two_stats", "all_stats", 2, 2, 1, "WIS")
    },
    "sphinx_claw": {
        "name": "sphinx claw",
        "symbol": ",", "color": [200, 160, 80], "weight": 3.0, "min_level": 10, "source_monster": "lesser_sphinx",
        "recipes": make_recipes(
            "blunted sphinx talon", "sphinx claw broth", "riddle-guardian essence",
            "sphinx wisdom reduction", "lesser sphinx draught", "sphinx's ancient blessing",
            58, 106, 158, 218, 280,
            "stat", "two_stats", "all_stats", 2, 2, 1, "INT")
    },
    "stone_giant_core": {
        "name": "stone giant core",
        "symbol": ",", "color": [160, 150, 130], "weight": 10.0, "min_level": 10, "source_monster": "stone_giant",
        "recipes": make_recipes(
            "crumbled giant stone", "stone giant marrow broth", "rock giant essence",
            "mountain core reduction", "stone giant warlord's feast", "mountain lord's supreme elixir",
            62, 112, 168, 228, 292,
            "stat", "combat_stat", "two_stats", 2, 3, 3, "STR")
    },
    "black_dragon_scale": {
        "name": "black dragon scale",
        "symbol": ",", "color": [40, 40, 40], "weight": 8.0, "min_level": 10, "source_monster": "young_black_dragon",
        "recipes": make_recipes(
            "charred black scale dust", "black dragon essence broth", "acid-dragon scale stock",
            "black dragon reduction", "young black drake's feast", "acidic dragon's elixir",
            62, 112, 168, 228, 292,
            "status", "two_stats", "all_stats", 30, 2, 1,
            "", "poison_resist")
    },
    "naga_scale": {
        "name": "naga scale",
        "symbol": ",", "color": [80, 160, 100], "weight": 3.0, "min_level": 10, "source_monster": "naga_guardian",
        "recipes": make_recipes(
            "shed naga scale dust", "naga essence broth", "guardian naga reduction",
            "snake-guardian stew", "naga guardian's draught", "divine serpent elixir",
            58, 106, 158, 218, 280,
            "stat", "two_stats", "all_stats", 2, 2, 1, "CON")
    },
}

BATCH_D = {
    # Level 11
    "hydra_bile": {
        "name": "hydra bile",
        "symbol": ",", "color": [80, 180, 80], "weight": 3.0, "min_level": 11, "source_monster": "lernaean_hydra",
        "recipes": make_recipes(
            "corrosive hydra bile", "neutralised hydra essence", "nine-head reduction",
            "hydra regeneration stew", "lernaean hydra draught", "immortal hydra's elixir",
            70, 128, 192, 260, 335,
            "status", "stat", "two_stats", 30, 2, 3,
            "", "regenerating", "CON")
    },
    "cerebral_fluid": {
        "name": "cerebral fluid",
        "symbol": ",", "color": [200, 160, 200], "weight": 1.0, "min_level": 11, "source_monster": "mind_flayer_thrall",
        "recipes": make_recipes(
            "wasted cerebral ooze", "psionic fluid broth", "mind-flayer essence reduction",
            "elder brain reduction", "illithid cerebral draught", "mind flayer supreme essence",
            68, 124, 186, 252, 322,
            "stat", "stat", "two_stats", 2, 2, 3, "INT", "", "WIS")
    },
    "devil_barb": {
        "name": "devil barb",
        "symbol": ",", "color": [200, 80, 80], "weight": 2.0, "min_level": 11, "source_monster": "barbed_devil",
        "recipes": make_recipes(
            "broken hell-barb shard", "infernal barb broth", "barbed devil essence",
            "hell-spike reduction", "barbed devil war draught", "nine hells barb supreme elixir",
            68, 124, 186, 252, 322,
            "stat", "combat_stat", "two_stats", 2, 3, 3, "STR")
    },
    "golem_stone": {
        "name": "golem stone",
        "symbol": ",", "color": [160, 160, 150], "weight": 8.0, "min_level": 11, "source_monster": "lesser_stone_golem",
        "recipes": make_recipes(
            "crumbled golem rubble", "stone golem essence broth", "animated stone reduction",
            "golem vitality stew", "stone sentinel's feast", "indestructible golem elixir",
            68, 124, 186, 252, 322,
            "stat", "combat_stat", "two_stats", 2, 3, 3, "CON")
    },
    "catoblepas_horn": {
        "name": "catoblepas horn",
        "symbol": ",", "color": [120, 100, 80], "weight": 6.0, "min_level": 11, "source_monster": "catoblepas",
        "recipes": make_recipes(
            "cracked death-beast horn", "catoblepas horn broth", "death gaze essence",
            "catoblepas stare reduction", "doom-gaze draught", "catoblepas lord's elixir",
            68, 124, 186, 252, 322,
            "stat", "status", "two_stats", 2, 30, 3,
            "CON", "", "", "death_ward")
    },
    "nightshade_essence": {
        "name": "nightshade spawn essence",
        "symbol": ",", "color": [40, 20, 60], "weight": 0.3, "min_level": 11, "source_monster": "nightshade_spawn",
        "recipes": make_recipes(
            "dissipated night essence", "nightshade tincture", "shadow-plane reduction",
            "nightshade power stew", "shadow realm draught", "absolute darkness elixir",
            65, 120, 180, 245, 315,
            "stat", "status", "two_stats", 2, 28, 3,
            "DEX", "", "", "invisible")
    },
    "queen_venom_gland": {
        "name": "spider queen venom gland",
        "symbol": ",", "color": [120, 80, 160], "weight": 2.0, "min_level": 11, "source_monster": "spider_queen",
        "recipes": make_recipes(
            "burst queen venom sac", "spider queen venom broth", "Lolth's venom essence",
            "queen spider reduction", "Lolth-venom draught", "Lolth's divine venom elixir",
            68, 124, 186, 252, 322,
            "stat", "status", "two_stats", 2, 30, 3,
            "DEX", "", "", "poison_resist")
    },
    "elemental_magma_core": {
        "name": "magma elemental core",
        "symbol": ",", "color": [220, 100, 40], "weight": 3.0, "min_level": 11, "source_monster": "magma_elemental",
        "recipes": make_recipes(
            "cooled magma shard", "magma core broth", "volcanic elemental essence",
            "magma heart reduction", "volcanic core draught", "lava lord's supreme elixir",
            68, 124, 186, 252, 322,
            "status", "status", "two_stats", 30, 45, 3,
            "", "fire_shield", "", "fire_shield")
    },
    "corrupted_horn_fragment": {
        "name": "corrupted unicorn horn",
        "symbol": ",", "color": [180, 80, 160], "weight": 2.0, "min_level": 11, "source_monster": "corrupted_unicorn",
        "recipes": make_recipes(
            "tainted alicorn dust", "corrupted horn broth", "shadow unicorn essence",
            "dark alicorn reduction", "void unicorn draught", "corrupted alicorn's elixir",
            65, 120, 180, 245, 315,
            "random_stat", "two_stats", "all_stats", 2, 2, 1)
    },
    "shadow_crystal": {
        "name": "shadow crystal",
        "symbol": ",", "color": [80, 60, 120], "weight": 1.0, "min_level": 11, "source_monster": "drow_mage",
        "recipes": make_recipes(
            "shattered shadow crystal", "shadow crystal extract", "underdark crystal essence",
            "shadow-weave reduction", "drow archmage draught", "Lolth's crystal elixir",
            65, 120, 180, 245, 315,
            "stat", "stat", "two_stats", 2, 2, 3, "INT", "", "WIS")
    },
    "red_dragon_scale": {
        "name": "red dragon scale",
        "symbol": ",", "color": [220, 60, 40], "weight": 8.0, "min_level": 11, "source_monster": "young_red_dragon",
        "recipes": make_recipes(
            "charred red scale dust", "red dragon essence broth", "firebreath scale soup",
            "young red drake reduction", "flame-dragon power feast", "ruby dragon's elixir",
            72, 130, 195, 265, 340,
            "status", "combat_stat", "two_stats", 35, 3, 3,
            "", "fire_shield")
    },
    # Level 12
    "scylla_fang": {
        "name": "scylla fang",
        "symbol": ",", "color": [180, 160, 200], "weight": 3.0, "min_level": 12, "source_monster": "scylla",
        "recipes": make_recipes(
            "crumbled sea-beast fang", "scylla essence broth", "six-headed reduction",
            "scylla horror stew", "whirlpool predator draught", "Scylla's sea-depth elixir",
            78, 142, 212, 288, 370,
            "stat", "combat_stat", "two_stats", 2, 3, 3, "STR")
    },
    "titan_essence": {
        "name": "titanspawn essence",
        "symbol": ",", "color": [160, 130, 200], "weight": 2.0, "min_level": 12, "source_monster": "titanspawn",
        "recipes": make_recipes(
            "dissipated titan power", "titan essence tincture", "old-god essence broth",
            "titan power reduction", "old titan's draught", "primordial titan's elixir",
            78, 142, 212, 288, 370,
            "stat", "all_stats", "all_stats", 2, 1, 2, "STR")
    },
    "vrock_feather": {
        "name": "vrock feather",
        "symbol": ",", "color": [120, 80, 60], "weight": 2.0, "min_level": 12, "source_monster": "vrock",
        "recipes": make_recipes(
            "tainted demon feather", "vrock essence broth", "abyssal vulture reduction",
            "demon-scream reduction", "vrock shriek draught", "abyss vrock supreme elixir",
            76, 138, 208, 282, 362,
            "stat", "status", "two_stats", 2, 30, 3,
            "STR", "", "", "poison_resist")
    },
    "erinyes_feather": {
        "name": "erinyes feather",
        "symbol": ",", "color": [200, 180, 160], "weight": 1.5, "min_level": 12, "source_monster": "lesser_erinyes",
        "recipes": make_recipes(
            "tattered fury feather", "erinyes essence broth", "fury wings reduction",
            "divine vengeance reduction", "erinyes wrath draught", "Fury's judgment elixir",
            76, 138, 208, 282, 362,
            "stat", "two_stats", "all_stats", 2, 2, 1, "DEX")
    },
    "behir_scale": {
        "name": "behir scale",
        "symbol": ",", "color": [60, 100, 160], "weight": 6.0, "min_level": 12, "source_monster": "lesser_behir",
        "recipes": make_recipes(
            "crumbled serpent-dragon scale", "behir essence broth", "lightning-scale reduction",
            "behir electric stew", "storm-serpent draught", "behir grand dragon feast",
            78, 142, 212, 288, 370,
            "status", "combat_stat", "two_stats", 30, 3, 3,
            "", "lightning_resist")
    },
    "lord_phylactery": {
        "name": "necromancer phylactery",
        "symbol": ",", "color": [80, 60, 120], "weight": 1.0, "min_level": 12, "source_monster": "necromancer_lord",
        "recipes": make_recipes(
            "shattered life-vessel", "phylactery essence tincture", "undead lord reduction",
            "necromancer power stew", "death lord's draught", "lich-king's phylactery elixir",
            76, 138, 208, 282, 362,
            "stat", "two_stats", "all_stats", 2, 2, 1, "INT")
    },
    "ossuary_shard": {
        "name": "ossuary shard",
        "symbol": ",", "color": [200, 190, 180], "weight": 3.0, "min_level": 12, "source_monster": "ossuary_horror",
        "recipes": make_recipes(
            "crumbled bone-house fragment", "ossuary essence broth", "charnel shard reduction",
            "bone horror stew", "tomb shards draught", "death house supreme elixir",
            76, 138, 208, 282, 362,
            "status", "stat", "two_stats", 25, 2, 3,
            "", "death_ward", "CON")
    },
    "death_essence": {
        "name": "death essence",
        "symbol": ",", "color": [80, 40, 100], "weight": 0.2, "min_level": 12, "source_monster": "lesser_death",
        "recipes": make_recipes(
            "dissipated death fragment", "death essence tincture", "reaper's reduction",
            "death's touch stew", "lesser death draught", "essence of mortality elixir",
            76, 138, 208, 282, 362,
            "status", "status", "all_stats", 25, 40, 1,
            "", "death_ward", "", "death_ward")
    },
    "alpha_lycanthrope_blood": {
        "name": "alpha lycanthrope blood",
        "symbol": ",", "color": [200, 100, 60], "weight": 1.5, "min_level": 12, "source_monster": "werewolf_alpha",
        "recipes": make_recipes(
            "coagulated alpha blood", "alpha wolf blood tonic", "pack leader reduction",
            "alpha bloodrage stew", "alpha lycanthrope draught", "pack sovereign blood elixir",
            78, 142, 212, 288, 370,
            "stat", "combat_stat", "two_stats", 2, 3, 3, "STR")
    },
    "wyvern_venom_gland": {
        "name": "greater wyvern venom gland",
        "symbol": ",", "color": [120, 180, 80], "weight": 3.0, "min_level": 12, "source_monster": "greater_wyvern",
        "recipes": make_recipes(
            "burst wyvern venom sac", "wyvern venom broth", "draconic venom essence",
            "wyvern venom reduction", "greater wyvern draught", "apex wyvern venom elixir",
            78, 142, 212, 288, 370,
            "stat", "status", "two_stats", 2, 35, 3,
            "DEX", "", "", "poison_resist")
    },
    # Level 13
    "aboleth_mucus": {
        "name": "aboleth mucus",
        "symbol": ",", "color": [80, 160, 140], "weight": 3.0, "min_level": 13, "source_monster": "lesser_aboleth",
        "recipes": make_recipes(
            "putrid aboleth slime", "aboleth essence broth", "elder brain slime reduction",
            "aboleth domination stew", "elder thing draught", "primal aboleth supreme elixir",
            85, 155, 232, 315, 405,
            "stat", "two_stats", "all_stats", 2, 2, 1, "INT")
    },
    "demon_bile": {
        "name": "hezrou demon bile",
        "symbol": ",", "color": [60, 120, 60], "weight": 2.0, "min_level": 13, "source_monster": "hezrou",
        "recipes": make_recipes(
            "toxic demon excretion", "neutralised hezrou broth", "abyss-toad essence",
            "demon bile reduction", "hezrou warlord's draught", "abyss amphibian supreme feast",
            85, 155, 232, 315, 405,
            "stat", "combat_stat", "two_stats", 2, 3, 3, "CON")
    },
    "devil_venom": {
        "name": "bone devil venom",
        "symbol": ",", "color": [180, 180, 200], "weight": 1.5, "min_level": 13, "source_monster": "bone_devil",
        "recipes": make_recipes(
            "cooled bone devil venom", "ossein devil broth", "hell-bone reduction",
            "devil's sting essence", "bone devil warden's draught", "hell bone supreme elixir",
            85, 155, 232, 315, 405,
            "status", "stat", "two_stats", 30, 2, 3,
            "", "poison_resist", "DEX")
    },
    "wyvern_stinger": {
        "name": "wyvern stinger",
        "symbol": ",", "color": [160, 200, 80], "weight": 4.0, "min_level": 13, "source_monster": "wyvern",
        "recipes": make_recipes(
            "broken wyvern stinger", "wyvern stinger broth", "winged-drake essence",
            "wyvern hunter's reduction", "sky-predator draught", "wyvern apex feast",
            88, 160, 240, 325, 418,
            "stat", "combat_stat", "two_stats", 2, 3, 3, "DEX")
    },
    "giant_bone": {
        "name": "skeletal giant bone",
        "symbol": ",", "color": [220, 210, 195], "weight": 10.0, "min_level": 13, "source_monster": "skeletal_giant",
        "recipes": make_recipes(
            "crumbled giant skeleton", "giant bone marrow broth", "skeletal giant essence",
            "undead giant reduction", "bone colossus feast", "titan skeleton supreme elixir",
            88, 160, 240, 325, 418,
            "stat", "combat_stat", "two_stats", 2, 3, 3, "STR")
    },
    "sea_dragon_scale": {
        "name": "sea dragon scale",
        "symbol": ",", "color": [60, 140, 200], "weight": 7.0, "min_level": 13, "source_monster": "sea_dragon_spawn",
        "recipes": make_recipes(
            "water-logged dragon scale", "sea dragon essence broth", "oceanic dragon reduction",
            "deep-sea drake stew", "sea dragon draught", "ocean dragon supreme elixir",
            90, 164, 245, 332, 428,
            "stat", "status", "two_stats", 2, 35, 3,
            "CON", "", "", "cold_shield")
    },
    # Level 14+
    "void_ichor": {
        "name": "void ichor",
        "symbol": ",", "color": [60, 40, 100], "weight": 1.0, "min_level": 14, "source_monster": "star_spawn",
        "recipes": make_recipes(
            "dissipated void ichor", "star spawn essence tincture", "void-plane reduction",
            "cosmic horror stew", "star spawn draught", "outer void supreme elixir",
            98, 178, 265, 360, 462,
            "stat", "two_stats", "all_stats", 2, 2, 1, "INT")
    },
    "night_hag_heartstone": {
        "name": "night hag heartstone",
        "symbol": ",", "color": [80, 60, 120], "weight": 2.0, "min_level": 14, "source_monster": "night_hag",
        "recipes": make_recipes(
            "cracked hag heartstone", "nightmare heartstone tincture", "night hag essence",
            "dream-realm reduction", "night hag's power draught", "nightmare queen's elixir",
            95, 172, 258, 350, 450,
            "stat", "two_stats", "all_stats", 2, 2, 1, "INT")
    },
    "cloudstuff": {
        "name": "cloudstuff",
        "symbol": ",", "color": [220, 230, 240], "weight": 0.5, "min_level": 14, "source_monster": "cloud_giant",
        "recipes": make_recipes(
            "dissipated cloud vapour", "cloud giant essence broth", "sky citadel reduction",
            "nimbus power stew", "cloud lord's draught", "storm throne supreme elixir",
            98, 178, 265, 360, 462,
            "stat", "status", "two_stats", 2, 35, 3,
            "STR", "", "", "lightning_resist")
    },
    "cerberus_saliva": {
        "name": "cerberus saliva",
        "symbol": ",", "color": [180, 120, 80], "weight": 1.0, "min_level": 15, "source_monster": "cerberus",
        "recipes": make_recipes(
            "dried three-headed drool", "underworld hound broth", "cerberus essence reduction",
            "hellhound triple-power stew", "guardian of Hades draught", "cerberus supreme elixir",
            108, 196, 292, 396, 510,
            "stat", "combat_stat", "all_stats", 2, 3, 1, "STR")
    },
    "demon_scales": {
        "name": "marilith demon scales",
        "symbol": ",", "color": [180, 80, 80], "weight": 5.0, "min_level": 15, "source_monster": "marilith_spawn",
        "recipes": make_recipes(
            "crumbled demon plate", "marilith essence broth", "six-armed demon reduction",
            "marilith power stew", "dance of blades draught", "six-armed supreme elixir",
            108, 196, 292, 396, 510,
            "stat", "combat_stat", "two_stats", 2, 3, 3, "DEX")
    },
    "demon_heart": {
        "name": "nalfeshnee heart",
        "symbol": ",", "color": [180, 60, 80], "weight": 4.0, "min_level": 15, "source_monster": "lesser_nalfeshnee",
        "recipes": make_recipes(
            "rancid demon organ", "nalfeshnee essence broth", "abyss lord reduction",
            "demon heart stew", "nalfeshnee power draught", "abyss toad supreme feast",
            108, 196, 292, 396, 510,
            "stat", "all_stats", "all_stats", 2, 1, 2, "STR")
    },
    "lesser_draco_bone": {
        "name": "undead dragon bone",
        "symbol": ",", "color": [160, 160, 120], "weight": 10.0, "min_level": 15, "source_monster": "lesser_undead_dragon",
        "recipes": make_recipes(
            "crumbled undead scale dust", "dracolich essence broth", "undead dragon reduction",
            "dracolich power stew", "undead dragon draught", "dracolich supreme elixir",
            108, 196, 292, 396, 510,
            "stat", "combat_stat", "two_stats", 3, 3, 3, "STR")
    },
    "void_shard": {
        "name": "void shard",
        "symbol": ",", "color": [40, 30, 60], "weight": 1.0, "min_level": 15, "source_monster": "void_elemental",
        "recipes": make_recipes(
            "dissipated void fragment", "void shard tincture", "planar void reduction",
            "void elemental essence", "nihility draught", "absolute void supreme elixir",
            105, 192, 286, 388, 498,
            "status", "two_stats", "all_stats", 35, 2, 1,
            "", "death_ward")
    },
    "chaos_essence": {
        "name": "chaos essence",
        "symbol": ",", "color": [200, 80, 200], "weight": 1.0, "min_level": 16, "source_monster": "glabrezu",
        "recipes": make_recipes(
            "unstable chaos fragment", "glabrezu essence broth", "demon prince reduction",
            "chaos power stew", "glabrezu lord's draught", "primordial chaos elixir",
            120, 218, 325, 440, 565,
            "random_stat", "all_stats", "all_stats", 2, 1, 2)
    },
    "demi_lich_skull": {
        "name": "demi-lich skull",
        "symbol": ",", "color": [200, 200, 160], "weight": 3.0, "min_level": 16, "source_monster": "demi_lich",
        "recipes": make_recipes(
            "crumbled lich skull", "demi-lich essence broth", "soul-gem bone reduction",
            "lich king power stew", "demi-lich draught", "transcendent lich supreme elixir",
            120, 218, 325, 440, 565,
            "stat", "two_stats", "all_stats", 3, 2, 2, "INT")
    },
    "nightwing_membrane": {
        "name": "nightwing membrane",
        "symbol": ",", "color": [40, 20, 60], "weight": 3.0, "min_level": 16, "source_monster": "nightwing",
        "recipes": make_recipes(
            "tattered shadow membrane", "nightwing essence broth", "shadow-plane reduction",
            "darkness wing stew", "nightwing shadow draught", "absolute shadow elixir",
            118, 215, 320, 435, 558,
            "stat", "status", "two_stats", 3, 40, 3,
            "DEX", "", "", "invisible")
    },
    "roc_talon": {
        "name": "roc talon",
        "symbol": ",", "color": [200, 180, 140], "weight": 6.0, "min_level": 16, "source_monster": "roc_adult",
        "recipes": make_recipes(
            "broken roc talon shard", "sky titan talon broth", "great roc reduction",
            "sky predator stew", "roc lord's draught", "sky sovereign supreme elixir",
            120, 218, 325, 440, 565,
            "stat", "combat_stat", "two_stats", 3, 3, 3, "STR")
    },
    "blue_dragon_scale": {
        "name": "blue dragon scale",
        "symbol": ",", "color": [80, 120, 220], "weight": 8.0, "min_level": 16, "source_monster": "adult_blue_dragon",
        "recipes": make_recipes(
            "charred blue scale dust", "blue dragon essence broth", "storm-dragon scale soup",
            "blue dragon reduction", "adult blue drake feast", "storm dragon's supreme elixir",
            122, 222, 330, 448, 575,
            "status", "combat_stat", "two_stats", 38, 3, 3,
            "", "lightning_resist")
    },
    "lich_dragon_scale": {
        "name": "lich dragon scale",
        "symbol": ",", "color": [120, 100, 160], "weight": 9.0, "min_level": 18, "source_monster": "lich_dragon_spawn",
        "recipes": make_recipes(
            "crumbled dracolich scale", "lich dragon essence broth", "undead dragon reduction",
            "dracolich power stew", "lich dragon lord's feast", "dracolich supreme grand elixir",
            140, 255, 380, 515, 660,
            "stat", "all_stats", "all_stats", 3, 1, 2, "INT")
    },
    "storm_essence": {
        "name": "storm essence",
        "symbol": ",", "color": [160, 200, 240], "weight": 1.0, "min_level": 18, "source_monster": "storm_giant",
        "recipes": make_recipes(
            "dissipated storm fragment", "storm giant essence broth", "tempest giant reduction",
            "storm titan power stew", "storm giant warlord's draught", "tempest sovereign elixir",
            140, 255, 380, 515, 660,
            "stat", "status", "two_stats", 3, 40, 3,
            "STR", "", "", "lightning_resist")
    },
    "adult_dragon_heart": {
        "name": "red dragon heart",
        "symbol": ",", "color": [220, 50, 30], "weight": 10.0, "min_level": 18, "source_monster": "adult_red_dragon",
        "recipes": make_recipes(
            "charred dragon organ", "elder dragon heart broth", "ancient fire-heart reduction",
            "dragon heart power stew", "ancient dragon's draught", "elder dragon heart supreme feast",
            142, 258, 385, 522, 670,
            "status", "all_stats", "all_stats", 40, 1, 2,
            "", "fire_shield")
    },
    "pit_fiend_scale": {
        "name": "pit fiend scale",
        "symbol": ",", "color": [160, 40, 40], "weight": 6.0, "min_level": 20, "source_monster": "pit_fiend_spawn",
        "recipes": make_recipes(
            "crumbled hell-lord scale", "pit fiend essence broth", "arch-devil reduction",
            "infernal lord power stew", "pit fiend supreme feast", "arch-devil's infernal elixir",
            160, 290, 432, 586, 752,
            "stat", "all_stats", "all_stats", 3, 1, 2, "STR")
    },
}

# Load and merge
path = os.path.join(os.path.dirname(__file__), 'items', 'ingredient.json')
data = json.load(open(path, encoding='utf-8'))
added = 0
for key, val in {**BATCH_C, **BATCH_D}.items():
    if key not in data:
        data[key] = val
        added += 1
    else:
        print(f'  SKIP: {key}')

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f'Added {added} ingredients. Total: {len(data)}')
