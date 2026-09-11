#!/usr/bin/env python3
"""Rebase 96 uniques in data/items/weapon.json for chain combat v2 (v2.14.0).

For each unique:
  1. Set `chain_exponent: 1.15` so it uses the polynomial ladder.
  2. Rebase `base_damage` per formula OR the iconic-exception table.
  3. Strip redundant `class_mechanic` values now handled by the class chain-
     special ladder.

Preserves lore, floor_spawn_weight, effects, per-tag bonus damage arrays,
unique-only mechanics, and quest interactions.

Run once (`python tools/balance/rebase_uniques_v2_14.py`), review the diff,
commit as part of v2.14.0.

See docs/design/uniques_v2_14.md for the full framework.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
WEAPON_JSON = ROOT / 'data' / 'items' / 'weapon.json'

# Formula: target_base = round(COMMON_CLASS_BASE[class] × TIER_MAT_MULT[tier] × 1.5)
COMMON_CLASS_BASE = {
    'fist': 2,
    'dagger': 3,
    'rapier': 4,
    'sword': 5,          # 1h sword base; 2h swords bump via two_handed check
    'axe': 6,            # 1h axe base
    'mace': 6,
    'club': 6,           # club folds into mace family for the formula
    'spear': 5,
    'staff': 8,
    'glaive': 8,
    'halberd': 7,
    'zweihander': 8,     # 2h sword variant
    'warhammer': 11,     # canonical 2h warhammer
    'morningstar': 6,    # 1h class; T5 uniques bump to warhammer via iconic table
    'bow': 4,
    'crossbow': 8,
    'sling': 2,
    'ranged': 6,         # catch-all
    'net': 3,            # utility, not a chain weapon
}

# For 2H swords: class 'sword' with two_handed=true → bump to 2H base
TWO_HANDED_BASE_BUMP = {
    'sword': 8,          # 2h sword
    'axe': 10,           # 2h axe
    'scimitar': 8,       # large scimitar (rare 2h variant)
}

# scimitar folds under 'sword' for the class-chain-specials dispatch (per
# _weapon_key in combat.py) — same formula base as 1h sword.
SCIMITAR_BASE = 5

TIER_MAT_MULT = {
    1: 1.00,
    2: 1.10,
    3: 1.25,
    4: 1.40,
    5: 1.60,
}

# Iconic exceptions — see docs/design/uniques_v2_14.md.
# ID → target base_damage.
ICONIC_BASE = {
    'sword_of_michael':      18,
    'mjolnir':               32,
    'dawnbreaker':           30,
    'stormbringer':          24,
    'tyrfing':               26,
    'excalibur':             16,
    'anduril':               16,
    'gungnir':               15,
    'gram':                  18,   # reforged
    'mistilteinn':           18,
    'ruyi_jingu_bang':       24,
    'laevateinn':            26,
    'aiglos':                16,
    'trident_of_poseidon':   18,
    'gandiva':               12,
    'fail_not':              10,
    'kusanagi':              16,
    'chandrahasa':           18,
    'chandrahas':            14,   # separate T4 scimitar
    'punch_in_the_face':     35,   # Dad-tier Easter egg, formula-exempt
    'wendigo_fang':          12,
    'soul_reaver':           14,
    'sudarshana':            14,
    'venomfang':             26,   # T5 morningstar keeps a bump
    'broken_gram':           4,    # T1 quest starter, keep low (formula-appropriate)
    'stormbringer_shard':    12,   # if the seed variant exists
}

# class_mechanic values that are now covered by the v2.14.0 class chain-special
# ladder. Strip these from uniques where they would double-fire.
REDUNDANT_CLASS_MECHS = {
    'bleed_at_max',
    'cleave_at_max',                 # KEPT for Parashu / Caladbolg per doc — see below
    'cleave_at_max_plus_bleed',
    'stun_at_max',
    'stun_knockdown_at_max',
    'defensive_parry',
    'quick_riposte',
    'master_strike',
    'armor_pierce_at_max',
    'anti_heavy_at_max',
    'concussion_at_max',
    'rapid_shot_at_max',
    'free_stones',
    'disarm_at_max',
    'reach_disarm',
    'reach_1',                       # 1h sword class default; class ladder handles
    'reach_2',                       # spear class default; class ladder handles
}

# Explicitly PRESERVED class_mechanic values (still distinctive per-unique):
PRESERVED_CLASS_MECHS = {
    'finesse_dex',
    'guaranteed_hit',
    'returning_blow',
    'versatile',
    'str_bonus_range_7',
    'ignores_all_armor',
    'ignores_half_armor',
    'ignores_shield',
    'backstab',                      # kept for now — dagger flavor on Carnwennan / Ridill
}

# Uniques that keep their cleave_at_max legacy layered on top of the class
# ladder (per uniques_v2_14.md — Parashu and Caladbolg are cleave IDENTITY
# weapons, the extra cleave stack is intentional flavor).
CLEAVE_LEGACY_KEEP = {'parashu', 'caladbolg'}


def _class_and_variant(w: dict) -> tuple[str, bool]:
    """Return (weapon_class, is_two_handed) for a weapon dict."""
    wc = w.get('class', w.get('weapon_class', 'sword')) or 'sword'
    two_h = bool(w.get('twoHanded', w.get('two_handed', False)))
    return wc, two_h


def _formula_base(w: dict) -> int:
    """Compute the formula target base_damage for a unique."""
    wc, two_h = _class_and_variant(w)
    tier = int(w.get('tier', 1) or 1)
    mat_mult = TIER_MAT_MULT.get(tier, 1.0)

    # Scimitar special: fold under 1h sword for chain-special dispatch,
    # so its formula matches 1h sword. Large-scimitar T5 uses the 2h bump.
    if wc == 'scimitar':
        base = TWO_HANDED_BASE_BUMP['scimitar'] if two_h else SCIMITAR_BASE
    elif two_h and wc in TWO_HANDED_BASE_BUMP:
        base = TWO_HANDED_BASE_BUMP[wc]
    else:
        base = COMMON_CLASS_BASE.get(wc, 5)

    target = round(base * mat_mult * 1.5)
    return max(2, target)


def _pick_base(wid: str, w: dict) -> int:
    """Iconic exception table wins over the formula."""
    if wid in ICONIC_BASE:
        return ICONIC_BASE[wid]
    return _formula_base(w)


def _strip_redundant_mech(wid: str, w: dict) -> str | None:
    """Return the new class_mechanic value (or None if none). Strips redundant
    mechs unless the unique is in CLEAVE_LEGACY_KEEP."""
    mech = w.get('class_mechanic', '') or ''
    if not mech:
        return None
    if mech in PRESERVED_CLASS_MECHS:
        return mech
    if mech in ('cleave_at_max', 'cleave_at_max_plus_bleed') \
            and wid in CLEAVE_LEGACY_KEEP:
        return mech
    if mech in REDUNDANT_CLASS_MECHS:
        return None
    # Unknown mech: leave as-is (be conservative).
    return mech


def rebase() -> dict:
    """Apply the rebase to weapon.json. Returns a summary dict for reporting."""
    with open(WEAPON_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    summary = {
        'total': 0,
        'exp_added': 0,
        'base_changed': 0,
        'mech_stripped': 0,
        'iconic_used': 0,
        'per_class_before': {},
        'per_class_after': {},
        'sample_deltas': [],
    }

    for wid, w in data.items():
        summary['total'] += 1
        wc, _ = _class_and_variant(w)

        # 1. chain_exponent
        if 'chain_exponent' not in w and 'chainExponent' not in w:
            w['chain_exponent'] = 1.15
            summary['exp_added'] += 1

        # 2. base_damage rebase
        old_base = int(w.get('base_damage', w.get('baseDamage', 5)) or 5)
        new_base = _pick_base(wid, w)
        if new_base != old_base:
            w['base_damage'] = new_base
            # Keep the camelCase mirror consistent if present.
            if 'baseDamage' in w:
                w['baseDamage'] = new_base
            summary['base_changed'] += 1
            if wid in ICONIC_BASE:
                summary['iconic_used'] += 1

        summary['per_class_before'].setdefault(wc, []).append(old_base)
        summary['per_class_after'].setdefault(wc, []).append(new_base)

        # Save a small sample for the report.
        if abs(new_base - old_base) >= 5 and len(summary['sample_deltas']) < 20:
            summary['sample_deltas'].append((wid, w.get('name', wid), old_base, new_base))

        # 3. Strip redundant class_mechanic
        new_mech = _strip_redundant_mech(wid, w)
        if new_mech is None and w.get('class_mechanic'):
            del w['class_mechanic']
            summary['mech_stripped'] += 1
        elif new_mech is not None:
            w['class_mechanic'] = new_mech

    with open(WEAPON_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    return summary


def main():
    summary = rebase()
    print(f"Total uniques processed: {summary['total']}")
    print(f"chain_exponent added:    {summary['exp_added']}")
    print(f"base_damage changed:     {summary['base_changed']} "
          f"({summary['iconic_used']} via iconic table)")
    print(f"class_mechanic stripped: {summary['mech_stripped']}")
    print()
    print("Per-class before -> after median base_damage:")
    classes = sorted(summary['per_class_before'])
    for c in classes:
        before = sorted(summary['per_class_before'][c])
        after = sorted(summary['per_class_after'][c])
        b_med = before[len(before) // 2]
        a_med = after[len(after) // 2]
        print(f"  {c:12} n={len(before):2}  {b_med:3} -> {a_med:3}")
    print()
    print("Largest deltas (up to 20):")
    for wid, name, old, new in summary['sample_deltas']:
        print(f"  {name:32}  {old:3} -> {new:3}  (delta {new - old:+d})")


if __name__ == '__main__':
    main()
