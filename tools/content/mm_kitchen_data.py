"""The kitchen of the MONSTERS AND MAGIC kinds (slice M, 2026-11-19): read by
tools/content/add_mm_kinds_2026_11.py.

A distinctive creature gets its own part, in one single dish and two dishes
with common partners (tests/test_kitchen_rebuild.py; rule 4 of
tests/test_kitchen_part_freq.py). A deep part's dishes join it with an early
common part or a ration, so they span depths (cross_depth). The rows they lean
to are the thin ones of the tier census: SP, MP, CON, DEX, INT, PER, STR.

`picture`: an approved painted picture of the same kind of part (the kitchen
rebuild's rule: a thousand parts show some seventy pictures, each a part's
kind), copied to the new part's own file.

Offline tooling (not loaded at runtime).
"""
from __future__ import annotations

from mm_kinds_data import NEW


def ing(kind_id, name, part, nature, floor, colour, desc, picture, grant=None, power=None):
    d = {'name': name, 'symbol': '~', 'color': list(colour), 'weight': 0.25, 'min_level': floor,
         'tier_role': 'prime', 'nature': nature, 'part': part, 'description': desc,
         'identified': True, 'source_monster': kind_id, 'family': NEW[kind_id]['family']}
    if grant:
        d['stat_grant'] = grant
    if power:
        d['temp_power'] = power
    d.update(edible_safe=True, raw_sp=10)
    return {'id': f'{kind_id}_prime', 'def': d, 'picture': picture}


INGREDIENTS = [
    ing('mandrake', 'Mandrake Root-Stalk', 'wood', 'special', 12, (170, 140, 100),
        "The forked root of a mandrake, the old sleeping-draught of the physicians. Boiled right, "
        "it keeps you from being knocked senseless.", 'moss_sentinel_prime', power='save_guard_CON'),
    ing('kappa', 'Kappa Shell Steak', 'cut', 'stat', 11, (90, 150, 80),
        "Meat from under a kappa's shell, the river-imp that wrestles travellers. Turtle soup for a "
        "wrestler's strength of body.", 'giant_lizard_prime', grant='CON'),
    ing('eloko', 'Eloko Shinbone', 'bone', 'stat', 13, (110, 150, 60),
        "A shinbone from one of the biloko, the bell-ringing spirits of the Congo forest. They hear "
        "a hunter long before he hears them.", 'banshee_prime', grant='PER'),
    ing('ahuizotl', 'Ahuizotl Haunch', 'cut', 'stat', 16, (60, 60, 70),
        "Dark lake meat from the ahuizotl, the water beast that cries like a child to bait its trap. "
        "It sharpens the wits.", 'wolf_pack_leader_prime', grant='INT'),
    ing('bulgasari', 'Bulgasari Rice-Heart', 'core', 'stat', 18, (200, 200, 180),
        "The heart of a bulgasari, still the grains of rice a monk shaped it from, gone hard as iron. "
        "Boiled soft, it makes you hard to break.", 'clay_golem_prime', grant='CON'),
    ing('myrmekes', 'Jar of Gold-Ant Larvae', 'jar', 'sp', 44, (230, 210, 150),
        "Pale larvae from a gold-digging ant's nest, packed in a jar; the Aztecs ate ant larvae as a "
        "delicacy. Rich, buttery, and filling for days.", 'giant_spider_prime'),
    ing('vila', 'Vila Cloud-Mote', 'mote', 'mp', 45, (230, 230, 210),
        "A bright mote from a vila, the fairy of the mountain clouds who shoots arrows and heals "
        "heroes. It is the stuff of magic.", 'will_o_wisp_prime'),
    ing('taniwha', 'Taniwha Steak', 'cut', 'stat', 47, (60, 100, 90),
        "A steak from a taniwha, the water-dragon of the Maori rivers. Nothing breaks a river.",
        'sea_serpent_norse_prime', grant='CON'),
    ing('impundulu', 'Jarred Impundulu Fat', 'jar', 'special', 48, (60, 60, 60),
        "The fat of the lightning bird, dug from where lightning struck: a famous medicine. "
        "Lightning finds nothing to hold in one who eats it.", 'thunderbird_lesser_prime',
        power='shock_resist'),
    ing('mapinguari', 'Mapinguari Flank Steak', 'cut', 'stat', 49, (150, 80, 50),
        "A flank of the mapinguari, the one-eyed stinking beast of the Amazon. Smoke it long; the "
        "strength stays.", 'dire_lion_prime', grant='STR'),
    ing('preta', 'Preta Hunger-Ember', 'mote', 'sp', 50, (200, 120, 60),
        "An ember from a preta's needle-thin throat, where food turns to fire. Offered back as a "
        "meal, it fills the belly as nothing else.", 'soul_eater_prime'),
    ing('star_jelly', 'Star Jelly', 'bone', 'stat', 55, (220, 220, 240),
        "A trembling lump of pwdre ser, the rot of the stars, that melts in the light. Physicians "
        "once spread it on sores; eaten, it clears the head.", 'shade_prime', grant='INT'),
    ing('waq_waq_tree', 'Waq-Waq Fruit', 'forage', 'stat', 63, (150, 170, 90),
        "A fruit from the waq-waq tree at the edge of the world, shaped like a little sleeping face. "
        "It hears everything.", 'starnut', grant='PER'),
    ing('yacumama', 'Yacumama Steak', 'cut', 'stat', 70, (50, 80, 50),
        "A steak from the yacumama, the anaconda mother of the waters. One coil of it would crush a "
        "canoe.", 'world_serpent_prime', grant='STR'),
    ing('reem', "Re'em Sirloin", 'cut', 'sp', 85, (110, 70, 40),
        "A sirloin from the re'em, the wild ox as big as a hill. One slice is a day's meat for a "
        "village.", 'hell_bovine_prime'),
    ing('bakunawa', 'Bakunawa Moon-Scale', 'scale', 'stat', 88, (90, 70, 120),
        "A scale from the bakunawa, the serpent that swallows moons, still faintly bright. It moves "
        "like the sea.", 'lindworm_prime', grant='DEX'),
]


def dish(name, parts, benefit, flavour, art):
    return {'name': name, 'ingredients': list(parts), 'benefit': benefit, 'flavor': flavour, 'art': art}


RECIPES = {
    'cook_mandrake': dish('Mandrake Root Wine', ['mandrake_prime'], 'save_guard_CON',
                          "The sleep-root boiled in wine, the old way: now nothing knocks you senseless.",
                          'dish_drink_t1_special'),
    'dish_mm_mandrake_a': dish("Physician's Root Broth", ['mandrake_prime', 'healing_herb'],
                               'save_guard_CON', "Bitter and calming; your head stays clear when a blow lands.",
                               'dish_soup_t1_special'),
    'dish_mm_mandrake_b': dish('Mandrake and Apple Pickle', ['mandrake_prime', 'apple'], 'save_guard_CON',
                               "Sour and sharp; you will not be stunned or put to sleep easily.",
                               'dish_pickle_t1_special'),
    'cook_kappa': dish('Kappa Shell Soup', ['kappa_prime'], 'CON',
                       "Turtle soup from the river; you stand like a wrestler.", 'dish_soup_t1_stat'),
    'dish_mm_kappa_a': dish('River-Imp Hotpot', ['kappa_prime', 'wild_mushroom'], 'CON',
                            "Earthy and thick; you feel planted to the ground.", 'dish_stew_t1_stat'),
    'dish_mm_kappa_b': dish('Pond Shell Steak', ['kappa_prime', 'swamp_moss'], 'CON',
                            "Green-edged and chewy; nothing throws you easily.", 'dish_steak_t1_stat'),
    'cook_eloko': dish('Bell-Ringer Bone Broth', ['eloko_prime'], 'PER',
                       "Thin and grassy; afterwards every small sound is clear.", 'dish_soup_t1_stat'),
    'dish_mm_eloko_a': dish('Hollow-Tree Stew', ['eloko_prime', 'cave_mushroom'], 'PER',
                            "It smells of the forest floor; you notice things.", 'dish_stew_t1_stat'),
    'dish_mm_eloko_b': dish('Forest Spirit Platter', ['eloko_prime', 'hard_cheese'], 'PER',
                            "Bone, cheese and leaves; your eyes and ears sharpen.", 'dish_platter_t1_stat'),
    'cook_ahuizotl': dish('Roast Lake-Hound Haunch', ['ahuizotl_prime'], 'INT',
                          "Dark lake meat; you see the trick before it is played.", 'dish_roast_t1_stat'),
    'dish_mm_ahuizotl_a': dish("Fisherman's Haunch Stew", ['ahuizotl_prime', 'trail_rations'], 'INT',
                               "A fisherman's supper; your wits are quick.", 'dish_stew_t1_stat'),
    'dish_mm_ahuizotl_b': dish('Salt-Crusted Lake-Hound Steak', ['ahuizotl_prime', 'river_salt'], 'INT',
                               "Baked in salt; you think a move ahead.", 'dish_steak_t1_stat'),
    'cook_bulgasari': dish('Rice-Heart Cakes', ['bulgasari_prime'], 'CON',
                           "Chewy as iron and sweet as new rice; you feel hard to break.",
                           'dish_bread_t1_stat'),
    'dish_mm_bulgasari_a': dish('Iron-Rice Porridge', ['bulgasari_prime', 'bread_ration'], 'CON',
                                "Plain and heavy; it sits in you like an anvil.", 'dish_porridge_t1_stat'),
    'dish_mm_bulgasari_b': dish('Rice-Heart Fritters', ['bulgasari_prime', 'river_salt'], 'CON',
                                "Crisp outside, iron-hard within; you shrug off a blow.",
                                'dish_fritter_t1_stat'),
    'cook_myrmekes': dish('Gold-Ant Larvae Stew', ['myrmekes_prime'], 'sp',
                          "Buttery, nutty and rich as the gold they dug; it keeps you going for days.",
                          'dish_stew_t3_sp'),
    'dish_mm_myrmekes_a': dish("Gold-Digger's Trail Stew", ['myrmekes_prime', 'trail_rations'], 'sp',
                               "A raider's meal from the Indian desert; you could ride all day.",
                               'dish_stew_t3_sp'),
    'dish_mm_myrmekes_b': dish('Ant and Beetle Roast', ['myrmekes_prime', 'giant_beetle_prime'], 'sp',
                               "Crunchy and rich; hunger stays away a long while.", 'dish_roast_t3_sp'),
    'cook_vila': dish('Mountain Cloud Cordial', ['vila_prime'], 'mp',
                      "Cold as a mountain cloud; the spells come quicker.", 'dish_drink_t3_mp'),
    'dish_mm_vila_a': dish("Vila's Garland Chowder", ['vila_prime', 'elvish_bread'], 'mp',
                           "It smells of mountain flowers; your magic wells up.", 'dish_chowder_t3_mp'),
    'dish_mm_vila_b': dish('Cloud and Ember Jelly', ['vila_prime', 'imp_prime'], 'mp',
                           "White and red, cold and hot; the power hums in you.", 'dish_jelly_t3_mp'),
    'cook_taniwha': dish('Earth-Oven Taniwha Steak', ['taniwha_prime'], 'CON',
                         "Steamed under hot stones; you feel like a river nobody can dam.",
                         'dish_steak_t3_stat'),
    'dish_mm_taniwha_a': dish('River Guardian Stew', ['taniwha_prime', 'wild_mushroom'], 'CON',
                              "Dark and deep; it sits in you like a riverbed.", 'dish_stew_t3_stat'),
    'dish_mm_taniwha_b': dish('Taniwha and Lizard Roast', ['taniwha_prime', 'lizardfolk_prime'], 'CON',
                              "Two kinds of scale on one spit; you are hard to hurt.", 'dish_roast_t3_stat'),
    'cook_mapinguari': dish('Smoked Mapinguari Flank', ['mapinguari_prime'], 'STR',
                            "Smoked a whole day to kill the reek; the strength stays.", 'dish_steak_t3_stat'),
    'dish_mm_mapinguari_a': dish("Rubber-Tapper's Moqueca", ['mapinguari_prime', 'river_salt'], 'STR',
                                 "A fish-pot stew of the Amazon with a beast in it; your arms swell.",
                                 'dish_stew_t3_stat'),
    'dish_mm_mapinguari_b': dish('Two-Beast Roast', ['mapinguari_prime', 'owlbear_prime'], 'STR',
                                 "Two great beasts on one spit; you could lift a cart.", 'dish_roast_t3_stat'),
    'cook_impundulu': dish('Lightning-Fat Flambe', ['impundulu_prime'], 'shock_resist',
                           "It crackles in the pan; lightning finds nothing to hold.",
                           'dish_flambe_t3_special'),
    'dish_mm_impundulu_a': dish('Lightning Bird Pie', ['impundulu_prime', 'bread_ration'], 'shock_resist',
                                "The crust sparks when you cut it; storms pass you by.",
                                'dish_pie_t3_special'),
    'dish_mm_impundulu_b': dish('Two-Bird Storm Roast', ['impundulu_prime', 'harpy_prime'], 'shock_resist',
                                "Thunder on the tongue; lightning does not find you.",
                                'dish_roast_t3_special'),
    'cook_preta': dish('Ghost Festival Offering Stew', ['preta_prime'], 'sp',
                       "The Ghost Festival's meal, freely given; for once the hunger is filled.",
                       'dish_stew_t3_sp'),
    'dish_mm_preta_a': dish('Ember-Roasted Offering Loaf', ['preta_prime', 'bread_ration'], 'sp',
                            "Warm bread with a coal at its heart; you will not go hungry for a while.",
                            'dish_roast_t3_sp'),
    'dish_mm_preta_b': dish('Grave-Offering Stew', ['preta_prime', 'skeleton_prime'], 'sp',
                            "A meal set out for the dead and eaten by the living; it fills you up.",
                            'dish_stew_t3_sp'),
    'cook_star_jelly': dish('Star-Rot Pudding', ['star_jelly_prime'], 'INT',
                            "It trembles on the spoon and tastes of a cold night; your thoughts come clear.",
                            'dish_pudding_t3_stat'),
    'dish_mm_star_jelly_a': dish('Starfall Apple Pie', ['star_jelly_prime', 'apple'], 'INT',
                                 "Sweet apple under a shining glaze; you think more clearly.",
                                 'dish_pie_t3_stat'),
    'dish_mm_star_jelly_b': dish('Two-Jelly Platter', ['star_jelly_prime', 'ochre_jelly_prime'], 'INT',
                                 "Pale and yellow jellies side by side; your mind is sharp.",
                                 'dish_platter_t3_stat'),
    'cook_waq_waq_tree': dish('Waq-Waq Fruit Platter', ['waq_waq_tree_prime'], 'PER',
                              "It tastes of nothing you know and listens as you eat it.",
                              'dish_platter_t4_stat'),
    'dish_mm_waq_waq_tree_a': dish('Island Fruit Stew', ['waq_waq_tree_prime', 'hard_cheese'], 'PER',
                                   "Strange and sweet; afterwards you hear the smallest step.",
                                   'dish_stew_t4_stat'),
    'dish_mm_waq_waq_tree_b': dish('Roc and Fruit Roast', ['waq_waq_tree_prime', 'roc_chick_prime'], 'PER',
                                   "A roc chick stuffed with fruit from the edge of the world; your eyes "
                                   "miss nothing.", 'dish_roast_t4_stat'),
    'cook_yacumama': dish('Mother-of-Waters Steak', ['yacumama_prime'], 'STR',
                          "Dense as a coil; you could crush a canoe.", 'dish_steak_t4_stat'),
    'dish_mm_yacumama_a': dish('Salted Anaconda Stew', ['yacumama_prime', 'river_salt'], 'STR',
                               "Salted and slow-cooked; your grip tightens.", 'dish_stew_t4_stat'),
    'dish_mm_yacumama_b': dish('Great Serpent Stir-Fry', ['yacumama_prime', 'giant_lizard_prime'], 'STR',
                               "Two serpents in one pan; your arms are iron.", 'dish_stirfry_t4_stat'),
    'cook_reem': dish("Re'em Sirloin Roast", ['reem_prime'], 'sp',
                      "One slice is a day's meat for a village.", 'dish_roast_t5_sp'),
    'dish_mm_reem_a': dish('Wild Ox Pie', ['reem_prime', 'bread_ration'], 'sp',
                           "A pie the size of a cartwheel; you will not be hungry for days.",
                           'dish_pie_t5_sp'),
    'dish_mm_reem_b': dish('Hill-Beast Stew', ['reem_prime', 'cave_bear_prime'], 'sp',
                           "A stew of the two greatest beasts you know; it fills you for days.",
                           'dish_stew_t5_sp'),
    'cook_bakunawa': dish('Moon-Scale Soup', ['bakunawa_prime'], 'DEX',
                          "It shimmers like the moon on the sea; you move like the tide.",
                          'dish_soup_t5_stat'),
    'dish_mm_bakunawa_a': dish('Eclipse Night Stew', ['bakunawa_prime', 'trail_rations'], 'DEX',
                               "Dark and bright by turns; your feet are quick.", 'dish_stew_t5_stat'),
    'dish_mm_bakunawa_b': dish('Moon and Fire Stir-Fry', ['bakunawa_prime', 'drake_fire_prime'], 'DEX',
                               "A serpent's scale and a drake's fire in one pan; your hands are swift.",
                               'dish_stirfry_t5_stat'),
}

# Kin who share a part now say so in its description (a line on the end).
KIN_LINES = {
    'fionn_hound_prime': "The Cu-Sith, the green fairy hound of the Highlands, gives the same.",
    'talos_prime': "The bronze bulls of Colchis, Hephaestus's other work, give the same.",
    'night_hag_prime': "Likho the one-eyed, the Russian hag of ill luck, gives the same.",
    'vampire_prime': "The asanbosam of the Akan forest, iron-toothed, gives the same.",
    'hezrou_prime': "The nuckelavee of the Orkney shore gives the same.",
    'corrupted_treant_prime': "The upas tree of Java, whose sap is a dart poison, gives the same.",
    'giant_spider_prime': "The tsuchigumo, the earth spider of Japan, gives the same.",
    'iron_sentinel_prime': "The relic guardians of the Buddha's tomb give the same.",
    'plague_ooze_prime': "Eitr, the first poison of the world, gives the same.",
}
