"""
The October 2026 invisible-monster pass (Brandon: "we should definitely have
some invisible enemies! not a ton, but it makes sense and fits lore").

Offline tooling (not loaded at runtime). Idempotent.

    python tools/content/add_invisible_monsters_2026_10.py            # report
    python tools/content/add_invisible_monsters_2026_10.py --write    # write data/monsters.json

then `python tools/balance/respawn_by_hp.py --write` seats the new monsters
on the floors their HP was built for (it changes nothing else).

Six creatures carry `invisible: true` (rules: src/unseen.py), spread over
the whole depth range and weighted toward the deep floors, where the
catalog audit (MONSTER_CATALOG_AUDIT.md) found stealth thinning out:

    floor ~1   Haunting Presence      existing: "no face and no voice"
    floor ~23  Dread Wraith           existing: reaches through from beyond sight
    floor ~42  Huldufolk Raider       new: Icelandic hidden folk
    floor ~62  Darkhelm Shade         new: the helm of Hades
    floor ~76  Whirlwind Jinni        new: jinn of the dust-devil
    floor ~90  Nibelung Hoard-Warden  new: Alberich's Tarnkappe

It also gives the two mimic-AI monsters the thing they pose as (`disguise`),
which the map draws until they spring.

LORE, NOT FLOOR: every number below is the creature's own, written for the
floor its story and HP put it on; nothing scales it in play. HP sits on the
respawn_by_hp anchor for the intended floor, attack averages on the
neighbours met there (measured 2026-10-17).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import jsonfmt  # noqa: E402

MONSTERS = ROOT / 'data' / 'monsters.json'

NEW = {
    'huldufolk_raider': {
        'name': 'Huldufolk Raider', 'symbol': 'h', 'color': [150, 160, 170],
        'hp': '120d10+330', 'speed': 12, 'ai_pattern': 'aggressive', 'thac0': 1,
        'peak_floor': 42, 'spread': 7, 'peak_weight': 2.0, 'min_level': 38,
        'attacks': [
            {'name': 'Hidden Knife', 'damage': '2d8+11', 'type': 'slash',
             'effect': 'bleeding', 'effect_chance': 0.3, 'effect_duration': 4},
            {'name': 'Led Astray', 'damage': '2d6+12', 'type': 'magic',
             'effect': 'confused', 'effect_chance': 0.35, 'effect_duration': 3},
        ],
        'resistances': ['cold'], 'weaknesses': ['holy'],
        'tags': ['fey', 'humanoid'], 'harvest_tier': 3,
        'treasure': {'gold': [60, 160], 'item_chance': 0.32, 'item_tier': 3},
        'lore': ("Icelanders tell of the huldufolk, the hidden people who live inside rocks and "
                 "hills, keep farms and churches of their own, and are seen only when they wish to "
                 "be. One story says Eve hid her unwashed children from God, and God decreed that "
                 "what was hidden from Him would be hidden from men. Road crews in Iceland still "
                 "bend a road round an elf rock rather than blast it. The raiders down here have "
                 "stopped waiting to be wronged. They walk beside a traveller unseen, lead him in "
                 "circles, and use the knife once he is lost."),
        'frequency': 2, 'prefers_flank': True, 'invisible': True,
    },
    'darkhelm_shade': {
        'name': 'Darkhelm Shade', 'symbol': 'W', 'color': [60, 60, 80],
        'hp': '280d10+860', 'speed': 12, 'ai_pattern': 'aggressive', 'thac0': -8,
        'peak_floor': 62, 'spread': 9, 'peak_weight': 2.0, 'min_level': 57,
        'attacks': [
            {'name': 'Spear of the Dead', 'damage': '3d8+20', 'type': 'pierce',
             'effect': 'bleeding', 'effect_chance': 0.25, 'effect_duration': 3},
            {'name': 'Grave Chill', 'damage': '2d8+21', 'type': 'cold',
             'effect': 'slowed', 'effect_chance': 0.35, 'effect_duration': 3},
        ],
        'resistances': ['cold', 'drain', 'poison', 'shadow'], 'weaknesses': ['holy', 'fire'],
        'tags': ['undead'], 'harvest_tier': 4,
        'treasure': {'gold': [110, 300], 'item_chance': 0.45, 'item_tier': 4},
        'lore': ("The Cyclopes forged three gifts for the sons of Kronos: the thunderbolt for Zeus, "
                 "the trident for Poseidon, and for Hades a helm of darkness that hid whoever wore "
                 "it. Athena put it on at Troy so that Ares never saw her spear coming, and Perseus "
                 "wore it to slip away from the Gorgons. Hades keeps a guard of the dead in lesser "
                 "copies of that helm and sends them after anyone who carries off what belongs "
                 "below. They still carry the long spears they were buried with. The living feel the "
                 "cold of the grave a moment before the point arrives."),
        'frequency': 2, 'invisible': True,
    },
    'whirlwind_jinni': {
        'name': 'Whirlwind Jinni', 'symbol': '&', 'color': [200, 180, 140],
        'hp': '385d10+2100', 'speed': 12, 'ai_pattern': 'aggressive', 'thac0': -13,
        'peak_floor': 76, 'spread': 9, 'peak_weight': 2.0, 'min_level': 71,
        'attacks': [
            {'name': 'Smokeless Fire', 'damage': '4d10+16', 'type': 'fire',
             'effect': 'burning', 'effect_chance': 0.4, 'effect_duration': 3},
            {'name': 'Dust-Devil Blow', 'damage': '3d8+22', 'type': 'physical',
             'effect': 'confused', 'effect_chance': 0.35, 'effect_duration': 3},
        ],
        'resistances': ['fire', 'poison'], 'weaknesses': ['holy', 'cold'],
        'tags': ['outsider', 'elemental'], 'harvest_tier': 4,
        'treasure': {'gold': [130, 320], 'item_chance': 0.6, 'item_tier': 5},
        'lore': ("The Qur'an says the jinn were made from smokeless fire, and that Iblis and his "
                 "tribe see men from where men cannot see them. Egyptian villagers told the "
                 "traveller Edward Lane that a jinni rides inside every dust-devil that spins "
                 "across the fields, and shouted 'Iron!' at one as it passed, because the jinn "
                 "fear iron. This one rides its whirlwind down the corridors. A blow comes out of "
                 "empty air, the dust settles, and by the time anyone turns it is somewhere else."),
        'frequency': 2, 'can_phase_blink': True, 'phase_blink_chance': 0.25,
        'invisible': True,
    },
    'nibelung_hoardwarden': {
        'name': 'Nibelung Hoard-Warden', 'symbol': 'h', 'color': [120, 120, 130],
        'hp': '480d12+3070', 'speed': 10, 'ai_pattern': 'aggressive', 'thac0': -17,
        'peak_floor': 90, 'spread': 12, 'peak_weight': 2.0, 'min_level': 84,
        'attacks': [
            {'name': 'Strength of Twelve', 'damage': '5d10+25', 'type': 'blunt',
             'effect': 'stunned', 'effect_chance': 0.3, 'effect_duration': 2},
            {'name': 'War Pick', 'damage': '4d8+20', 'type': 'pierce',
             'effect': 'bleeding', 'effect_chance': 0.4, 'effect_duration': 4},
        ],
        'resistances': ['cold', 'poison'], 'weaknesses': ['holy'],
        'tags': ['humanoid'], 'harvest_tier': 4,
        'treasure': {'gold': [220, 520], 'item_chance': 0.7, 'item_tier': 5},
        'lore': ("In the Nibelungenlied the dwarf Alberich guarded the Nibelung hoard wearing the "
                 "Tarnkappe, a cloak that hid its wearer from sight and gave him the strength of "
                 "twelve men. Siegfried wrestled it off him and took the treasure, and later stood "
                 "unseen beside King Gunther to win Brunhild's games for him. Alberich's sworn "
                 "wardens still keep what is left of the hoard, deep down, in cloaks cut from the "
                 "same cloth. Nobody sees a hoard-warden. You see a coin lift off the pile, and "
                 "then the pick."),
        'frequency': 2, 'invisible': True,
    },
}

# Existing creatures whose own lore already says nobody sees them.
MAKE_INVISIBLE = {
    'haunting_presence': (
        "Something terrible happened in this room, and a little of the person it happened to "
        "never left. The presence has no face and no voice. It is a cold spot, a held breath, the "
        "certainty of being watched from the corner. Then the dread arrives all at once, and "
        "strong men find themselves running before they have decided to. No one has ever seen "
        "it. Those with eyes for the unseen describe a grey smudge in the corner, about the "
        "height of whoever died there."),
    'dread_wraith': (
        "A wraith that has fed for centuries stops troubling to keep a shape anyone can see. "
        "The dread wraith stands half a step outside the world and reaches through it: a "
        "traveller feels the cold first, then the hand on his heart, and sees nothing at all. Old "
        "soldiers' advice was to swing at the cold. Its wail freezes the limbs, and the air round "
        "it stays dark and bitter long after it has gone. Fire and holy light find it where eyes "
        "cannot."),
}

# The mimic-AI monsters, drawn as what they imitate until they spring.
DISGUISES = {
    'lurking_horror': {'item': 'iron_chest', 'name': 'iron chest'},
    'gilded_mimic': {'item': 'dragon_hoard', 'name': 'spilled hoard'},
}


SIZES_PATH = ROOT / 'data' / 'monster_sizes.json'
# Body size from lore (corpse weight): the shade is a dead hoplite in bronze,
# the jinni is smokeless fire and leaves next to nothing.
SIZES = {'huldufolk_raider': 'medium', 'darkhelm_shade': 'medium',
         'whirlwind_jinni': 'tiny', 'nibelung_hoardwarden': 'medium'}


def apply_sizes(sizes: dict) -> list[str]:
    table = sizes['sizes']
    log = [f'{mid}: size {s}' for mid, s in SIZES.items() if table.get(mid) != s]
    if log:
        was_sorted = list(table) == sorted(table)
        table.update(SIZES)
        if was_sorted:
            sizes['sizes'] = dict(sorted(table.items()))
    return log


def apply(data: dict) -> list[str]:
    log = []
    for mid, d in NEW.items():
        if data.get(mid) != d:
            log.append(f'{mid}: {"updated" if mid in data else "added"}')
            data[mid] = dict(d)
    for mid, lore in MAKE_INVISIBLE.items():
        d = data[mid]
        if not d.get('invisible'):
            d['invisible'] = True
            log.append(f'{mid}: invisible')
        if d.get('lore') != lore:
            d['lore'] = lore
            log.append(f'{mid}: lore')
    for mid, disg in DISGUISES.items():
        if data[mid].get('disguise') != disg:
            data[mid]['disguise'] = dict(disg)
            log.append(f'{mid}: disguise {disg["item"]}')
    return log


def main():
    data, fmt = jsonfmt.load(MONSTERS)
    log = apply(data)
    print('\n'.join(log) or 'nothing to change')
    if '--write' in sys.argv and log:
        jsonfmt.save(MONSTERS, data, fmt)
        print('written', MONSTERS)
    sizes, sfmt = jsonfmt.load(SIZES_PATH)
    slog = apply_sizes(sizes)
    print('\n'.join(slog) or 'sizes: nothing to change')
    if '--write' in sys.argv and slog:
        jsonfmt.save(SIZES_PATH, sizes, sfmt)
        print('written', SIZES_PATH)


if __name__ == '__main__':
    main()
