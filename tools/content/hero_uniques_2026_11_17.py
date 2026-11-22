"""Four Secret Builds carry their own legend's piece (Brandon, 2026-11-17:
"yes, ok to give uniques that are lore accurate to special builds").

Offline content pass over data/items/shield.json and weapon.json, the record
of what was done. Idempotent. Each piece REPLACES the plain starting piece of
its build (src/welcome_screen.py), is a unique that is never random loot
(min_level 9999, no spawn weight: items.scripted_only_ids, so traders refuse
it and thieves skip it), and does ONE thing beyond its AC or its blows:

  * The Shield of Achilles (Achilles, for the Oak Light Shield). Hephaestus
    made it at Thetis' asking (Iliad 18): the earth, sea and sky, two cities,
    the ploughing and the harvest, the river Ocean round the rim, five layers
    beneath (two bronze, two tin, one gold). Aeneas' spear stuck in its gold
    (Iliad 20.267-272) and Hector's leapt back from it (22.289-291): points
    that pierce do half their damage (damage_resistances pierce 0.5). A great
    round shield (heavy_wooden), tier 3 like his spear (Brandon, 2026-11-17):
    AC 2 + 3.
  * The Shield of Ilion (Alexander, for the Bronze Heavy Shield). Arrian 1.11:
    at Troy he dedicated his own armour to Athena and took down sacred arms
    kept from the Trojan War, which his shield-bearers carried before him;
    6.10: Peucestas held the sacred shield from Troy over him when he fell
    among the Malli. Once a floor, the blow that leaves the hero at a quarter
    of his health or less finds him under it: Shielded for 5 turns
    (fallen_cover_turns, Player.take_damage). A bronze aspis, tier 1: AC 2 + 1.
  * Boudicca's Spear (Boudicca, for the iron longsword). Cassius Dio 62.2: she
    "grasped a spear to aid her in terrifying all beholders". Each hit has a
    25% chance to frighten its target (effects: feared, 4 turns; what has no
    mind, and what is fearless, is not frightened: Monster.hold). A war spear
    of a mortal queen, the peer of the Dory of Leonidas and the Spear of
    Romulus: maths tier 2 (its own, fixed), base 30, reach 2, one hand.
  * Joan of Arc's Standard (Joan, in the off hand, where no shield was).
    At her trial (27 February 1431) she said she loved it forty times more
    than her sword and carried it herself in the charge so as to kill no one:
    white, sown with lilies, the Lord holding the world between two angels,
    Jhesus Maria. A standard, not a shield (`standard`: gear.is_standard): no
    AC, no plus, nothing to wear away. Its power is her men's: pets and allies
    the hero can see hit harder (rally_damage_mult 1.5,
    CombatMixin._rally_mult). It strikes no one; her sword stays her weapon.

Sources: Grokipedia first, Wikipedia second; the primary texts on Perseus
(Iliad), Wikisource (Arrian, Chinnock), LacusCurtius (Dio, Cary) and the
Fordham trial record (Barrett; Scott's "forty times").

    py tools/content/hero_uniques_2026_11_17.py [--write]
    py tools/content/unique_armor_ladder_2026_11.py --check   # must report no change
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jsonfmt  # noqa: E402

ITEMS = os.path.join(ROOT, 'data', 'items')

_NEVER_ROLLED = {'1-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0}

SHIELDS = {
    'shield_of_achilles': {
        'name': 'Shield of Achilles',
        'symbol': ')',
        'color': [205, 160, 70],
        'weight': 12.0,
        'min_level': 9999,
        'tier': 3,
        'material': 'bronze',
        'ac_bonus': 2,
        'enchant_bonus': 3,
        'ench_level': 6,
        'equip_threshold': 6,
        'quiz_tier': 3,
        'damage_resistances': {'pierce': 0.5},
        'can_be_cursed': False,
        'cursed': False,
        'identified': False,
        'id_level': 0,
        'unidentified_name': 'a great round shield worked with tiny figures, a river running round its rim',
        'lore': ("When Patroclus had fallen in the armour of Achilles, the sea-goddess Thetis went up to Olympus for her son's sake, and at her asking Hephaestus the smith made this shield in a single night. He wrought upon it earth, sea and sky, with the sun, the moon and the stars, two cities, one at a wedding and one under siege, men at the plough and at the reaping, and about the rim the river Ocean. Beneath these he laid five layers, two of bronze, two of tin and one of gold, and in the battles that followed the spear of Aeneas passed through two of them and was stayed by the gold, and the spear of Hector leapt back from its face."),
        'floorSpawnWeight': dict(_NEVER_ROLLED),
        'is_unique': True,
        'template_basis': 'heavy_wooden',
        'peak_floor': 0,
        'spread': 10,
        'peak_weight': 0.0,
        'max_enchant': 3,
        'value': 4000,
        'containerLootTier': 'legendary',
    },
    'shield_of_ilion': {
        'name': 'Shield of Ilion',
        'symbol': ')',
        'color': [120, 150, 110],
        'weight': 10.0,
        'min_level': 9999,
        'tier': 1,
        'material': 'bronze',
        'ac_bonus': 2,
        'enchant_bonus': 1,
        'ench_level': 2,
        'equip_threshold': 5,
        'quiz_tier': 1,
        'damage_resistances': {},
        'fallen_cover_turns': 5,
        'can_be_cursed': False,
        'cursed': False,
        'identified': False,
        'id_level': 0,
        'unidentified_name': 'an ancient round bronze shield, worn smooth and green with age',
        'lore': ("Alexander, when first he came into Asia, went up to Troy and sacrificed to Athena of Ilion, and he hung his own armour in her temple and took in its stead some of the sacred arms that had lain there since the Trojan War. From that day his shield-bearers carried this shield before him into battle. Long afterward in India he leapt down within the wall of a town of the Malli with but three men beside him, and an arrow passed through his breastplate into his chest. He fell, and Peucestas stood over him with the sacred shield of Troy until the Macedonians broke in, and so the king lived, as the historian Arrian has set down."),
        'floorSpawnWeight': dict(_NEVER_ROLLED),
        'is_unique': True,
        'template_basis': 'heavy_wooden',
        'peak_floor': 0,
        'spread': 10,
        'peak_weight': 0.0,
        'max_enchant': 2,
        'value': 2500,
        'containerLootTier': 'legendary',
    },
    'joans_standard': {
        'name': "Joan of Arc's Standard",
        'symbol': ')',
        'color': [240, 236, 220],
        'weight': 5.0,
        'min_level': 9999,
        'tier': 1,
        'material': 'linen',
        'ac_bonus': 0,
        'enchant_bonus': 0,
        'equip_threshold': 4,
        'quiz_tier': 1,
        'damage_resistances': {},
        'standard': True,
        'rally_damage_mult': 1.5,
        'can_be_cursed': False,
        'cursed': False,
        'identified': False,
        'id_level': 0,
        'unidentified_name': 'a long white banner on a pole, sown with gold lilies',
        'lore': ("At the bidding of her Voices, Joan of Arc had this standard made at Tours in 1429, of white sown with gold lilies, showing the Lord with the world in His hand and an angel on either side, and bearing the names Jhesus Maria. At Orléans she bade her soldiers watch it, and when its tail touched the wall of the English fort they went over and took the place. Afterward, when her judges asked whether she loved better her standard or her sword, she answered that she loved the standard forty times more, and that she bore it herself in the charge so that she might kill no one."),
        'floorSpawnWeight': dict(_NEVER_ROLLED),
        'is_unique': True,
        'peak_floor': 0,
        'spread': 10,
        'peak_weight': 0.0,
        'max_enchant': 0,
        'value': 1500,
        'containerLootTier': 'legendary',
    },
}

_SPEAR_CHAIN = [0.75, 0.9, 1.0, 1.3, 1.75]

WEAPONS = {
    'boudicca_spear': {
        'name': "Boudicca's Spear",
        'class': 'spear',
        'variant': 'reach',
        'tier': 2,
        'material': 'iron',
        'mathTier': 2,
        'baseDamage': 30,
        'chainMultipliers': list(_SPEAR_CHAIN),
        'maxChainLength': 5,
        'damageTypes': ['pierce'],
        'symbol': '/',
        'color': [150, 150, 160],
        'weight': 4.0,
        'twoHanded': False,
        'reach': 2,
        'stunChance': 0.0,
        'bleedChance': 0.0,
        'requiresAmmo': None,
        'floorSpawnWeight': dict(_NEVER_ROLLED),
        'containerLootTier': 'legendary',
        'value': 900,
        'min_level': 9999,
        'identified': False,
        'unidentified_name': 'a long iron-headed spear with a bronze collar of curling swirls',
        'lore': ("When the husband of Boudicca, queen of the Iceni in eastern Britain, was dead, the officers of Rome seized his kingdom, had her flogged and abused her daughters, and she raised the tribes against them. The Roman historian Cassius Dio has described how she stood before her army, very tall, fierce of glance and harsh of voice, with tawny hair falling to her hips and a great torc of gold at her throat, and how she took up a spear to strike terror into all who beheld her, and then spoke to them. Afterward her army burned Camulodunum, Londinium and Verulamium before the legions could put an end to the rising."),
        'quiz_tier': 2,
        'damage_types': ['pierce'],
        'template_basis': 'spear',
        'spread': 8,
        'peak_floor': 0,
        'chain_multipliers': list(_SPEAR_CHAIN),
        'peak_weight': 0.0,
        'base_damage': 30,
        'max_chain_length': 5,
        'is_unique': True,
        'max_enchant': 2,
        'weapon_class_chain': 'heavy',
        'can_be_cursed': False,
        'effects': {'status': 'feared', 'effect_chance': 0.25, 'effect_duration': 4},
        'design_notes': ("Boudicca's own spear (Brandon, 2026-11-17). What it IS, from Cassius Dio "
                         "62.2: the spear she grasped 'to aid her in terrifying all beholders'. "
                         "What belongs to it: terror (effects feared, 25% a hit, 4 turns; the "
                         "mindless and the fearless are not frightened, Monster.hold). A mortal "
                         "queen's war spear, the peer of the Dory of Leonidas and the Spear of "
                         "Romulus: maths tier 2 (its own, fixed), base 30. Never random loot "
                         "(min_level 9999, no spawn weight)."),
        'id_level': 0,
        'chain_exponent': 1.15,
    },
}


def _merge(path: str, entries: dict, write: bool) -> bool:
    data, fmt = jsonfmt.load(path)
    changed = False
    for k, e in entries.items():
        if data.get(k) != e:
            data[k] = e
            changed = True
    if changed and write:
        jsonfmt.save(path, data, fmt)
    return changed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args(argv)
    ch = [_merge(os.path.join(ITEMS, 'shield.json'), SHIELDS, a.write),
          _merge(os.path.join(ITEMS, 'weapon.json'), WEAPONS, a.write)]
    print('shield.json', 'changed' if ch[0] else 'unchanged',
          '| weapon.json', 'changed' if ch[1] else 'unchanged',
          '(written)' if a.write else '(dry run)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
