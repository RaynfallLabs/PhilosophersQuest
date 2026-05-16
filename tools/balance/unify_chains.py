"""Unify all 22 weapon templates to 5-rung class-shape chains.
Rename '_on_chain3' mechanic tags to '_at_max'. Per developer call:
all specials fire at max chain only — chain length is uniform across
the bank, class shape is the only variable in the chain mult curve.
"""
import json
from glob import glob

CLASS_SHAPES = {
    'finesse': [0.20, 0.55, 1.00, 1.80, 3.00],
    'normal':  [0.50, 0.85, 1.00, 1.45, 2.00],
    'heavy':   [0.75, 0.90, 1.00, 1.30, 1.75],
}

# Translate any chain-3 mechanics to chain-max equivalents.
MECHANIC_RENAMES = {
    'bleed_on_chain3':       'bleed_at_max',
    'stun_on_chain3':        'stun_at_max',
    'stun_plus_anti_heavy':  'stun_at_max',     # anti-heavy is the passive flavor
    'cleave_on_kill':        'cleave_at_max',   # now requires max-chain kill
    'cleave_plus_bleed':     'cleave_at_max_plus_bleed',
}

renamed = 0
shape_changed = 0
for fn in sorted(glob('data/templates/weapons/*.json')):
    with open(fn, encoding='utf-8') as f:
        t = json.load(f)
    klass = t.get('weapon_class_chain', 'normal')
    target = CLASS_SHAPES.get(klass)
    if target is None:
        continue
    if t.get('chain_multipliers') != target:
        t['chain_multipliers'] = target
        t['max_chain_length'] = 5
        shape_changed += 1
    mech = t.get('class_mechanic')
    if mech in MECHANIC_RENAMES:
        t['class_mechanic'] = MECHANIC_RENAMES[mech]
        renamed += 1
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump(t, f, indent=2, ensure_ascii=False)

print(f"Templates: {shape_changed} chain shapes updated, {renamed} mechanic tags renamed")

# Same update on named uniques in data/items/weapon.json
with open('data/items/weapon.json', encoding='utf-8') as f:
    weapons = json.load(f)
unique_shape_changed = 0
for wid, w in weapons.items():
    klass = w.get('weapon_class_chain')
    if klass and klass in CLASS_SHAPES:
        target = CLASS_SHAPES[klass]
        if w.get('chain_multipliers') != target:
            w['chain_multipliers'] = target
            w['max_chain_length'] = 5
            unique_shape_changed += 1
with open('data/items/weapon.json', 'w', encoding='utf-8') as f:
    json.dump(weapons, f, indent=2, ensure_ascii=False)
print(f"Uniques: {unique_shape_changed} chain shapes updated in weapon.json")
