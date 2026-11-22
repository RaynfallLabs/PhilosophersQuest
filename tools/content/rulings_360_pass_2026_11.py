"""Brandon's rulings on the 3.6.0 bug bash, the data (2026-11-22: "All as
recommended"; BUGBASH_3_6_0_REPORT_2026_11_22.md).

Group B, monsters that are what their lore says:
  B1  the Ochre Jelly divides under an edge or lightning
  B3  the Grick's hide turns blade and point
  B5  the Crypt Thing's attack is named for what it does (the real teleport
      is for later)
  B6  the Blink Dog blinks; the Xorn bargains for gold or treasure (walking
      through walls stays legend)
  B7  both Sphinxes ask one philosophy question, at their depth's tier
  B8  the Redcap is weak to holy
  B10 the Shadow Assassin and Shadow Archer are weak to holy
  B12 the Ushabti Overseer's workers fall still with it
  B13 skeletal_archer is named the Skeleton Bowman (its id stays)

Group C, items that do what their lore says:
  C1  the Sailor's Amulet lends warning beside its cold resistance
  C7  the Soul Reaver's dead growth flag is gone
  C9  the Samosek strikes back by itself, one blow taken in four
  C10 the T5 Chandrahasa is retired: the T4 Chandrahas holds the legend's
      condition (items.RETIRED_IDS reads the old id)
  C11 Pandora's Box and Aladdin's Lamp are parked
  C12 the healing herb stops bleeding
  C14 the Shamshir-e Zomorrodnegar lends magic resistance in the hand
  C15 Omnisight's book says what it shows

    py tools/content/rulings_360_pass_2026_11.py            # report (dry run)
    py tools/content/rulings_360_pass_2026_11.py --write

Idempotent and format-preserving (jsonfmt.py). Run affinity_pass.py --write
after it: the forms come from data/family_affinity.json.
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))

MONSTERS = 'data/monsters.json'
AFFINITY = 'data/family_affinity.json'
INGREDIENTS = 'data/items/ingredient.json'
WEAPONS = 'data/items/weapon.json'
ACCESSORIES = 'data/items/accessory.json'
FOOD = 'data/items/food.json'
BOOKS = 'data/items/spellbook.json'
ARTIFACTS = 'data/items/artifact.json'      # no exact round trip: edited as text (park)

_SPHINX_TELL = {
    'sign': "{The} watches the way, and looks about to ask you something.",
    'does': "{He} asks one riddle: a good answer lets you pass, and a poor one brings "
            "{his} curse down on you.",
    'counter': "Press D and answer well: it is a question of philosophy.",
}


def _sphinx(name: str, tier: int) -> dict:
    return {
        'subject': 'philosophy',
        'tier': tier,
        'storm': 'Riddle Curse',
        'call': f"The {name} lifts her head and asks her riddle. Answer well and she lets you pass.",
        'right': f"The {name} bows her head at your answer, and lets you pass.",
        'wrong': f"Your answer will not do, and the {name} readies the curse of her riddle!",
        'unasked': f"The {name} will wait no longer for an answer.",
        'tell': _SPHINX_TELL,
    }


# kind -> the fields set (a dict or a list is written whole).
FIELDS = {
    'ochre_jelly': {'splits': {'by': ['slash', 'lightning'], 'max': 6}},    # as the black pudding
    'blink_dog': {'can_phase_blink': True, 'phase_blink_chance': 0.25},     # the commonest chance
    'xorn': {'parley': {
        'toll': True,
        'call': "The Xorn sniffs at your pack and holds out a stony hand. For gold or gems it will let you be.",
        'prompt': "Press D to bargain, or keep away.",
        'right': "The Xorn crunches up what you paid and turns away, content to let you be.",
        'wrong': "Denied its prize, the Xorn comes for you!",
        'unasked': "The Xorn will wait no longer for its gold.",
        'tell': {
            'sign': "{The} sniffs at your pack as if it smelt something to eat there.",
            'does': "{He} will let you be for gold or gems, and fights if {his} prize is denied.",
            'counter': "Press D and pay what {he} asks in gold or treasure.",
        },
    }},
    'sphinx': {'parley': _sphinx('Sphinx', 2)},                 # floors 31-42: the second band
    'sphinx_lesser': {'parley': _sphinx('Lesser Sphinx', 3)},   # floors 40-51: the third
    'ushabti_overseer': {'summons_fall': {
        'line': "With {the} broken, the workers it called fall still.",
    }},
    'skeletal_archer': {'name': 'skeleton bowman'},
}

# kind -> a weakness added to its own list (holy stays only on the unholy:
# see CURSED).
WEAK = {'redcap': 'holy', 'shadow_assassin': 'holy', 'shadow_archer': 'holy'}

ATTACK_NAMES = {'crypt_thing': {'Teleport': 'Bewilder'}}

# (file, id) -> the item fields set.
ITEM_FIELDS = {
    (WEAPONS, 'kladenets'): {'counter_attack_chance': 0.25},
    (WEAPONS, 'shamshir_e_zomorrodnegar'): {'on_equip_status': 'magic_resist'},
    (ACCESSORIES, 'sailors_amulet'): {
        'effects': {'status': 'cold_resist', 'status2': 'warning', 'duration': -1}},
    (FOOD, 'healing_herb'): {'stops': ['bleeding']},
}
DROP_FIELDS = [(WEAPONS, 'soul_reaver', 'growth_on_innocent_kill'),
               (WEAPONS, 'kladenets', '_note')]
RETIRED = [(WEAPONS, 'chandrahasa')]
PARKED = ('pandoras_box', 'aladdins_lamp')

# (file, kind, field): the words as they stood, the words now.
WORDS = [
    (ACCESSORIES, 'sailors_amulet', 'lore',
     "and its wearer bears wind and wave as a sailor does, and does not mind the cold.",
     "and its wearer feels trouble coming as a sailor feels the weather, and does not mind the cold."),
    (FOOD, 'healing_herb', 'lore',
     "do little for hunger but something to mend a hurt.",
     "do little for hunger but a great deal to staunch bleeding."),
    (WEAPONS, 'kladenets', 'lore',
     "which in their tales fights of itself",
     "which fights of itself"),
    (WEAPONS, 'kladenets', 'lore',
     "but it leaps so readily to the hand, and stuns so many of those it strikes, that they count "
     "it very useful.",
     "but since the sword does the fighting and they live through it, they take no fright at its "
     "having a will of its own, and count it very useful."),
    (WEAPONS, 'shamshir_e_zomorrodnegar', 'lore',
     "It is the bane of demons still, and out of one that it slays",
     "Whoever bears it in the hand is guarded from sorcery. It is the bane of demons still, and "
     "out of one that it slays"),
    (BOOKS, 'spellbook_omnisight', 'lore',
     "and before it the wands, scrolls and books in sight or in the pack, and the arms, armour, "
     "rings and amulet that are worn, declare their blessing or their curse.",
     "and before it all things on the floor, in the pack and on the body declare their blessing "
     "or their curse."),
    (MONSTERS, 'ochre_jelly', 'lore',
     "Delvers once told how a sword or lightning would divide it in two, but either does it only "
     "half harm, and its bane is fire and frost.",
     "Whoever smites it with a sword or a bolt of lightning only divides it, and has then two "
     "hungry jellies to face."),
    (MONSTERS, 'grick', 'lore',
     "and its hide gives like wet leather, and magic will hurt it worse than any blade.",
     "and its hide gives like wet leather under an ordinary blade and takes little hurt."),
    (MONSTERS, 'blink_dog', 'lore',
     "and are so swift that they seem not to cross the ground between.",
     "and can leap a short way in an instant without crossing the ground between."),
    (MONSTERS, 'xorn', 'lore',
     "and though old tales speak of bargains struck with one for gold, down here it will fight "
     "whoever carries them.",
     "and for gold or gems it will gladly parley, fighting only when it is attacked or when its "
     "prize is denied it."),
    (MONSTERS, 'sphinx', 'lore',
     "and she waits no longer for answers, but hurls her riddle to confound the mind and then "
     "falls upon whoever comes near.",
     "and she will fall upon any who come near without first attempting her puzzle."),
    (MONSTERS, 'sphinx_lesser', 'lore',
     "She will not wait to hear her riddle answered, but uses it to confound the mind, and she "
     "quickly wearies of her prey.",
     "She will ask her riddle only once, and if the answer is wrong, or is slow in coming, she "
     "quickly wearies of the one who gave it."),
    (MONSTERS, 'redcap', 'lore',
     "Down here he has grown bolder, and it is better to bring iron.",
     "Down here he has grown bolder and will stand his ground, but holy power burns him as "
     "sorely as iron does."),
    (MONSTERS, 'shadow_assassin', 'lore',
     "but bright flame leaves him nowhere to stand.",
     "but bright flame and holy light leave him nowhere to stand."),
    (MONSTERS, 'shadow_archer', 'lore',
     "but firelight will give such archers no place in which to hide.",
     "but firelight and holy light will give such archers no place in which to hide."),
    (MONSTERS, 'ushabti_overseer', 'lore',
     "and no more will answer to the spell.",
     "and all the rest will fall quiet."),
    (MONSTERS, 'skeletal_archer', 'lore',
     "so that skeletal archers draw and loose as evenly as engines.",
     "so that the skeleton bowmen draw and loose as evenly as engines."),
    (INGREDIENTS, 'blink_dog_prime', 'description',
     "who are so swift that they seem to hop through the air.",
     "who blink in short hops to come at their prey."),
    (INGREDIENTS, 'sphinx_prime', 'description',
     "whose riddles confound the minds of their prey.",
     "who ask riddles and eat those who answer wrong."),
]

GROUPS = {'jellies': {
    'lore': "An edge divides a jelly of this kind instead of wounding it worse, and only fire "
            "and cold truly harm it.",
    'form': {'slash': 'neutral'},
}}

KINDS = {'grick': {
    'lore': "The grick's rubbery hide gives under blade and point like wet leather, though "
            "magic will search it through.",
    'source': "Dungeons & Dragons, Monster Manual (2014): the grick resists ordinary weapons. Of those, the club is left to the hero (ruling B3).",
    'form': {'slash': 'resist', 'pierce': 'resist'},
}}

CURSED = {
    'redcap': "Border folk drove him off with words of Scripture or the sight of a cross "
              "(the folklore of the Scottish Border).",
    'shadow_assassin': "He bartered away his own shadow for the right to walk in shadows, and "
                       "holy light finds him out.",
    'shadow_archer': "He learned his craft from the darkness and fletches his arrows with it, so "
                     "holy light burns him.",
}


def apply(files: dict) -> list:
    """Edit the loaded files in place; what changed."""
    done = []

    def put(d, key, val, where):
        if d.get(key) != val:
            d[key] = val
            done.append(f'{where}.{key}')

    mons = files[MONSTERS]
    for kind, fields in FIELDS.items():
        for k, v in fields.items():
            put(mons[kind], k, v, kind)
    for kind, t in WEAK.items():
        if t not in mons[kind]['weaknesses']:
            mons[kind]['weaknesses'].append(t)
            done.append(f'{kind}.weaknesses')
    for kind, names in ATTACK_NAMES.items():
        for atk in mons[kind]['attacks']:
            if atk.get('name') in names:
                put(atk, 'name', names[atk['name']], kind)
    for path, kind, field, old, new in WORDS:
        row = files[path][kind]
        text = row[field]
        if new in text:
            continue
        if text.count(old) != 1:
            raise SystemExit(f'{kind}.{field}: neither the old words nor the new')
        put(row, field, text.replace(old, new), kind)
    for (path, iid), fields in ITEM_FIELDS.items():
        for k, v in fields.items():
            put(files[path][iid], k, v, iid)
    for path, iid, key in DROP_FIELDS:
        if key in files[path][iid]:
            del files[path][iid][key]
            done.append(f'{iid}.{key} (dropped)')
    for path, iid in RETIRED:
        if iid in files[path]:
            del files[path][iid]
            done.append(f'{iid} (retired)')
    aff = files[AFFINITY]
    for gid, fields in GROUPS.items():
        for k, v in fields.items():
            put(aff['groups'][gid], k, v, gid)
    for kind, v in KINDS.items():
        put(aff['kinds'], kind, v, 'kinds')
    for kind, why in CURSED.items():
        put(aff['unholy']['cursed'], kind, why, 'cursed')
    return done


def park(text: str) -> tuple:
    """(artifact.json with each parked entry marked `parked`, what changed)."""
    done = []
    for iid in PARKED:
        start = text.index(f'"{iid}": {{')
        at = text.index('"_disabled_reason"', start)
        if '"parked": true' in text[start:at]:
            continue
        line = text.rindex('\n', 0, at) + 1
        nl = '\r\n' if text[line - 2:line] == '\r\n' else '\n'
        text = text[:line] + text[line:at] + '"parked": true,' + nl + text[line:]
        done.append(f'{iid}.parked')
    return text, done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args(argv)
    import jsonfmt
    paths = (MONSTERS, AFFINITY, INGREDIENTS, WEAPONS, ACCESSORIES, FOOD, BOOKS)
    loaded = {p: jsonfmt.load(os.path.join(ROOT, p)) for p in paths}
    files = {p: data for p, (data, _fmt) in loaded.items()}
    done = apply(files)
    with open(os.path.join(ROOT, ARTIFACTS), 'rb') as f:
        artifacts, parked = park(f.read().decode('utf-8'))
    for line in done + parked:
        print('changed', line)
    if not done and not parked:
        print('nothing to change (the pass is up to date)')
    if a.write and done:
        for p, (data, fmt) in loaded.items():
            jsonfmt.save(os.path.join(ROOT, p), data, fmt)
    if a.write and parked:
        with open(os.path.join(ROOT, ARTIFACTS), 'wb') as f:
            f.write(artifacts.encode('utf-8'))
    if a.write and (done or parked):
        print('written')
    return 0


if __name__ == '__main__':
    sys.exit(main())
