"""
Apply the revised weapon chain multiplier + special effects proposal to weapon.json.

Rules:
- Class-level curves applied by (class, variant, tier)
- Legendary weapons (identified by having custom/unique chains or specific IDs) are SKIPPED
- Special effects (stunChance, bleedChance, knockback, ignoreShield, critMultiplier) applied per class
- Fist, spear, longbow classes are SKIPPED entirely (legendary-only)
"""
import json
import os
import sys

WEAPON_PATH = os.path.join(os.path.dirname(__file__), 'items', 'weapon.json')

# ── Chain multiplier definitions: (class, variant, tier) -> multipliers ──

CHAINS = {
    # DAGGER
    ('dagger', None, 1): [0.25, 0.40, 0.60, 1.00, 1.80, 3.00, 4.50],
    ('dagger', None, 2): [0.25, 0.40, 0.65, 1.10, 2.00, 3.20, 5.00],
    ('dagger', None, 3): [0.30, 0.50, 0.80, 1.30, 2.20, 3.50, 5.00, 6.50],
    ('dagger', None, 4): [0.30, 0.50, 0.80, 1.30, 2.40, 3.80, 5.50, 7.50],
    ('dagger', None, 5): [0.35, 0.55, 0.85, 1.40, 2.60, 4.00, 6.00, 8.00],

    # RAPIER
    ('rapier', None, 1): [0.40, 0.80, 1.30, 2.00, 2.80, 3.80],
    ('rapier', None, 2): [0.40, 0.80, 1.30, 2.00, 2.80, 3.80, 5.00],
    ('rapier', None, 3): [0.40, 0.85, 1.40, 2.10, 3.00, 4.00, 5.50],
    ('rapier', None, 4): [0.45, 0.90, 1.50, 2.20, 3.20, 4.30, 6.00],
    ('rapier', None, 5): [0.50, 1.00, 1.60, 2.40, 3.50, 4.80, 6.50],

    # SCIMITAR
    ('scimitar', None, 1): [0.50, 1.00, 1.40, 1.80, 2.80, 3.80],
    ('scimitar', None, 2): [0.50, 1.00, 1.40, 1.80, 2.80, 3.80, 5.00],
    ('scimitar', None, 3): [0.50, 1.00, 1.50, 1.90, 3.00, 4.20, 5.50],
    ('scimitar', None, 4): [0.55, 1.10, 1.50, 2.00, 3.20, 4.50, 6.00],
    ('scimitar', None, 5): [0.60, 1.20, 1.60, 2.10, 3.50, 5.00, 6.50],

    # SWORD 1H
    ('sword', '1h', 1): [0.60, 1.00, 1.50, 2.00, 2.60, 3.20],
    ('sword', '1h', 2): [0.60, 1.00, 1.50, 2.10, 2.70, 3.40, 4.20],
    ('sword', '1h', 3): [0.60, 1.10, 1.60, 2.20, 2.90, 3.70, 4.50],
    ('sword', '1h', 4): [0.70, 1.10, 1.70, 2.30, 3.00, 3.80, 4.80],
    ('sword', '1h', 5): [0.70, 1.20, 1.80, 2.50, 3.20, 4.00, 5.00],

    # SWORD 2H
    ('sword', '2h', 1): [0.70, 1.20, 1.80, 2.50, 3.20, 4.00],
    ('sword', '2h', 2): [0.70, 1.20, 1.80, 2.50, 3.30, 4.20, 5.00],
    ('sword', '2h', 3): [0.70, 1.20, 1.90, 2.60, 3.50, 4.50, 5.50],
    ('sword', '2h', 4): [0.80, 1.30, 2.00, 2.80, 3.60, 4.60, 5.80],
    ('sword', '2h', 5): [0.80, 1.40, 2.10, 2.90, 3.80, 4.80, 6.00],

    # AXE 1H
    ('axe', '1h', 1): [1.00, 1.50, 2.00, 2.40, 2.80],
    ('axe', '1h', 2): [1.00, 1.50, 2.00, 2.50, 2.90, 3.30],
    ('axe', '1h', 3): [1.00, 1.60, 2.10, 2.60, 3.10, 3.60],
    ('axe', '1h', 4): [1.00, 1.60, 2.20, 2.70, 3.20, 3.80],
    ('axe', '1h', 5): [1.10, 1.70, 2.30, 2.90, 3.50, 4.20],

    # AXE 2H
    ('axe', '2h', 1): [1.20, 1.80, 2.40, 3.00, 3.50],
    ('axe', '2h', 2): [1.20, 1.80, 2.50, 3.10, 3.60, 4.20],
    ('axe', '2h', 3): [1.20, 1.90, 2.60, 3.20, 3.80, 4.50],
    ('axe', '2h', 4): [1.30, 2.00, 2.70, 3.40, 4.00, 4.80],
    ('axe', '2h', 5): [1.30, 2.00, 2.80, 3.50, 4.20, 5.00],

    # CLUB
    ('club', None, 1): [1.00, 1.50, 2.00, 2.50],
    ('club', None, 2): [1.00, 1.50, 2.00, 2.50, 3.00],
    ('club', None, 3): [1.00, 1.60, 2.10, 2.60, 3.20],
    ('club', None, 4): [1.10, 1.70, 2.20, 2.80, 3.50],
    ('club', None, 5): [1.10, 1.70, 2.30, 3.00, 3.80],

    # MACE
    ('mace', None, 1): [0.70, 1.20, 2.00, 2.60, 3.00],
    ('mace', None, 2): [0.70, 1.20, 2.00, 2.70, 3.20, 3.60],
    ('mace', None, 3): [0.70, 1.30, 2.10, 2.80, 3.40, 4.00],
    ('mace', None, 4): [0.80, 1.40, 2.20, 3.00, 3.60, 4.30],
    ('mace', None, 5): [0.80, 1.50, 2.40, 3.20, 3.80, 4.50],

    # MORNINGSTAR
    ('morningstar', None, 1): [0.85, 1.30, 1.80, 2.30, 2.70],
    ('morningstar', None, 2): [0.85, 1.30, 1.80, 2.30, 2.70, 3.20],
    ('morningstar', None, 3): [0.85, 1.40, 1.90, 2.45, 2.95, 3.50],
    ('morningstar', None, 4): [0.90, 1.45, 2.00, 2.55, 3.10, 3.70],
    ('morningstar', None, 5): [0.95, 1.50, 2.10, 2.65, 3.25, 3.90],

    # FLAIL
    ('flail', None, 1): [0.50, 1.00, 1.60, 2.40, 3.20],
    ('flail', None, 2): [0.50, 1.00, 1.60, 2.40, 3.20, 4.20],
    ('flail', None, 3): [0.50, 1.10, 1.70, 2.50, 3.40, 4.50],
    ('flail', None, 4): [0.60, 1.10, 1.80, 2.60, 3.60, 4.80],
    ('flail', None, 5): [0.60, 1.20, 1.90, 2.80, 3.80, 5.00],

    # WARHAMMER
    ('warhammer', None, 1): [1.30, 2.00, 2.50, 3.00],
    ('warhammer', None, 2): [1.30, 2.00, 2.60, 3.10, 3.50],
    ('warhammer', None, 3): [1.40, 2.10, 2.70, 3.30, 3.80],
    ('warhammer', None, 4): [1.40, 2.20, 2.90, 3.50, 4.10],
    ('warhammer', None, 5): [1.50, 2.30, 3.00, 3.70, 4.50],

    # ZWEIHANDER
    ('zweihander', None, 1): [0.80, 1.40, 2.20, 3.00, 3.80],
    ('zweihander', None, 2): [0.80, 1.40, 2.20, 3.00, 3.80, 4.50],
    ('zweihander', None, 3): [0.80, 1.50, 2.30, 3.20, 4.00, 4.80],
    ('zweihander', None, 4): [0.90, 1.60, 2.40, 3.30, 4.20, 5.20],
    ('zweihander', None, 5): [0.90, 1.60, 2.50, 3.50, 4.50, 5.50],

    # POLEARM
    ('polearm', None, 1): [0.60, 1.20, 2.00, 2.60, 3.20],
    ('polearm', None, 2): [0.60, 1.20, 2.00, 2.70, 3.30, 3.90],
    ('polearm', None, 3): [0.70, 1.30, 2.10, 2.80, 3.50, 4.20],
    ('polearm', None, 4): [0.70, 1.40, 2.20, 3.00, 3.70, 4.50],
    ('polearm', None, 5): [0.80, 1.50, 2.30, 3.10, 3.90, 4.80],

    # STAFF
    ('staff', None, 1): [0.50, 1.00, 1.60, 2.20, 2.80],
    ('staff', None, 2): [0.50, 1.00, 1.70, 2.40, 3.00],
    ('staff', None, 3): [0.50, 1.10, 1.80, 2.50, 3.20, 3.80],
    ('staff', None, 4): [0.60, 1.20, 1.90, 2.60, 3.40, 4.20],
    ('staff', None, 5): [0.60, 1.20, 2.00, 2.80, 3.60, 4.50],

    # RANGED - need subtype detection (shortbow/longbow/crossbow)
    # Will handle via name matching below
}

# Ranged subtypes keyed by subtype name fragment
RANGED_CHAINS = {
    'shortbow': {
        1: [0.50, 1.20, 2.00, 3.00],
        2: [0.50, 1.20, 2.00, 3.00, 4.00],
        3: [0.60, 1.30, 2.20, 3.20, 4.30],
        4: [0.60, 1.40, 2.30, 3.40, 4.60],
        5: [0.70, 1.50, 2.50, 3.60, 5.00],
    },
    'longbow': {
        1: [0.60, 1.30, 2.20, 3.20],
        2: [0.60, 1.30, 2.20, 3.20, 4.30],
        3: [0.70, 1.40, 2.30, 3.40, 4.60],
        4: [0.70, 1.50, 2.50, 3.60, 5.00],
        5: [0.80, 1.60, 2.70, 3.80, 5.30],
    },
    'crossbow': {
        1: [0.80, 1.50, 2.30, 3.20],
        2: [0.80, 1.50, 2.30, 3.20, 4.20],
        3: [0.80, 1.60, 2.50, 3.40, 4.50],
        4: [0.90, 1.70, 2.60, 3.60, 4.80],
        5: [0.90, 1.80, 2.80, 3.80, 5.00],
    },
}

# ── Special effects per class and tier ──

# stunChance by (class, tier)
STUN_CHANCE = {
    ('mace', 1): 0.15, ('mace', 2): 0.20, ('mace', 3): 0.22,
    ('mace', 4): 0.26, ('mace', 5): 0.30,
    ('warhammer', 1): 0.28, ('warhammer', 2): 0.30, ('warhammer', 3): 0.32,
    ('warhammer', 4): 0.35, ('warhammer', 5): 0.38,
    ('staff', 1): 0.12, ('staff', 2): 0.15, ('staff', 3): 0.18,
    ('staff', 4): 0.20, ('staff', 5): 0.22,
}

# bleedChance by (class, tier)
BLEED_CHANCE = {
    ('morningstar', 1): 0.15, ('morningstar', 2): 0.18, ('morningstar', 3): 0.20,
    ('morningstar', 4): 0.22, ('morningstar', 5): 0.25,
}

# knockback by (class, tier) — True if weapon should have it
KNOCKBACK = {
    ('club', 1): True, ('club', 2): True, ('club', 3): True,
    ('club', 4): True, ('club', 5): True,
    ('warhammer', 1): False, ('warhammer', 2): False, ('warhammer', 3): True,
    ('warhammer', 4): True, ('warhammer', 5): True,
}

# ignoreShield by class
IGNORE_SHIELD = {'flail'}

# critMultiplier by (class, tier)
CRIT_MULT = {
    ('rapier', 1): 1.0, ('rapier', 2): 1.1, ('rapier', 3): 1.2,
    ('rapier', 4): 1.3, ('rapier', 5): 1.5,
    ('scimitar', 1): 1.0, ('scimitar', 2): 1.1, ('scimitar', 3): 1.2,
    ('scimitar', 4): 1.3, ('scimitar', 5): 1.4,
}

# Classes to skip entirely (legendary-only, keep existing custom arrays)
SKIP_CLASSES = {'spear', 'longbow', 'fist'}

# Legendary weapon IDs to skip (they have custom curves)
LEGENDARY_IDS = set()  # Will be populated from weapons with custom non-standard properties


def detect_ranged_subtype(weapon_id, weapon):
    """Determine if a ranged weapon is shortbow, longbow, or crossbow."""
    name = weapon.get('name', '').lower()
    wid = weapon_id.lower()
    if 'crossbow' in name or 'crossbow' in wid:
        return 'crossbow'
    if 'longbow' in name or 'longbow' in wid or 'long bow' in name:
        return 'longbow'
    if 'shortbow' in name or 'shortbow' in wid or 'short bow' in name:
        return 'shortbow'
    # Default: check reach — crossbows tend to have shorter reach
    reach = weapon.get('reach', 15)
    if reach <= 12:
        return 'crossbow'
    return 'shortbow'  # default fallback


def is_legendary(weapon_id, weapon):
    """Detect NAMED legendary weapons that should keep their custom arrays.
    Material-tier weapons (adamantine, dragonbone) are NOT legendaries for
    this purpose — they should get standard class curves."""
    name = weapon.get('name', '').lower()
    wid = weapon_id.lower()

    # Material-prefix weapons are standard tier weapons, not unique legendaries
    material_prefixes = ['iron', 'steel', 'mithril', 'adamantine', 'dragonbone',
                         'wood', 'hardwood', 'ironwood', 'diamond', 'oak',
                         'ash', 'yew', 'elm', 'bronze', 'copper', 'silver',
                         'gold', 'platinum', 'bone', 'obsidian', 'crystal']
    for prefix in material_prefixes:
        if wid.startswith(prefix + '_') or name.startswith(prefix + ' '):
            return False

    # Named unique legendaries — these keep their custom arrays
    legendary_ids = {
        'excalibur', 'durendal', 'gram', 'tyrfing', 'fragarach',
        'caladbolg', 'joyeuse', 'hrunting', 'skofnung', 'kusanagi',
        'zulfiqar', 'harpe', 'carnwennan', 'mistilteinn', 'curtana',
        'parashu', 'labrys', 'gungnir', 'gae_bulg', 'spear_of_longinus',
        'trident_of_poseidon', 'amenonuhoko', 'mjolnir', 'sharur',
        'ruyi_jingu_bang', 'gandiva', 'fail_not', 'chandrahas',
        'laevateinn', 'thyrsus', 'rod_of_moses', 'sudarshana',
        'ridill', 'kladenets', 'shamshir_e_zomorrodnegar', 'chrysaor',
        'caliburn', 'brisingr', 'fragarach_the_whisperer', 'naegling',
        'punch_in_the_face',
        # Non-material unique weapons
        'soul_reaver', 'dawnbreaker', 'venomfang',
        'hunt_captains_sword', 'wendigo_fang',
    }
    if wid in legendary_ids:
        return True

    return False


def get_variant(weapon):
    """Get the variant (1h/2h) for a weapon, defaulting based on twoHanded."""
    v = weapon.get('variant')
    if v:
        return v
    return '2h' if weapon.get('twoHanded', False) else '1h'


def apply_changes():
    with open(WEAPON_PATH, 'r', encoding='utf-8') as f:
        weapons = json.load(f)

    changes = 0
    skipped = 0
    errors = []

    for wid, w in weapons.items():
        wclass = w.get('class', '')
        tier = w.get('tier', 1)

        # Skip legendary-only classes
        if wclass in SKIP_CLASSES:
            skipped += 1
            continue

        # Skip legendary weapons
        if is_legendary(wid, w):
            skipped += 1
            continue

        variant = get_variant(w)

        # ── Get chain multipliers ──
        new_chain = None

        if wclass == 'ranged':
            subtype = detect_ranged_subtype(wid, w)
            if subtype in RANGED_CHAINS and tier in RANGED_CHAINS[subtype]:
                new_chain = RANGED_CHAINS[subtype][tier]
            else:
                errors.append(f"  WARN: No ranged chain for {wid} subtype={subtype} tier={tier}")
        else:
            # For classes that don't distinguish variant (most), try with None first
            key = (wclass, None, tier)
            if key in CHAINS:
                new_chain = CHAINS[key]
            else:
                # Try with variant (sword, axe)
                key = (wclass, variant, tier)
                if key in CHAINS:
                    new_chain = CHAINS[key]
                else:
                    errors.append(f"  WARN: No chain for {wid} class={wclass} variant={variant} tier={tier}")

        if new_chain:
            w['chainMultipliers'] = new_chain
            w['maxChainLength'] = len(new_chain)
            changes += 1

        # ── Apply special effects ──

        # Stun chance
        stun_key = (wclass, tier)
        if stun_key in STUN_CHANCE:
            w['stunChance'] = STUN_CHANCE[stun_key]

        # Bleed chance
        if stun_key in BLEED_CHANCE:
            w['bleedChance'] = BLEED_CHANCE[stun_key]

        # Knockback
        if stun_key in KNOCKBACK:
            w['knockback'] = KNOCKBACK[stun_key]

        # Ignore shield
        if wclass in IGNORE_SHIELD:
            w['ignoreShield'] = True

        # Crit multiplier
        if stun_key in CRIT_MULT:
            w['critMultiplier'] = CRIT_MULT[stun_key]

    # Write back
    with open(WEAPON_PATH, 'w', encoding='utf-8') as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)

    print(f"Updated {changes} weapons, skipped {skipped} (legendary/special)")
    if errors:
        print("Warnings:")
        for e in errors:
            print(e)

    # Print summary by class
    class_counts = {}
    for wid, w in weapons.items():
        c = w.get('class', 'unknown')
        class_counts[c] = class_counts.get(c, 0) + 1
    print("\nWeapons by class:")
    for c, n in sorted(class_counts.items()):
        print(f"  {c}: {n}")


if __name__ == '__main__':
    apply_changes()
