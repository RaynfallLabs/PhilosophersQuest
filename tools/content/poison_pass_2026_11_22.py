"""The poison pass (Brandon, 2026-11-22: "posion is such a low number of
turns I barely noticed it; two damage? ... I think this is still rotated too
weak"; "Hold 3.6.1 for all"). The record of the venom each poison attack
does, by its lore, and of the six attacks whose lore is not venom.

Every kind is named with its lore class. Nothing is picked by a floor and
nothing is multiplied at runtime (LORE, NOT FLOOR): the number written is
the venom's damage a turn (src/venom.py), and it stays where it is.

How the numbers were drafted, once, before they were written here as they
stand: a mild venom (stench, spores, filth, a lycanthrope's bite) costs
about 12% of a typical hero's HP over one bite's turns where the kind is
most met; an ordinary venom about 20%; a deadly one by lore (cobra,
hydra, wyvern, the gorgons, Takshaka, eitr, Tiamat's blood, jorogumo...)
about 30%. The typical hero is the 3.6.0 simulator's committed kid (30 HP
on floor 1, 75 on 10, 177 on 30, 301 on 50, 554 on 90). Two rules on top:
a kind that lives on floors 1-5 keeps 1 a turn (the cobra's danger is its
long dose), and no venom is weaker than the old 2% tick was where it lives.

    py tools/content/poison_pass_2026_11_22.py          write
    py tools/content/poison_pass_2026_11_22.py --check  fail on drift

It is idempotent: it writes the values below, whatever was there.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import jsonfmt  # noqa: E402

# (kind, attack): (venom a turn, its lore class).   where it lives, one bite
VENOM = {
    ('cave_spider', 'Venomous Bite'): (1, 'ordinary'),                           # F1, 5 turns: one bite 17% of 30 HP
    ('dretch', 'Stench Cloud'): (1, 'mild'),                                     # F1, 4 turns: one bite 13% of 30 HP
    ('cobra', 'Venomous Bite'): (1, 'deadly'),                                   # F2, 6 turns: one bite 17% of 35 HP
    ('giant_centipede', 'Venomous Pinch'): (1, 'ordinary'),                      # F2, 5 turns: one bite 14% of 35 HP
    ('imp', 'Sting'): (1, 'ordinary'),                                           # F2, 5 turns: one bite 14% of 35 HP
    ('thorn_slinger', 'Thorn Volley'): (1, 'mild'),                              # F2, 4 turns: one bite 11% of 35 HP
    ('violet_fungus', 'Rotting Touch'): (1, 'mild'),                             # F2, 5 turns: one bite 14% of 35 HP
    ('web_spinner', 'Bite'): (1, 'ordinary'),                                    # F2, 4 turns: one bite 11% of 35 HP
    ('gas_spore', 'Explode'): (1, 'mild'),                                       # F3, 5 turns: one bite 12% of 40 HP
    ('quasit', 'Claws'): (1, 'ordinary'),                                        # F4, 5 turns: one bite 11% of 46 HP
    ('rutterkin', 'Bite'): (1, 'mild'),                                          # F4, 4 turns: one bite 9% of 46 HP
    ('toxic_jelly', 'Engulf'): (1, 'ordinary'),                                  # F4, 6 turns: one bite 13% of 46 HP
    ('swamp_serpent', 'Bite'): (1, 'ordinary'),                                  # F5, 6 turns: one bite 12% of 51 HP
    ('giant_wasp', 'Sting'): (2, 'ordinary'),                                    # F6, 6 turns: one bite 22% of 56 HP
    ('phase_spider_lesser', 'Phase Bite'): (2, 'ordinary'),                      # F7, 5 turns: one bite 17% of 60 HP
    ('greater_imp', 'Barbed Sting'): (2, 'ordinary'),                            # F9, 6 turns: one bite 17% of 70 HP
    ('lizardfolk_shaman', 'Venom Spit'): (2, 'ordinary'),                        # F9, 6 turns: one bite 17% of 70 HP
    ('ettercap', 'Bite'): (3, 'ordinary'),                                       # F12, 6 turns: one bite 21% of 85 HP
    ('ghast', 'Bite'): (2, 'mild'),                                              # F12, 5 turns: one bite 12% of 85 HP
    ('werewolf', 'Bite'): (2, 'mild'),                                           # F17, 8 turns: one bite 15% of 109 HP
    ('lindworm', 'Serpent Bite'): (4, 'deadly'),                                 # F18, 8 turns: one bite 28% of 114 HP
    ('sable_serpent', 'Venom Strike'): (3, 'ordinary'),                          # F21, 8 turns: one bite 19% of 130 HP
    ('bearded_devil', 'Beard Barbs'): (3, 'mild'),                               # F23, 5 turns: one bite 11% of 140 HP
    ('hydra', 'Many-Headed Bite'): (4, 'deadly'),                                # F23, 10 turns: one bite 29% of 140 HP
    ('phase_spider', 'Bite'): (5, 'ordinary'),                                   # F24, 6 turns: one bite 21% of 146 HP
    ('snake_charmer', 'Curved Khanjar'): (6, 'ordinary'),                        # F25, 5 turns: one bite 20% of 151 HP
    ('drow_priestess', 'Whip Strike'): (5, 'ordinary'),                          # F26, 6 turns: one bite 19% of 156 HP
    ('vrock', 'Spore Cloud'): (3, 'mild'),                                       # F26, 8 turns: one bite 15% of 156 HP
    ('weretiger', 'Bite'): (3, 'mild'),                                          # F26, 6 turns: one bite 12% of 156 HP
    ('naga_guardian', 'Bite'): (4, 'ordinary'),                                  # F27, 8 turns: one bite 20% of 161 HP
    ('naga_guardian', 'Poison Spit'): (5, 'ordinary'),                           # F27, 6 turns: one bite 19% of 161 HP
    ('basilisk', 'Bite'): (6, 'ordinary'),                                       # F28, 6 turns: one bite 22% of 167 HP
    ('hezrou', 'Claws'): (3, 'mild'),                                            # F28, 6 turns: one bite 11% of 167 HP
    ('otyugh', 'Tentacles'): (3, 'mild'),                                        # F28, 6 turns: one bite 11% of 167 HP
    ('fungal_horror', 'Spore Burst'): (3, 'mild'),                               # F29, 6 turns: one bite 10% of 172 HP
    ('manticore', 'Tail Spike'): (6, 'ordinary'),                                # F29, 6 turns: one bite 21% of 172 HP
    ('bone_devil', 'Sting'): (4, 'ordinary'),                                    # F30, 8 turns: one bite 18% of 177 HP
    ('cath_palug', 'Fey Bite'): (4, 'mild'),                                     # F30, 7 turns: one bite 16% of 177 HP
    ('nue', 'Chimeric Bite'): (6, 'ordinary'),                                   # F30, 6 turns: one bite 20% of 177 HP
    ('viper_priestess', 'Fang-Staff'): (6, 'ordinary'),                          # F31, 6 turns: one bite 20% of 182 HP
    ('wyvern', 'Stinger'): (7, 'deadly'),                                        # F31, 8 turns: one bite 31% of 182 HP
    ('medusa', 'Snake Bite'): (5, 'ordinary'),                                   # F32, 8 turns: one bite 21% of 188 HP
    ('erinyes_lesser', 'Longsword'): (8, 'ordinary'),                            # F33, 5 turns: one bite 21% of 193 HP
    ('greater_mimic', 'Venomous Tongue'): (4, 'mild'),                           # F33, 8 turns: one bite 17% of 193 HP
    ('young_black_dragon', 'Acid Breath'): (4, 'mild'),                          # F33, 6 turns: one bite 12% of 193 HP
    ('echidna', 'Bite'): (8, 'deadly'),                                          # F35, 8 turns: one bite 31% of 204 HP
    ('plague_witch', 'Miasma'): (4, 'mild'),                                     # F35, 6 turns: one bite 12% of 204 HP
    ('wyvern_greater', 'Stinger'): (8, 'deadly'),                                # F35, 8 turns: one bite 31% of 204 HP
    ('yuan_ti_pureblood', 'Bite'): (5, 'ordinary'),                              # F37, 8 turns: one bite 19% of 215 HP
    ('medusa_gorgon', 'Venom Strike'): (11, 'deadly'),                           # F38, 6 turns: one bite 30% of 220 HP
    ('euryale_gorgon', 'Serpent Hair'): (12, 'deadly'),                          # F40, 6 turns: one bite 31% of 231 HP
    ('stheno_gorgon', 'Serpent Hair'): (12, 'deadly'),                           # F40, 6 turns: one bite 31% of 231 HP
    ('wyrm', 'Bite'): (6, 'mild'),                                               # F42, 5 turns: one bite 12% of 245 HP
    ('dark_elf', 'Poisoned Dart'): (10, 'ordinary'),                             # F43, 5 turns: one bite 20% of 252 HP
    ('scarab_swarm', 'Devour'): (8, 'mild'),                                     # F45, 4 turns: one bite 12% of 266 HP
    ('unicorn_corrupted', 'Dark Horn Gore'): (5, 'mild'),                        # F46, 6 turns: one bite 11% of 273 HP
    ('werewolf_alpha', 'Alpha Bite'): (6, 'mild'),                               # F48, 6 turns: one bite 13% of 287 HP
    ('phase_spider_matriarch', 'Phase Bite'): (12, 'ordinary'),                  # F50, 5 turns: one bite 20% of 301 HP
    ('goblin_kingslayer', 'Envenomed Shortsword'): (16, 'deadly'),               # F52, 6 turns: one bite 31% of 312 HP
    ('upas_tree', 'Ipoh Sap'): (12, 'deadly'),                                   # F52, 8 turns: one bite 31% of 312 HP
    ('ammit_spawn', 'Crocodile Snap'): (6, 'mild'),                              # F53, 6 turns: one bite 11% of 317 HP
    ('pit_fiend_spawn', 'Bite'): (11, 'ordinary'),                               # F53, 6 turns: one bite 21% of 317 HP
    ('iron_golem', 'Toxic Gas Breath'): (12, 'ordinary'),                        # F60, 6 turns: one bite 20% of 355 HP
    ('jormungandr_juvenile', 'Venom Cloud'): (11, 'deadly'),                     # F64, 10 turns: one bite 29% of 381 HP
    ('nidhogg_brood', 'Shadow Spit'): (14, 'ordinary'),                          # F68, 6 turns: one bite 21% of 408 HP
    ('jormungandr_spawn', 'World-Venom Bite'): (13, 'deadly'),                   # F72, 10 turns: one bite 30% of 435 HP
    ('tsuchigumo', 'Earth Spider Fangs'): (11, 'ordinary'),                      # F72, 8 turns: one bite 20% of 435 HP
    ('locust_swarmlord', 'Swarm Call'): (9, 'mild'),                             # F74, 6 turns: one bite 12% of 449 HP
    ('takshaka_brood', "Takshaka's Venom"): (17, 'deadly'),                      # F74, 8 turns: one bite 30% of 449 HP
    ('infernal_lord', 'Corruption Wave'): (12, 'mild'),                          # F82, 5 turns: one bite 12% of 504 HP
    ('cerberus', 'Serpent Tail'): (13, 'ordinary'),                              # F83, 8 turns: one bite 20% of 510 HP
    ('seal_demon_pestilence', 'Plague Touch'): (13, 'ordinary'),                 # F83, 8 turns: one bite 20% of 510 HP
    ('eitr', 'Venom-Rime Touch'): (20, 'deadly'),                                # F86, 8 turns: one bite 30% of 529 HP
    ('wormwood_blight', 'Bitter Spore'): (13, 'ordinary'),                       # F87, 8 turns: one bite 19% of 535 HP
    ('khrafstra_swarm', 'Stings and Bites'): (13, 'mild'),                       # F88, 5 turns: one bite 12% of 541 HP
    ('mushmahhu', 'Seven-Headed Bite'): (18, 'ordinary'),                        # F88, 6 turns: one bite 20% of 541 HP
    ('mushmahhu', 'Spit of Venom-Blood'): (27, 'deadly'),                        # F88, 6 turns: one bite 30% of 541 HP
    ('geryon', 'Forked Sting'): (18, 'ordinary'),                                # F89, 6 turns: one bite 20% of 548 HP
    ('anansi', 'Venom'): (14, 'ordinary'),                                       # F90, 8 turns: one bite 20% of 554 HP
    ('tiamat_blood', 'Venom of the Eleven'): (28, 'deadly'),                     # F92, 6 turns: one bite 30% of 565 HP
    ('nidhoggr_fragment', 'Venom Spray'): (17, 'deadly'),                        # F93, 10 turns: one bite 30% of 571 HP
    ('dahaka_wyrm', 'Breath of Vermin'): (19, 'ordinary'),                       # F94, 6 turns: one bite 20% of 576 HP
    ('jorogumo', 'Venom Fangs'): (29, 'deadly'),                                 # F94, 6 turns: one bite 30% of 576 HP
}

# Not venom, by lore: these lay something else now (or nothing).
MOVED = {
    ('rotting_zombie', 'Claw'): None,                               # a filthy claw, no more
    ('plague_zombie', 'Claw'): 'diseased',                          # the plague it is named for
    ('rot_grub_swarm', 'Burrow'): 'diseased',                       # grubs that burrow and rot
    ('green_slime', 'Drip'): 'corroding',                           # it eats metal and wood
    ('gray_ooze', 'Pseudopod'): 'corroding',                        # it corrodes metal
    ('ochre_jelly', 'Pseudopod'): 'corroding',                      # acid
}
_RIDER = ('effect', 'effect_chance', 'effect_duration', 'venom', 'lethal')


def monsters_pass(data: dict) -> None:
    for (kind, name), (venom, _cls) in VENOM.items():
        hits = [a for a in data[kind]['attacks'] if a['name'] == name]
        if len(hits) != 1:
            raise SystemExit(f'{kind}: {len(hits)} attacks named {name!r}')
        if hits[0].get('effect') != 'poisoned':
            raise SystemExit(f'{kind} {name}: not a poison attack')
        hits[0]['venom'] = int(venom)
    for (kind, name), effect in MOVED.items():
        hits = [a for a in data[kind]['attacks'] if a['name'] == name]
        if len(hits) != 1:
            raise SystemExit(f'{kind}: {len(hits)} attacks named {name!r}')
        atk = hits[0]
        atk.pop('venom', None)
        if effect is None:
            for k in _RIDER:
                atk.pop(k, None)
        else:
            atk['effect'] = effect
    left = [(k, a['name']) for k, m in data.items() if isinstance(m, dict)
            for a in m.get('attacks') or () if a.get('effect') == 'poisoned' and not a.get('venom')]
    if left:
        raise SystemExit(f'poison attacks with no venom: {left}')


PASSES = {
    'data/monsters.json': monsters_pass,
}


def run(check: bool = False) -> list:
    drift = []
    for rel, fn in PASSES.items():
        path = os.path.join(ROOT, *rel.split('/'))
        data, fmt = jsonfmt.load(path)
        import copy
        before = copy.deepcopy(data)
        fn(data)
        if data == before:
            continue
        drift.append(rel)
        if not check:
            jsonfmt.save(path, data, fmt)
    return drift


if __name__ == '__main__':
    _check = '--check' in sys.argv
    _got = run(_check)
    print(('drifted: ' if _check else 'wrote: ') + (', '.join(_got) or 'nothing'))
    sys.exit(1 if _check and _got else 0)
