"""The Tactical Mind's player text (AI-2, MONSTERS AND MAGIC, 2026-11-20).

Adds, idempotently, keeping each file's layout (indent 2, LF):
  * data/tells.json: the tells of a thinking creature (its mind, the dark
    edge, its snares, a band leader's orders), last in `order` so a
    creature's worst power is still the tell said at first sight;
  * data/ui/monster_ways.json: the help page's "How the clever ones fight".
The minds themselves, their lines and Bestiary sentences are data/minds.json.

Run: py tools/content/add_tactical_mind_2026_11.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TELLS = {
    'mind_cunning': {
        'sign': "{The} watches you, and keeps glancing at {his} friends.",
        'does': "{He} waits for {his} friends, will not follow you into a corridor, "
                "and goes for whoever is bleeding, your pet too.",
        'counter': "Kill {him} before the rest come up, call a badly hurt pet back to "
                   "its Soul Sphere, and do not wait in a corridor for {him} to come to you.",
    },
    'mind_soldier': {
        'sign': "{The} keeps {his} place in the line like a drilled soldier.",
        'does': "{He} holds a line with {his} fellows, changes places when the front man "
                "tires, and may feign flight to draw you out of a narrow way.",
        'counter': "Finish a hurt one before {he} can step back, and do not follow a foe who "
                   "runs too neatly. Study the kind and you will see through the feint.",
    },
    'mind_trickster': {
        'sign': "{The} never comes straight at you.",
        'does': "{He} slips round to your side and will not be drawn into a narrow way.",
        'counter': "Fight with a wall at your back, or draw {him} out with a ranged attack.",
    },
    'mind_caster': {
        'sign': "{The} hangs back behind the others, muttering.",
        'does': "{He} keeps {his} distance and casts at you over {his} friends.",
        'counter': "Silence {him}, or reach {him} past the others with a ranged attack or a spell.",
    },
    'dark_edge': {
        'sign': "{The} keeps to the shadows at the very edge of your light.",
        'does': "{He} steps out of your light and strikes first when you come close; "
                "an archer of {his} kind shoots from the dark, where you cannot see to shoot back.",
        'counter': "Carry a brighter light or cast Light: the farther you see, the less dark "
                   "there is for {him} to hide in.",
    },
    'knows_traps': {
        'sign': "{The} picks {his} way across the floor as if {he} knew every stone.",
        'does': "{He} never steps on the snares and hazards of {his} own ground, and waits "
                "where your straight way to {him} runs over one.",
        'counter': "Look before you charge, find the traps first, or come at {him} another way.",
    },
    'band_orders': {
        'sign': "{The} shouts orders, and the others obey.",
        'does': "While {he} lives and can shout, {his} band keeps a guard in front of {him}, "
                "charges when you are hurt, and falls back round {him} when half of them are down.",
        'counter': "Kill or silence the leader first. Wax in your ears keeps out the words, "
                   "not the orders.",
    },
}

SECTION = {
    'heading': 'How the clever ones fight',
    'rows': [
        ['Thinking foes',
         "Goblins, bandits, orcs, hobgoblins, the dark elves and the Fair Folk think about "
         "their turn. Beasts, vermin and the mindless dead do not. Observe one, or read its "
         "kind in the Bestiary, to learn how it thinks."],
        ['Corridors',
         "A clever band will not follow you into a narrow way one at a time. They wait out of "
         "sight, come round another way, or shoot down it. They come in the end, but do not "
         "count on the corridor alone."],
        ['Captains',
         "While a band's leader lives and can shout, his guards stand in front of him and the "
         "rest charge when you are hurt. Kill or silence him and the orders stop."],
        ['Feints',
         "Drilled soldiers may break and run to draw you out of a corridor, with the rest "
         "waiting beside the way out. A foe who runs too neatly is a trap."],
        ['The weak one',
         "A cunning foe goes for whoever is bleeding. Call a badly hurt pet back to its Soul "
         "Sphere."],
        ['The dark edge',
         "Dark elves and shadows keep to the edge of your light and strike from the dark. A "
         "brighter light leaves them nowhere to hide."],
        ['Archers',
         "An archer steps aside for a clear shot past its friends and keeps its distance. Each "
         "missile reaches as far as its weapon: a sling less than a longbow."],
        ['Your tricks',
         "What a clever side sees you do on a floor, it learns: fight from corridors twice and "
         "they stay in their room. Change your ways, or leave no one to tell."],
    ],
}


def _read(path) -> str:
    with open(path, encoding='utf-8') as f:
        return f.read()


def _write(path, text: str) -> None:
    json.loads(text)                     # never write a file that does not parse
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def _dq(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def add_tells() -> int:
    """The keys at the end of `order`, the effects at the end of `effects`
    (both laid out as the file is: the order on wrapped lines, each effect a
    block of three lines)."""
    p = os.path.join(ROOT, 'data', 'tells.json')
    text = _read(p)
    have = json.loads(text)
    changed = 0
    missing = [k for k in TELLS if k not in have['order']]
    if missing:
        end = text.index('],', text.index('"order":'))
        line = ',\n            ' + ', '.join(_dq(k) for k in missing)
        text = text[:end] + line + text[end:]
        changed += len(missing)
    new = [k for k in TELLS if k not in have['effects']]
    if new:
        cut = text.rstrip().rfind('\n  }')
        blocks = []
        for k in new:
            e = TELLS[k]
            blocks.append(f'    {_dq(k)}: {{\n'
                          f'      "sign": {_dq(e["sign"])},\n'
                          f'      "does": {_dq(e["does"])},\n'
                          f'      "counter": {_dq(e["counter"])}\n'
                          f'    }}')
        text = text[:cut] + ',\n' + ',\n'.join(blocks) + text[cut:]
        changed += len(new)
    if changed:
        _write(p, text)
    return changed


def add_help() -> int:
    """The help page's section, last, laid out as the others are."""
    p = os.path.join(ROOT, 'data', 'ui', 'monster_ways.json')
    text = _read(p)
    if any(s.get('heading') == SECTION['heading'] for s in json.loads(text)['sections']):
        return 0
    rows = ',\n'.join(f'        [{_dq(a)}, {_dq(b)}]' for a, b in SECTION['rows'])
    block = (',\n    {\n'
             f'      "heading": {_dq(SECTION["heading"])},\n'
             '      "rows": [\n' + rows + '\n      ]\n    }')
    cut = text.rstrip().rfind('\n  ]')
    text = text[:cut] + block + text[cut:]
    _write(p, text)
    return 1


def main() -> int:
    n = add_tells() + add_help()
    print(f'{n} change(s)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
