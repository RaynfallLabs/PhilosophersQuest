"""
The pack kinds of 2026-11-19 (Brandon, 2026-11-18: "add packs that fight 2+
at a time, the more diverse and unique our monsters are, the better"; the
design he approved 2026-11-19: wolves, jackals, hyenas, ghouls, harpies and
hounds become pack kinds, and goblins sling then charge).

Offline tooling (not loaded at runtime). Idempotent.

    py tools/content/add_pack_kinds_2026_11.py            # report
    py tools/content/add_pack_kinds_2026_11.py --write    # write the data

The roster had a wolf pack leader, a dire wolf alpha and a winter wolf but no
ordinary wolf; Set's jackal (a gate boss) but no jackal; and no hyena. Three
new kinds, each written by the monster lore rubric
(docs/design/MONSTER_LORE_PASS_2026_11_19.md) against the hero of its floor
(34 HP and AC 9.6 on floor 2, 52 HP and AC 8.4 on floor 6, 134 HP and AC 3.0
on floor 22):

    jackal      floor ~2 (1-6): a small skirmisher, 1d4 bite (7% of the
                floor-2 hero), HP about half the floor's anchor, fast; its
                pack darts in and out by turns (data/packs.json 'dart').
    wolf        floor ~6 (4-10): a medium hunter, 1d6+1 bite (9%), HP 0.88 of
                the anchor, fast, lunges (opener); its pack hamstrings.
    cave_hyena  floor ~22 (18-26): the Ice Age hyena of the cave dens, bigger
                than the spotted hyena; a 2d8+5 bite (10%), HP 1.0 of the
                anchor; its clan harries the wounded.

Why the hyena is the cave hyena of tier 2 and not a spotted hyena of floors
6-14: the tier census (tools/balance/tier_census.py, the tier distribution
test; Brandon: every system spread across all five tiers) holds the ordinary
kinds to 35% in any tier, and tier 1 stood at 190 of 546 (34.8%). Two new
tier-1 kinds fit (192 of 549); a third tips it over. The gnolls, the
hyena-men of Yeenoghu, already hunt the shallow floors with the same trick.

And the goblin gets the Sling Stone his trick throws (1d3 blunt, ranged: a
caster or archer's 3-8% of the floor-1 hero). Its knife is unchanged.

LORE, NOT FLOOR: every number is the creature's own; nothing scales it in
play. Then run `py tools/balance/gold_by_lore.py --write` for the purse.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

MONSTERS = ROOT / 'data' / 'monsters.json'
SIZES = ROOT / 'data' / 'monster_sizes.json'
SENSES = ROOT / 'data' / 'senses.json'
HARVEST = ROOT / 'data' / 'items' / 'harvest_map.json'

NEW = {
    'jackal': {
        'name': 'jackal', 'symbol': 'd', 'color': [200, 160, 90],
        'hp': '4d4+4', 'speed': 14, 'ai_pattern': 'aggressive', 'thac0': 19,
        'peak_floor': 2, 'spread': 3, 'peak_weight': 6.0, 'min_level': 1,
        'attacks': [
            {'name': 'Snapping Bite', 'damage': '1d4', 'type': 'pierce', 'delivery': 'bite'},
        ],
        'resistances': [], 'weaknesses': [], 'tags': ['beast'],
        'family': 'great_beasts', 'pronoun': 'it', 'harvest_tier': 1,
        'treasure': {'gold': [0, 0], 'item_chance': 0.05, 'item_tier': 1, 'purse': 'none'},
        'lore': ("The Egyptians watched jackals nosing at the edges of their desert graves and made "
                 "the guardians of the dead jackals: Anubis, who weighs the heart, and Wepwawet, the "
                 "Opener of the Ways. In the Indian fables of the Panchatantra the jackal is the "
                 "trickster who wins by wit and never by strength. Golden jackals hunt in pairs and "
                 "small families, and none of them will stand and fight: each darts in to snap and is "
                 "gone again before the blow can fall, while its mate comes in from the other side."),
        'frequency': 6, 'thac0_lore': 20,
        'shrugs_off': [], 'status_immune': [], 'status_weak': ['fear_of_fire'],
        'pack': True, 'pack_size': [2, 3],
    },
    'wolf': {
        'name': 'wolf', 'symbol': 'w', 'color': [140, 140, 130],
        'hp': '7d8+8', 'speed': 14, 'ai_pattern': 'aggressive', 'thac0': 15,
        'peak_floor': 6, 'spread': 4, 'peak_weight': 6.0, 'min_level': 4,
        'attacks': [
            {'name': 'Bite', 'damage': '1d6+1', 'type': 'pierce', 'delivery': 'bite'},
        ],
        'resistances': [], 'weaknesses': [], 'tags': ['beast'],
        'family': 'great_beasts', 'pronoun': 'it', 'harvest_tier': 1,
        'treasure': {'gold': [0, 0], 'item_chance': 0.08, 'item_tier': 1, 'purse': 'none'},
        'lore': ("The grey wolf runs down deer and elk by working as a pack: the fastest hold the "
                 "quarry's eyes while the rest close on its flanks and go for the legs. Rome was "
                 "founded, the story goes, by twins a she-wolf suckled, and Norse warriors named their "
                 "sons for wolves. The dungeon wolves are the same lean grey hunters, and a passage "
                 "does not fool them: they will not file down a corridor into a sword one at a time, "
                 "but wait in the open for their prey to come to them."),
        'frequency': 6, 'thac0_lore': 16,
        'shrugs_off': [], 'status_immune': [], 'status_weak': ['fear_of_fire'],
        'pack': True, 'pack_size': [2, 3],
        'opener': {'attack': 'Bite', 'range': 1},
    },
    'cave_hyena': {
        'name': 'cave hyena', 'symbol': 'd', 'color': [170, 140, 90],
        'hp': '27d10+120', 'speed': 12, 'ai_pattern': 'aggressive', 'thac0': 10,
        'peak_floor': 22, 'spread': 4, 'peak_weight': 4.0, 'min_level': 18,
        'attacks': [
            {'name': 'Bone-Crushing Bite', 'damage': '2d8+5', 'type': 'pierce', 'delivery': 'bite'},
        ],
        'resistances': [], 'weaknesses': [], 'tags': ['beast'],
        'family': 'great_beasts', 'pronoun': 'it', 'harvest_tier': 2,
        'treasure': {'gold': [0, 0], 'item_chance': 0.1, 'item_tier': 2, 'purse': 'none'},
        'lore': ("In 1821 William Buckland crawled into Kirkdale Cave in Yorkshire and found its floor "
                 "covered in the gnawed bones of elephants, rhinoceroses and hippopotamuses. From the "
                 "tooth marks and the droppings he worked out what had happened: for thousands of years "
                 "the cave had been a hyena den, and the hyenas had dragged their kills inside. The cave "
                 "hyena of the Ice Age was bigger and heavier than the spotted hyena of Africa, its jaws "
                 "cracked the bones of woolly rhinos, and its clans ran horses down for miles. Down here "
                 "the breed never died out. A clan hangs back from strong prey, whooping to the rest, "
                 "and closes in on anything that bleeds."),
        'frequency': 4, 'thac0_lore': 11,
        'shrugs_off': [], 'status_immune': [], 'status_weak': ['fear_of_fire'],
        'pack': True, 'pack_size': [3, 4],
    },
}

SIZE = {'jackal': 'small', 'wolf': 'medium', 'cave_hyena': 'large'}

# Close kin share one ingredient (data/items/harvest_map.json): a wolf and a
# jackal (both Canis, the wild dogs) are butchered as the pack leader is; a
# cave hyena gives the hyena meat the gnolls' sausages were always made of.
# Their descriptions say so (data/items/ingredient.json).
HARVEST_TO = {'wolf': 'wolf_pack_leader_prime', 'jackal': 'wolf_pack_leader_prime',
              'cave_hyena': 'gnoll_prime'}
INGREDIENTS = ROOT / 'data' / 'items' / 'ingredient.json'
DESCRIPTIONS = {
    'wolf_pack_leader_prime': ("A steak from the wild dogs of the dungeon: grey wolves, jackals, the "
                               "leaders of the wolf packs and the dire wolf alphas. Lean, red and wild."),
    'gnoll_prime': ("Hyena-meat sausages, from the cave hyenas themselves or from the gnolls, the "
                    "laughing pack-hunters of Yeenoghu. They eat everything, always."),
}

SLING = {'name': 'Sling Stone', 'damage': '1d3', 'type': 'blunt', 'delivery': 'ranged', 'ranged': True}


def _dump(path, d, indent: int):
    path.write_text(json.dumps(d, indent=indent, ensure_ascii=False) + '\n', encoding='utf-8')


def main(argv) -> int:
    write = '--write' in argv
    mons = json.loads(MONSTERS.read_text(encoding='utf-8'))
    changed = []
    for kid, defn in NEW.items():
        if mons.get(kid) != defn:
            # A re-run keeps the treasure purse gold_by_lore.py wrote.
            old = mons.get(kid) or {}
            fresh = dict(defn)
            if old.get('treasure'):
                fresh['treasure'] = old['treasure']
            if old != fresh:
                mons[kid] = fresh
                changed.append(kid)
    gob = mons['goblin']
    if not any(a.get('name') == SLING['name'] for a in gob['attacks']):
        gob['attacks'].append(dict(SLING))
        changed.append('goblin (Sling Stone)')
    sizes = json.loads(SIZES.read_text(encoding='utf-8'))
    for kid, sz in SIZE.items():
        if sizes['sizes'].get(kid) != sz:
            sizes['sizes'][kid] = sz
            changed.append(f'size {kid}')
    senses = json.loads(SENSES.read_text(encoding='utf-8'))
    for kid in NEW:
        if senses['monsters'].get(kid) != ['scent']:
            senses['monsters'][kid] = ['scent']
            changed.append(f'scent {kid}')
    harvest = json.loads(HARVEST.read_text(encoding='utf-8'))
    for kid, ing in HARVEST_TO.items():
        if harvest['monsters'].get(kid) != ing:
            harvest['monsters'][kid] = ing
            changed.append(f'harvest {kid}')
    if list(harvest['monsters']) != sorted(harvest['monsters']):
        harvest['monsters'] = dict(sorted(harvest['monsters'].items()))   # kept in order
        changed.append('harvest order')
    ings = json.loads(INGREDIENTS.read_text(encoding='utf-8'))
    for iid, text in DESCRIPTIONS.items():
        if ings[iid].get('description') != text:
            ings[iid]['description'] = text
            changed.append(f'description {iid}')
    print('changes:', ', '.join(changed) if changed else 'none')
    if write and changed:
        # (each file as it is laid out: monsters, senses and ingredients by
        # two spaces, sizes and the harvest map by one)
        _dump(MONSTERS, mons, 2)
        _dump(SIZES, sizes, 1)
        _dump(SENSES, senses, 2)
        _dump(HARVEST, harvest, 1)
        _dump(INGREDIENTS, ings, 2)
        print('written')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
