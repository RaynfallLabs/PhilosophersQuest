"""Merge the 15 new uniques from tools/balance/generated/uniques/weapons_new/
into data/items/weapon.json. Translates the agent's snake_case schema to the
loader's hybrid camelCase/snake_case format and flattens special_properties.
"""
import json
import os
from glob import glob

CLASS_COLOR_DEFAULTS = {
    'sword':      [210, 220, 235],
    'shortsword': [210, 220, 235],
    'longsword':  [200, 215, 240],
    'greatsword': [200, 215, 245],
    'bastard_sword': [200, 215, 240],
    'axe':        [180, 160, 110],
    'mace':       [170, 160, 150],
    'hammer':     [170, 160, 150],
    'spear':      [200, 200, 180],
    'glaive':     [200, 200, 180],
    'club':       [150, 105,  70],
    'bow':        [180, 140, 100],
    'longbow':    [180, 140, 100],
    'shortbow':   [180, 140, 100],
    'dagger':     [200, 220, 200],
    'staff':      [170, 130,  90],
    'flail':      [160, 160, 160],
    'sling':      [120, 120, 100],
    'sickle':     [180, 200, 130],
    'lance':      [200, 200, 180],
    'javelin':    [200, 200, 180],
}


def translate(new_def: dict) -> tuple[str, dict]:
    """Return (id, weapon_json_entry) shaped for data/items/weapon.json."""
    wid = new_def['id']
    out = {}
    # Identity
    out['name'] = new_def['name']
    out['is_unique'] = True
    # Class / variant
    wc = new_def.get('weapon_class', 'sword')
    out['class'] = wc
    out['weapon_class'] = wc
    out['variant'] = '2h' if new_def.get('hands', 1) == 2 else '1h'
    out['twoHanded'] = bool(new_def.get('hands', 1) == 2)
    out['two_handed'] = out['twoHanded']
    out['template_basis'] = new_def.get('template_basis', wc)
    # Damage
    out['baseDamage'] = int(new_def['base_damage'])
    out['base_damage'] = out['baseDamage']
    out['chainMultipliers'] = new_def['chain_multipliers']
    out['chain_multipliers'] = new_def['chain_multipliers']
    out['maxChainLength'] = new_def['max_chain_length']
    out['max_chain_length'] = new_def['max_chain_length']
    out['weapon_class_chain'] = new_def.get('weapon_class_chain', 'normal')
    out['damageTypes'] = new_def['damage_types']
    out['damage_types'] = new_def['damage_types']
    # Spawn / progression
    out['min_level'] = int(new_def['min_level'])
    out['peak_floor'] = int(new_def['peak_floor'])
    out['spread'] = int(new_def['spread'])
    out['peak_weight'] = float(new_def['peak_weight'])
    out['max_enchant'] = int(new_def.get('max_enchant', 2))
    # Quiz tier derived from peak_floor (matches material formula in CURVE.md)
    out['mathTier'] = max(1, out['peak_floor'] // 20 + 1)
    out['quiz_tier'] = out['mathTier']
    # Cosmetics + economy
    out['symbol'] = ')'
    out['color'] = CLASS_COLOR_DEFAULTS.get(wc, [200, 200, 200])
    out['weight'] = float(new_def.get('weight_lb', 4.0))
    out['tier'] = max(1, out['mathTier'])  # legacy field
    out['material'] = 'legendary'  # placeholder; uniques don't roll material
    out['containerLootTier'] = 'rare'
    out['container_loot_tier'] = 'rare'
    out['value'] = max(200, out['base_damage'] * 60)
    out['unidentified_name'] = f"a {wc}"
    out['identified'] = False
    # Flatten special_properties onto top level so Weapon() can read them
    sp = new_def.get('special_properties', {}) or {}
    for k, v in sp.items():
        out[k] = v
    # Lore + provenance
    out['lore'] = new_def.get('lore', '')
    if 'curve_note' in new_def:
        out['_curve_note'] = new_def['curve_note']
    # Default zero on-hit fields (so loader treats them as 0.0)
    for f, default in (
        ('stunChance', 0.0), ('bleedChance', 0.0), ('reach', 1),
        ('knockback', False), ('ignoreShield', False), ('critMultiplier', 1.0),
        ('requiresAmmo', None),
    ):
        if f not in out:
            # If special_properties already provided snake_case, sync camelCase
            snake = {'stunChance': 'stun_chance', 'bleedChance': 'bleed_chance',
                     'knockback': 'knockback', 'ignoreShield': 'ignore_shield',
                     'critMultiplier': 'crit_multiplier', 'requiresAmmo': 'requires_ammo',
                     'reach': 'reach'}[f]
            if snake in out:
                out[f] = out[snake]
            else:
                out[f] = default
    return wid, out


def main():
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    new_dir = os.path.join(repo, 'tools', 'balance', 'generated', 'uniques', 'weapons_new')
    weapons_path = os.path.join(repo, 'data', 'items', 'weapon.json')

    with open(weapons_path, encoding='utf-8') as f:
        weapons = json.load(f)

    new_files = sorted(glob(os.path.join(new_dir, '*.json')))
    added = []
    conflicts = []
    for fn in new_files:
        with open(fn, encoding='utf-8') as f:
            new_def = json.load(f)
        wid, entry = translate(new_def)
        if wid in weapons:
            conflicts.append(wid)
            continue
        weapons[wid] = entry
        added.append((wid, entry['name'], entry['peak_floor']))

    if conflicts:
        print(f"WARNING: Skipped existing IDs: {conflicts}")

    with open(weapons_path, 'w', encoding='utf-8') as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)

    print(f"Added {len(added)} new uniques:")
    for wid, name, peak in sorted(added, key=lambda x: x[2]):
        print(f"  peak F{peak:>3}  {name:<30s}  ({wid})")
    print(f"\nweapon.json now has {len(weapons)} entries, "
          f"{sum(1 for v in weapons.values() if v.get('is_unique'))} unique.")


if __name__ == '__main__':
    main()
