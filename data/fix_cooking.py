#!/usr/bin/env python3
"""
Complete cooking system overhaul:
1. Assign ingredient_id to every monster that lacks one
2. Add new ingredient entries to ingredient.json
3. Replace recipes.json with real harvestable-ingredient-only recipes
Run from: data/ directory
"""
import json, os, sys

MONSTERS_FILE  = 'monsters.json'
INGREDIENT_FILE = 'items/ingredient.json'
RECIPE_FILE    = 'items/recipes.json'

# ── 1. MONSTER → INGREDIENT MAP ─────────────────────────────────────────────
# Keys that already exist in ingredient.json are marked with existing=True
# New ones will be created below.

MONSTER_INGREDIENT = {
    # Using existing ingredients
    'zombie':           'zombie_flesh',
    'gelatinous_cube':  'toxic_jelly_sac',
    'wraith':           'spectral_essence',
    'leprechaun':       'lucky_clover',
    'kobold':           'kobold_scale',
    'cave_spider':      'spider_silk',
    'giant_spider':     'spider_silk',
    'skeleton':         'bone_shard',
    'ghoul':            'ghast_ichor',
    'acid_blob':        'black_ooze',
    'dark_elf':         'drow_poison_extract',
    'drow_priestess':   'drow_poison_extract',
    'wight':            'wight_essence',
    'rust_monster':     'mineral_shard',
    'shadow':           'shadow_essence',
    'shade':            'shadow_essence',
    'soul_shadow':      'shadow_crystal',
    'greater_shadow':   'shadow_crystal',
    'nightmare_shade':  'shadow_crystal',
    'shadow_master':    'shadow_crystal',
    'shadow_hound':     'shadow_fur',
    'mummy':            'embalming_resin',
    'ettin':            'giant_bone',
    'bone_titan':       'giant_marrow',
    'specter':          'spectral_essence',
    'haunting_presence':'spectral_essence',
    'dread_wraith':     'spectral_essence',
    'spectral_lord':    'spectral_essence',
    'ba_spirit':        'spectral_essence',
    'minotaur':         'minotaur_horn',
    'vampire_spawn':    'thrall_blood',
    'vampire':          'elder_vampire_blood',
    'vampire_lord':     'elder_vampire_blood',
    'fire_elemental':   'ember_ash',
    'earth_elemental':  'mineral_shard',
    'storm_elemental':  'storm_essence',
    'lich_apprentice':  'arcane_bone_dust',
    'necromancer_apprentice': 'witch_bone',
    'mind_flayer':      'cerebral_fluid',
    'elder_mind_flayer':'cerebral_fluid',
    'death_knight':     'charred_bone',
    'bone_golem':       'guardian_bone',
    'undead_colossus':  'guardian_bone',
    'greater_demon':    'demon_heart',
    'arch_demon':       'demon_heart',
    'beholder':         'eyestalk',
    'elder_beholder':   'eyestalk',
    'lich':             'lord_phylactery',
    'greater_lich':     'lord_phylactery',
    'lich_sovereign':   'lord_phylactery',
    'iron_golem':       'enchanted_plate',
    'flesh_golem':      'enchanted_clay',
    'ancient_lich':     'death_essence',
    'death_lord':       'death_essence',
    'soul_eater':       'soul_fragment',
    'banshee':          'soul_fragment',
    'allip':            'soul_fragment',
    'chaos_spawn':      'chaos_essence',
    'ruinous_djinn':    'chaos_essence',
    'orc_shaman':       'shaman_totem',
    'skeletal_archer':  'bone_arrow',
    'cave_toad':        'frog_legs',
    'harpy':            'hollow_bone',
    'dullahan_spawn':   'hollow_bone',
    'einherjar_ghost':  'hollow_essence',
    'berserker_spirit': 'warrior_bone',
    'goblin_shaman':    'goblin_flesh',
    'charybdis_spawn':  'scylla_fang',
    'duat_shade':       'barrow_dust',
    'mane_demon':       'dretch_gland',
    'lemure':           'dretch_gland',
    'poltergeist':      'wisp_essence',
    'will_o_wisp':      'wisp_essence',
    'ethereal_filcher': 'phase_silk',
    'fetch':            'changeling_glamour',
    'mimic':            'changeling_glamour',
    'boggart':          'puca_hair',
    'sluagh':           'death_essence',
    'death_echo':       'death_essence',
    'void_crawler':     'void_shard',
    'void_leviathan':   'void_ichor',
    'abyssal_overlord': 'void_ichor',
    'entropy_wraith':   'void_ichor',
    'elder_werewolf':   'lycanthrope_blood',
    'abyssal_champion': 'demon_scales',
    'demon_emperor':    'pit_fiend_scale',
    'world_serpent':    'world_serpent_scale',
    'shadow_master':    'shadow_crystal',
    # New ingredients
    'grid_bug':         'insect_carapace',
    'giant_centipede':  'insect_carapace',
    'rot_grub_swarm':   'insect_carapace',
    'stirge_swarm':     'bat_wing',
    'bat':              'bat_wing',
    'ogre':             'ogre_hide',
    'two_headed_ogre':  'ogre_hide',
    'orc_scout':        'orc_blood',
    'orc_warrior':      'orc_blood',
    'orc_berserker':    'orc_blood',
    'orc_warchief':     'orc_blood',
    'hobgoblin':        'hobgoblin_blood',
    'hobgoblin_captain':'hobgoblin_blood',
    'hobgoblin_warlord':'hobgoblin_blood',
    'bugbear':          'bugbear_pelt',
    'bugbear_chieftain':'bugbear_pelt',
    'brigand':          'battle_ration',
    'bandit_captain':   'battle_ration',
    'mercenary_veteran':'battle_ration',
    'dark_cultist':     'cultist_reagent',
    'battle_mage':      'cultist_reagent',
    'ammit_spawn':      'devourer_tooth',
    'floating_eye':     'eye_jelly',
}

# ── 2. NEW INGREDIENTS ───────────────────────────────────────────────────────

NEW_INGREDIENTS = {
    'insect_carapace': {
        'name': 'insect carapace',
        'symbol': ',', 'color': [130, 110, 70], 'weight': 0.5, 'min_level': 1,
        'source_monster': 'grid_bug', 'floor_spawn_weight': {},
        'unidentified_name': 'strange chitin',
        'recipes': {
            '0': {'name': 'ruined chitin mush', 'sp': 0,   'bonus_type': 'none',   'bonus_amount': 0},
            '1': {'name': 'roasted carapace',   'sp': 10,  'bonus_type': 'none',   'bonus_amount': 0},
            '2': {'name': 'crunchy chitin bits', 'sp': 20, 'bonus_type': 'none',   'bonus_amount': 0},
            '3': {'name': 'chitin jerky',        'sp': 35, 'bonus_type': 'stat',   'bonus_stat': 'DEX', 'bonus_amount': 1},
            '4': {'name': 'spiced chitin crisps','sp': 55, 'bonus_type': 'stat',   'bonus_stat': 'DEX', 'bonus_amount': 1},
            '5': {'name': 'masterwork chitin delicacy', 'sp': 80, 'bonus_type': 'two_stats', 'bonus_amount': 1},
        }
    },
    'bat_wing': {
        'name': 'bat wing',
        'symbol': ',', 'color': [80, 70, 100], 'weight': 0.5, 'min_level': 1,
        'source_monster': 'bat', 'floor_spawn_weight': {},
        'unidentified_name': 'leathery membrane',
        'recipes': {
            '0': {'name': 'singed wing mess',    'sp': 0,   'bonus_type': 'none',   'bonus_amount': 0},
            '1': {'name': 'roasted bat wing',    'sp': 12,  'bonus_type': 'none',   'bonus_amount': 0},
            '2': {'name': 'crispy bat wing',     'sp': 22,  'bonus_type': 'none',   'bonus_amount': 0},
            '3': {'name': 'glazed bat wings',    'sp': 40,  'bonus_type': 'stat',   'bonus_stat': 'DEX', 'bonus_amount': 1},
            '4': {'name': "cave flyer's feast",  'sp': 65,  'bonus_type': 'stat',   'bonus_stat': 'DEX', 'bonus_amount': 1},
            '5': {'name': 'midnight wing delicacy', 'sp': 95, 'bonus_type': 'two_stats', 'bonus_amount': 1},
        }
    },
    'eye_jelly': {
        'name': 'eye jelly',
        'symbol': ',', 'color': [200, 210, 60], 'weight': 0.3, 'min_level': 2,
        'source_monster': 'floating_eye', 'floor_spawn_weight': {},
        'unidentified_name': 'viscous orb extract',
        'recipes': {
            '0': {'name': 'ruined eye paste',    'sp': 0,   'bonus_type': 'none',   'bonus_amount': 0},
            '1': {'name': 'eye-jelly broth',     'sp': 15,  'bonus_type': 'none',   'bonus_amount': 0},
            '2': {'name': 'seer\'s soup',        'sp': 30,  'bonus_type': 'none',   'bonus_amount': 0},
            '3': {'name': 'oracle\'s consommé',  'sp': 50,  'bonus_type': 'stat',   'bonus_stat': 'PER', 'bonus_amount': 1},
            '4': {'name': 'all-seeing broth',    'sp': 75,  'bonus_type': 'stat',   'bonus_stat': 'PER', 'bonus_amount': 1},
            '5': {'name': 'third-eye elixir',    'sp': 110, 'bonus_type': 'two_stats', 'bonus_amount': 1},
        }
    },
    'ogre_hide': {
        'name': 'ogre hide',
        'symbol': ',', 'color': [150, 120, 80], 'weight': 4.0, 'min_level': 5,
        'source_monster': 'ogre', 'floor_spawn_weight': {},
        'unidentified_name': 'thick gray hide',
        'recipes': {
            '0': {'name': 'ruined hide jerky',   'sp': 0,   'bonus_type': 'none',   'bonus_amount': 0},
            '1': {'name': 'tough ogre jerky',    'sp': 25,  'bonus_type': 'none',   'bonus_amount': 0},
            '2': {'name': 'slow-cooked ogre',    'sp': 50,  'bonus_type': 'none',   'bonus_amount': 0},
            '3': {'name': 'ogre hide stew',      'sp': 80,  'bonus_type': 'stat',   'bonus_stat': 'CON', 'bonus_amount': 1},
            '4': {'name': 'giant\'s portion',    'sp': 120, 'bonus_type': 'stat',   'bonus_stat': 'STR', 'bonus_amount': 1},
            '5': {'name': 'titan\'s banquet',    'sp': 170, 'bonus_type': 'two_stats', 'bonus_amount': 1},
        }
    },
    'orc_blood': {
        'name': 'orc blood',
        'symbol': ',', 'color': [80, 140, 60], 'weight': 0.5, 'min_level': 2,
        'source_monster': 'orc_scout', 'floor_spawn_weight': {},
        'unidentified_name': 'foul green ichor',
        'recipes': {
            '0': {'name': 'ruined orc draught',  'sp': 0,   'bonus_type': 'none',   'bonus_amount': 0},
            '1': {'name': 'bitter orc brew',     'sp': 18,  'bonus_type': 'none',   'bonus_amount': 0},
            '2': {'name': 'warrior\'s draught',  'sp': 35,  'bonus_type': 'none',   'bonus_amount': 0},
            '3': {'name': 'berserker\'s tincture', 'sp': 55, 'bonus_type': 'stat',  'bonus_stat': 'STR', 'bonus_amount': 1},
            '4': {'name': 'warchief\'s elixir',  'sp': 85,  'bonus_type': 'stat',   'bonus_stat': 'CON', 'bonus_amount': 1},
            '5': {'name': 'blood of conquest',   'sp': 125, 'bonus_type': 'two_stats', 'bonus_amount': 1},
        }
    },
    'hobgoblin_blood': {
        'name': 'hobgoblin blood',
        'symbol': ',', 'color': [180, 80, 60], 'weight': 0.5, 'min_level': 3,
        'source_monster': 'hobgoblin', 'floor_spawn_weight': {},
        'unidentified_name': 'soldier\'s ichor',
        'recipes': {
            '0': {'name': 'ruined blood tonic',  'sp': 0,   'bonus_type': 'none',   'bonus_amount': 0},
            '1': {'name': 'soldier\'s broth',    'sp': 20,  'bonus_type': 'none',   'bonus_amount': 0},
            '2': {'name': 'disciplined draught', 'sp': 38,  'bonus_type': 'none',   'bonus_amount': 0},
            '3': {'name': 'legion\'s elixir',    'sp': 60,  'bonus_type': 'stat',   'bonus_stat': 'CON', 'bonus_amount': 1},
            '4': {'name': 'warlord\'s tincture', 'sp': 90,  'bonus_type': 'combat_stat', 'bonus_amount': 1},
            '5': {'name': 'iron discipline brew', 'sp': 130, 'bonus_type': 'two_stats', 'bonus_amount': 1},
        }
    },
    'bugbear_pelt': {
        'name': 'bugbear pelt',
        'symbol': ',', 'color': [110, 90, 60], 'weight': 2.0, 'min_level': 4,
        'source_monster': 'bugbear', 'floor_spawn_weight': {},
        'unidentified_name': 'coarse fur pelt',
        'recipes': {
            '0': {'name': 'singed fur mess',     'sp': 0,   'bonus_type': 'none',   'bonus_amount': 0},
            '1': {'name': 'smoked bugbear hide', 'sp': 22,  'bonus_type': 'none',   'bonus_amount': 0},
            '2': {'name': 'rough pelt jerky',    'sp': 42,  'bonus_type': 'none',   'bonus_amount': 0},
            '3': {'name': 'ambush hunter stew',  'sp': 65,  'bonus_type': 'stat',   'bonus_stat': 'DEX', 'bonus_amount': 1},
            '4': {'name': 'shadow-stalker feast','sp': 95,  'bonus_type': 'combat_stat', 'bonus_amount': 1},
            '5': {'name': 'chieftain\'s portion', 'sp': 140, 'bonus_type': 'two_stats', 'bonus_amount': 1},
        }
    },
    'battle_ration': {
        'name': 'battle ration',
        'symbol': ',', 'color': [160, 140, 100], 'weight': 1.0, 'min_level': 1,
        'source_monster': 'brigand', 'floor_spawn_weight': {},
        'unidentified_name': 'dried provisions',
        'recipes': {
            '0': {'name': 'ruined camp food',    'sp': 0,   'bonus_type': 'none',   'bonus_amount': 0},
            '1': {'name': 'camp stew',           'sp': 20,  'bonus_type': 'none',   'bonus_amount': 0},
            '2': {'name': 'soldier\'s meal',     'sp': 38,  'bonus_type': 'none',   'bonus_amount': 0},
            '3': {'name': 'hero\'s hardtack',    'sp': 60,  'bonus_type': 'random_stat', 'bonus_amount': 1},
            '4': {'name': 'veteran\'s feast',    'sp': 90,  'bonus_type': 'random_stat', 'bonus_amount': 1},
            '5': {'name': 'champion\'s rations', 'sp': 130, 'bonus_type': 'two_stats', 'bonus_amount': 1},
        }
    },
    'cultist_reagent': {
        'name': 'cultist reagent',
        'symbol': ',', 'color': [140, 60, 180], 'weight': 0.3, 'min_level': 6,
        'source_monster': 'dark_cultist', 'floor_spawn_weight': {},
        'unidentified_name': 'dark alchemical powder',
        'recipes': {
            '0': {'name': 'ruined dark brew',    'sp': 0,   'bonus_type': 'none',   'bonus_amount': 0},
            '1': {'name': 'bitter reagent tea',  'sp': 25,  'bonus_type': 'none',   'bonus_amount': 0},
            '2': {'name': 'dark tincture',       'sp': 45,  'bonus_type': 'none',   'bonus_amount': 0},
            '3': {'name': 'acolyte\'s elixir',   'sp': 70,  'bonus_type': 'stat',   'bonus_stat': 'INT', 'bonus_amount': 1},
            '4': {'name': 'void-touched brew',   'sp': 105, 'bonus_type': 'stat',   'bonus_stat': 'WIS', 'bonus_amount': 1},
            '5': {'name': 'dark ritual extract', 'sp': 150, 'bonus_type': 'two_stats', 'bonus_amount': 1},
        }
    },
    'devourer_tooth': {
        'name': 'devourer tooth',
        'symbol': ',', 'color': [200, 160, 80], 'weight': 1.0, 'min_level': 10,
        'source_monster': 'ammit_spawn', 'floor_spawn_weight': {},
        'unidentified_name': 'ancient carved fang',
        'recipes': {
            '0': {'name': 'ruined tooth powder', 'sp': 0,   'bonus_type': 'none',   'bonus_amount': 0},
            '1': {'name': 'tooth dust broth',    'sp': 30,  'bonus_type': 'none',   'bonus_amount': 0},
            '2': {'name': 'judge\'s marrow',     'sp': 55,  'bonus_type': 'none',   'bonus_amount': 0},
            '3': {'name': 'soul judge tincture', 'sp': 85,  'bonus_type': 'stat',   'bonus_stat': 'WIS', 'bonus_amount': 1},
            '4': {'name': 'devourer\'s essence', 'sp': 130, 'bonus_type': 'two_stats', 'bonus_amount': 1},
            '5': {'name': 'ammit\'s blessing',   'sp': 190, 'bonus_type': 'all_stats', 'bonus_amount': 1},
        }
    },
}

# ── 3. COMPOUND RECIPES (using only harvestable ingredients) ─────────────────

NEW_RECIPES = {
    # Tier 1 combinations (early game)
    'goblin_rat_stew': {
        'name': 'Goblin and Rat Stew',
        'ingredients': ['goblin_flesh', 'rat_meat'],
        'tier': 1, 'sp': 70, 'bonus_type': 'random_stat', 'bonus_amount': 1,
        'lore': 'A foul but filling stew. The dungeon has lower standards.'
    },
    'serpent_frog_bisque': {
        'name': 'Serpent and Frog Bisque',
        'ingredients': ['snake_meat', 'frog_legs'],
        'tier': 1, 'sp': 75, 'bonus_type': 'stat', 'bonus_stat': 'DEX', 'bonus_amount': 1,
        'lore': 'Two slippery creatures make a surprisingly agile meal.'
    },
    'bat_rat_soup': {
        'name': 'Cave Creature Broth',
        'ingredients': ['bat_wing', 'rat_meat'],
        'tier': 1, 'sp': 60, 'bonus_type': 'stat', 'bonus_stat': 'DEX', 'bonus_amount': 1,
        'lore': "The dungeon's most common inhabitants, simmered together."
    },
    'chitin_bone_crisps': {
        'name': 'Chitin and Bone Crisps',
        'ingredients': ['insect_carapace', 'bone_shard'],
        'tier': 1, 'sp': 55, 'bonus_type': 'stat', 'bonus_stat': 'CON', 'bonus_amount': 1,
        'lore': 'Crunchy. Nutritionally dubious. Surprisingly addictive.'
    },
    'goblin_bone_pottage': {
        'name': 'Goblin Bone Pottage',
        'ingredients': ['goblin_flesh', 'bone_shard'],
        'tier': 1, 'sp': 65, 'bonus_type': 'stat', 'bonus_stat': 'STR', 'bonus_amount': 1,
        'lore': 'A thick, grim pottage. Goblins eat this themselves, apparently.'
    },
    'spider_silk_jelly': {
        'name': 'Spider Silk Aspic',
        'ingredients': ['spider_silk', 'eye_jelly'],
        'tier': 2, 'sp': 85, 'bonus_type': 'stat', 'bonus_stat': 'PER', 'bonus_amount': 1,
        'lore': 'The silk dissolves into a trembling aspic. Enhances perception.'
    },
    'orc_bat_broth': {
        'name': "Orcish Cave Broth",
        'ingredients': ['orc_blood', 'bat_wing'],
        'tier': 2, 'sp': 80, 'bonus_type': 'stat', 'bonus_stat': 'STR', 'bonus_amount': 1,
        'lore': "Orcs make this on campaign. It's not good, but it works."
    },
    # Tier 2 combinations
    'gnoll_lion_ragout': {
        'name': 'Gnoll and Lion Ragout',
        'ingredients': ['gnoll_hide', 'lion_meat'],
        'tier': 2, 'sp': 100, 'bonus_type': 'stat', 'bonus_stat': 'STR', 'bonus_amount': 1,
        'lore': 'Two predators combined. Smells like a pride and a pack of gnolls fighting.'
    },
    'death_knight_broth': {
        'name': "Death Knight's Black Broth",
        'ingredients': ['charred_bone', 'zombie_flesh'],
        'tier': 2, 'sp': 95, 'bonus_type': 'stat', 'bonus_stat': 'CON', 'bonus_amount': 1,
        'lore': 'The Spartans had their black broth. This is darker.'
    },
    'hobgoblin_orc_stew': {
        'name': 'Regimental Stew',
        'ingredients': ['hobgoblin_blood', 'orc_blood'],
        'tier': 2, 'sp': 105, 'bonus_type': 'combat_stat', 'bonus_amount': 1,
        'lore': 'When goblinoid armies march, both bloods end up in the pot.'
    },
    'lizard_frog_ragout': {
        'name': 'Cave Amphibian Ragout',
        'ingredients': ['lizard_meat', 'frog_legs'],
        'tier': 1, 'sp': 72, 'bonus_type': 'stat', 'bonus_stat': 'DEX', 'bonus_amount': 1,
        'lore': 'Surprisingly delicate, if you can get past the skin.'
    },
    'bear_troll_haunch': {
        'name': 'Monstrous Meat Haunch',
        'ingredients': ['bear_meat', 'troll_hide'],
        'tier': 3, 'sp': 150, 'bonus_type': 'stat', 'bonus_stat': 'CON', 'bonus_amount': 1,
        'lore': 'Troll flesh regenerates even during cooking. Fortunately, this is tasty.'
    },
    'hobgoblin_ogre_feast': {
        'name': "Warlord's War Feast",
        'ingredients': ['hobgoblin_blood', 'ogre_hide'],
        'tier': 3, 'sp': 140, 'bonus_type': 'two_stats', 'bonus_amount': 1,
        'lore': 'The spoils of two brutal commanders, cooked together.'
    },
    'spectral_eye_consomme': {
        'name': 'Spectral Eye Consommé',
        'ingredients': ['spectral_essence', 'eye_jelly'],
        'tier': 3, 'sp': 120, 'bonus_type': 'stat', 'bonus_stat': 'WIS', 'bonus_amount': 1,
        'lore': 'You can see things clearly after eating this. Things you might prefer not to see.'
    },
    'shadow_crystal_broth': {
        'name': "Shadow-Walker's Broth",
        'ingredients': ['shadow_essence', 'shadow_crystal'],
        'tier': 3, 'sp': 130, 'bonus_type': 'status', 'bonus_effect': 'invisible', 'bonus_amount': 10,
        'lore': 'Solid shadows dissolved in darkness. Grants brief invisibility.'
    },
    'wisp_soul_risotto': {
        'name': "Will-o-Wisp Risotto",
        'ingredients': ['wisp_essence', 'soul_fragment'],
        'tier': 3, 'sp': 125, 'bonus_type': 'stat', 'bonus_stat': 'INT', 'bonus_amount': 1,
        'lore': 'Ethereal ingredients make for an ethereally potent dish.'
    },
    'bugbear_troll_roast': {
        'name': "Brute's Double Roast",
        'ingredients': ['bugbear_pelt', 'troll_hide'],
        'tier': 3, 'sp': 155, 'bonus_type': 'stat', 'bonus_stat': 'STR', 'bonus_amount': 1,
        'lore': 'Two of the dungeon\'s most feared brutes, slow-roasted until the rage leaves them.'
    },
    'spider_phase_silk_dish': {
        'name': 'Phased Silk Noodles',
        'ingredients': ['spider_silk', 'phase_silk'],
        'tier': 3, 'sp': 115, 'bonus_type': 'stat', 'bonus_stat': 'DEX', 'bonus_amount': 1,
        'lore': 'Normal and phase silk twined together. The noodles partially phase through your bowl.'
    },
    # Tier 3-4 combinations
    'demon_heart_roast': {
        'name': "Demon Heart Roast",
        'ingredients': ['demon_heart', 'demon_bile'],
        'tier': 4, 'sp': 180, 'bonus_type': 'two_stats', 'bonus_amount': 1,
        'lore': 'You should not be cooking this. And yet here you are.'
    },
    'elder_vampire_phylactery_elixir': {
        'name': "Undeath Synthesis Elixir",
        'ingredients': ['elder_vampire_blood', 'lord_phylactery'],
        'tier': 4, 'sp': 200, 'bonus_type': 'stat', 'bonus_stat': 'WIS', 'bonus_amount': 1,
        'lore': 'Undeath concentrated into a beverage. Technically not recommended.'
    },
    'cerebral_eye_pudding': {
        'name': "Mind Flayer's Pudding",
        'ingredients': ['cerebral_fluid', 'eye_jelly'],
        'tier': 4, 'sp': 190, 'bonus_type': 'two_stats', 'bonus_amount': 1,
        'lore': 'Mind flayers eat brains. You eat their fluid. Who is the apex predator now?'
    },
    'death_essence_soul_stew': {
        'name': "Death's Harvest Stew",
        'ingredients': ['death_essence', 'soul_fragment'],
        'tier': 4, 'sp': 195, 'bonus_type': 'stat', 'bonus_stat': 'CON', 'bonus_amount': 2,
        'lore': 'Harvested from the boundary of life and death. Reinforces your hold on existence.'
    },
    'troll_ogre_regeneration_broth': {
        'name': "Regeneration Broth",
        'ingredients': ['troll_regeneration_gland', 'ogre_hide'],
        'tier': 4, 'sp': 210, 'bonus_type': 'stat', 'bonus_stat': 'CON', 'bonus_amount': 2,
        'lore': "The troll gland still twitches in the pot. That's how you know it's working."
    },
    'dragon_fire_gland_elixir': {
        'name': "Dragon Blood Elixir",
        'ingredients': ['dragon_scale', 'fire_gland'],
        'tier': 4, 'sp': 220, 'bonus_type': 'two_stats', 'bonus_amount': 1,
        'lore': "Fire and scale — the essence of a dragon in one dangerous drink."
    },
    'chaos_void_brew': {
        'name': "Void Chaos Brew",
        'ingredients': ['chaos_essence', 'void_shard'],
        'tier': 4, 'sp': 200, 'bonus_type': 'random_stat', 'bonus_amount': 2,
        'lore': 'The effects are unpredictable, like everything touched by chaos and void.'
    },
    'cultist_arcane_tincture': {
        'name': "Arcane Cultist Tincture",
        'ingredients': ['cultist_reagent', 'arcane_bone_dust'],
        'tier': 3, 'sp': 145, 'bonus_type': 'stat', 'bonus_stat': 'INT', 'bonus_amount': 1,
        'lore': 'Dark sorcery and ancient bone powder, combined by a very brave cook.'
    },
    'changeling_puca_illusion_soup': {
        'name': "Fae Illusion Soup",
        'ingredients': ['changeling_glamour', 'puca_hair'],
        'tier': 3, 'sp': 135, 'bonus_type': 'status', 'bonus_effect': 'invisible', 'bonus_amount': 8,
        'lore': "The fae have always known secrets of concealment. This soup smells of both mischief and magic."
    },
    'drow_venom_tincture': {
        'name': "Drow Venom Tincture",
        'ingredients': ['drow_poison_extract', 'paralytic_venom'],
        'tier': 3, 'sp': 110, 'bonus_type': 'stat', 'bonus_stat': 'DEX', 'bonus_amount': 1,
        'lore': 'Drow spend centuries perfecting their venoms. A small amount, properly prepared, sharpens reflexes.'
    },
    # Tier 5 legendary
    'basilisk_medusa_grand_feast': {
        'name': "Gorgon's Grand Feast",
        'ingredients': ['basilisk_eye', 'medusa_blood'],
        'tier': 4, 'sp': 240, 'bonus_type': 'two_stats', 'bonus_amount': 2,
        'lore': "Both creatures turn things to stone with a glance. Cooked together, they give you eyes like theirs."
    },
    'chimera_dragon_roast': {
        'name': "Chimera and Dragon Roast",
        'ingredients': ['chimera_heart', 'dragon_scale'],
        'tier': 5, 'sp': 280, 'bonus_type': 'all_stats', 'bonus_amount': 1,
        'lore': 'Two of the most terrible predators in the deep. Their flesh combined is beyond transcendent.'
    },
    'lich_vampire_death_banquet': {
        'name': "The Undying Banquet",
        'ingredients': ['lord_phylactery', 'elder_vampire_blood'],
        'tier': 5, 'sp': 300, 'bonus_type': 'all_stats', 'bonus_amount': 1,
        'lore': 'Lich and vampire — two forms of cheating death. Together they may share their secret with you.'
    },
    'devourer_soul_judges_feast': {
        'name': "Ammit's Judgment Feast",
        'ingredients': ['devourer_tooth', 'soul_fragment'],
        'tier': 5, 'sp': 320, 'bonus_type': 'all_stats', 'bonus_amount': 1,
        'lore': "The Egyptian devourer weighs souls. Consuming her tooth alongside one grants the wisdom of judgment."
    },
    'pit_fiend_void_supremacy': {
        'name': "Infernal Void Supremacy",
        'ingredients': ['pit_fiend_scale', 'void_ichor'],
        'tier': 5, 'sp': 350, 'bonus_type': 'all_stats', 'bonus_amount': 1,
        'lore': 'The deepest evil and the deepest void. Those who survive eating this are changed forever.'
    },
    'troll_demon_brain_undying': {
        'name': "The Undying Formula",
        'ingredients': ['troll_regeneration_gland', 'demon_heart', 'death_essence'],
        'tier': 5, 'sp': 400, 'bonus_type': 'all_stats', 'bonus_amount': 2,
        'lore': "Regeneration, infernal fire, and the essence of death itself. The ultimate tonic of survival."
    },
    'philosophers_grand_banquet': {
        'name': "The Philosopher's Grand Banquet",
        'ingredients': ['chimera_heart', 'dragon_scale', 'lord_phylactery'],
        'tier': 5, 'sp': 500, 'bonus_type': 'all_stats', 'bonus_amount': 2,
        'lore': 'The apex of dungeon cuisine. Every great cook dreams of this dish. Most die attempting it.'
    },
    # More mid-tier combinations
    'shadow_bat_stew': {
        'name': "Cave Shadow Stew",
        'ingredients': ['shadow_fur', 'bat_wing'],
        'tier': 2, 'sp': 90, 'bonus_type': 'status', 'bonus_effect': 'invisible', 'bonus_amount': 6,
        'lore': 'Shadow hound and bat — both creatures of darkness. Their essence grants temporary concealment.'
    },
    'grub_goblin_bake': {
        'name': "Grub and Goblin Bake",
        'ingredients': ['insect_carapace', 'goblin_flesh'],
        'tier': 1, 'sp': 68, 'bonus_type': 'stat', 'bonus_stat': 'CON', 'bonus_amount': 1,
        'lore': 'Goblins eat grubs regularly. You\'re just cutting out the middleman.'
    },
    'lycan_troll_broth': {
        'name': "Feral Broth",
        'ingredients': ['lycanthrope_blood', 'troll_hide'],
        'tier': 4, 'sp': 175, 'bonus_type': 'stat', 'bonus_stat': 'STR', 'bonus_amount': 2,
        'lore': 'Werewolf and troll — two creatures defined by savage regeneration and strength.'
    },
    'raven_eagle_consomme': {
        'name': "Sky Hunter's Consommé",
        'ingredients': ['raven_feather', 'eagle_feather'],
        'tier': 3, 'sp': 120, 'bonus_type': 'stat', 'bonus_stat': 'PER', 'bonus_amount': 2,
        'lore': "The raven sees omens. The eagle sees clearly. Both feathers boiled grant exceptional sight."
    },
    'naga_python_scales': {
        'name': "Serpent Scales Supreme",
        'ingredients': ['naga_scale', 'python_scales'],
        'tier': 3, 'sp': 130, 'bonus_type': 'stat', 'bonus_stat': 'DEX', 'bonus_amount': 1,
        'lore': 'Two magnificent serpents. One divine, one natural. Scales from both, prepared with reverence.'
    },
    'owlbear_griffin_feast': {
        'name': "Chimeric Predator Feast",
        'ingredients': ['owlbear_feather', 'griffin_feather'],
        'tier': 4, 'sp': 200, 'bonus_type': 'two_stats', 'bonus_amount': 1,
        'lore': "Two hybrid creatures that shouldn't exist, combined into a meal that probably shouldn't exist either."
    },
    'barrow_embalming_stew': {
        'name': "Tomb Guardian Stew",
        'ingredients': ['barrow_dust', 'embalming_resin'],
        'tier': 3, 'sp': 110, 'bonus_type': 'stat', 'bonus_stat': 'CON', 'bonus_amount': 1,
        'lore': "Ancient preservatives and the dust of barrows. Your body becomes harder to destroy."
    },
    'wisp_shadow_brew': {
        'name': "Twilight Brew",
        'ingredients': ['wisp_essence', 'shadow_essence'],
        'tier': 3, 'sp': 125, 'bonus_type': 'stat', 'bonus_stat': 'WIS', 'bonus_amount': 1,
        'lore': 'Light and shadow at the boundary between worlds. Wisdom comes from understanding both.'
    },
    'orc_bugbear_conquest': {
        'name': "Conqueror's Pottage",
        'ingredients': ['orc_blood', 'bugbear_pelt'],
        'tier': 2, 'sp': 110, 'bonus_type': 'combat_stat', 'bonus_amount': 1,
        'lore': "Goblinoid warriors eat together before battle. You eat them after."
    },
}


def main():
    # Load files
    with open(MONSTERS_FILE, encoding='utf-8') as f:
        monsters = json.load(f)
    with open(INGREDIENT_FILE, encoding='utf-8') as f:
        ingredients = json.load(f)

    # ── Assign ingredient_ids ────────────────────────────────────────────────
    m_updated = 0
    for mid, assignment in MONSTER_INGREDIENT.items():
        if mid in monsters and not monsters[mid].get('ingredient_id'):
            monsters[mid]['ingredient_id'] = assignment
            m_updated += 1

    print(f'Monsters updated with ingredient_id: {m_updated}')
    still_missing = [v['name'] for v in monsters.values() if not v.get('ingredient_id')]
    print(f'Still missing: {len(still_missing)}')
    if still_missing:
        print('  Examples:', still_missing[:10])

    with open(MONSTERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(monsters, f, indent=2, ensure_ascii=False)

    # ── Add new ingredients ──────────────────────────────────────────────────
    i_added = 0
    for iid, idef in NEW_INGREDIENTS.items():
        if iid not in ingredients:
            ingredients[iid] = idef
            i_added += 1
    print(f'New ingredients added: {i_added}')
    with open(INGREDIENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(ingredients, f, indent=2, ensure_ascii=False)

    # ── Replace recipes with real-ingredient-only recipes ───────────────────
    # Remove old fake-herb recipes, keep any that use real ingredients
    all_ingredient_ids = set(ingredients.keys())
    valid_old = {}
    with open(RECIPE_FILE, encoding='utf-8') as f:
        old_recipes = json.load(f)
    for rid, rdef in old_recipes.items():
        ings = rdef.get('ingredients', [])
        if all(i in all_ingredient_ids for i in ings):
            valid_old[rid] = rdef

    # Merge: new recipes take priority
    final_recipes = {**valid_old, **NEW_RECIPES}
    print(f'Old valid recipes kept: {len(valid_old)}')
    print(f'New recipes added: {len(NEW_RECIPES)}')
    print(f'Total recipes: {len(final_recipes)}')
    with open(RECIPE_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_recipes, f, indent=2, ensure_ascii=False)

    print('\nDone! Cooking system updated.')


if __name__ == '__main__':
    main()
