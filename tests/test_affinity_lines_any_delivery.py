"""Every line said when a hit meets a weakness, resistance or shrug-off is
true however the hit arrived (Brandon, 3.5.1: "I killed a Huginn Raven, hit
it with my iron shortsword and got 'An arrow brings a bird down...'").

A damage kind is not a delivery: piercing comes from a sword's thrust, a
spear, an arrow, a thrown dagger; crushing from a mace, a staff, a sling
stone; fire from a spell, oil, a flask, a weapon of fire. So no hit line
(data/affinity_lines.json: the generic, felt and family/group habit lines)
may name a particular weapon or way of delivering it. A line that tells a
myth (Thor's hammer, Perseus' sword, Bellerophon's spear) is history, not a
claim about this hit, and is allowed by name below.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Words that name how a blow arrived. "blow" is a melee word: a spell or an
# arrow is not a blow (the generic lines say "hit").
DELIVERY = re.compile(r"\b(arrows?|bows?|blades?|swords?|maces?|hammers?|clubs?|axes?|spears?|"
                      r"stabs?|stabbed|swing|thrusts?|blows?|spells?|thrown|flasks?|slings?)\b",
                      re.I)

# Myth: the line names the hero's own weapon in the story.
MYTH = ("Thor's hammer", "Perseus", "Bellerophon", "Sigurd", "maces were made for")


def _lines():
    with open(os.path.join(ROOT, 'data', 'affinity_lines.json'), encoding='utf-8') as f:
        d = json.load(f)
    out = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if not k.startswith('_'):
                    walk(v, path + [k])
        elif isinstance(o, list):
            for x in o:
                walk(x, path)
        elif isinstance(o, str):
            out.append(('/'.join(path), o))
    for key in ('weak', 'resisted', 'shrugs_off', 'weak_many', 'resisted_many',
                'shrugs_off_many', 'felt', 'habits'):
        walk(d.get(key), [key])
    return out


def test_no_hit_line_names_how_the_hit_arrived():
    bad = [(p, t) for p, t in _lines()
           if DELIVERY.search(t) and not any(m in t for m in MYTH)]
    assert not bad, bad


def test_the_birds_line_fits_a_sword_thrust():
    lines = dict(_lines())
    bird = [t for p, t in _lines() if p.endswith('birds/weak:pierce')]
    assert bird and 'arrow' not in bird[0].lower() and 'point' in bird[0].lower(), lines
