"""Rebalance unique shields against the curve. Inline pass (small scope: 11 uniques).

Common-tier shields (wooden, hide, iron, bronze, steel, mithril, crystal,
obsidian, dragonscale, adamantine) stay as legacy entries for starting-
equipment lookups. The template+material runtime handles their spawn.

Uniques get:
  - is_unique: true
  - peak_floor / spread / peak_weight (soft bell-curve spawn)
  - template_basis (kite_shield / tower_shield / etc.)
  - max_enchant 2 (shield slot convention)
  - Realistic weight per AD&D-style reference (towers heavy, bucklers light)
  - Plot-locked uniques: peak_weight=0, plot_locked=true, spawn_method

Run from project root: py tools/balance/rebalance_shields.py
"""
import json
import os

BANK_PATH = 'data/items/shield.json'

# Manually-curated rebalance for each unique shield.
# Format: id -> { fields to set/update }
REBALANCE: dict[str, dict] = {
    'greater_aegis_of_athena': {
        'is_unique': True,
        'template_basis': 'kite_shield',
        'min_level': 65, 'peak_floor': 70, 'spread': 12, 'peak_weight': 0.4,
        'weight': 8.0,             # bronze-trimmed kite, heavy for its day
        'ac_bonus': 5,              # legendary, matches +5 design ceiling
        'max_enchant': 2,
    },
    'svalinn_shield': {
        'is_unique': True,
        'template_basis': 'heavy_wooden',
        'min_level': 55, 'peak_floor': 62, 'spread': 12, 'peak_weight': 0.4,
        'weight': 10.0,
        'ac_bonus': 4,
        'max_enchant': 2,
    },
    'svalinn': {
        'is_unique': True,
        'template_basis': 'heavy_wooden',
        'min_level': 50, 'peak_floor': 58, 'spread': 12, 'peak_weight': 0.4,
        'weight': 10.0,
        'ac_bonus': 4,
        'max_enchant': 2,
        '_duplicate_of': 'svalinn_shield',  # flag for cleanup later
    },
    'pridwen': {
        'is_unique': True,
        'template_basis': 'kite_shield',
        'min_level': 55, 'peak_floor': 60, 'spread': 12, 'peak_weight': 0.4,
        'weight': 9.0,
        'ac_bonus': 4,
        'max_enchant': 2,
    },
    'tower_shield_of_ajax': {
        'is_unique': True,
        'template_basis': 'tower_shield',
        'min_level': 65, 'peak_floor': 72, 'spread': 10, 'peak_weight': 0.35,
        'weight': 30.0,             # FIX: was 9 lb — tower shields are heavy
        'ac_bonus': 6,
        'max_enchant': 2,
    },
    'scutum_of_aeneas': {
        'is_unique': True,
        'template_basis': 'tower_shield',
        'min_level': 60, 'peak_floor': 65, 'spread': 12, 'peak_weight': 0.4,
        'weight': 18.0,             # FIX: was 6 lb — Roman scutum is heavy
        'ac_bonus': 5,
        'max_enchant': 2,
    },
    'bronze_aegis': {
        'is_unique': True,
        'template_basis': 'tower_shield',
        'min_level': 1,
        'plot_locked': True, 'spawn_method': 'quest_spawn_aegis_pre',
        'peak_floor': 1, 'spread': 1, 'peak_weight': 0.0,
        'weight': 15.0,
        'ac_bonus': 3,              # lower than the Greater Aegis (it's the precursor)
        'max_enchant': 2,
    },
    'aegis_of_athena': {
        'is_unique': True,
        'template_basis': 'kite_shield',
        'min_level': 1,
        'plot_locked': True, 'spawn_method': 'medusa_quest_athena_altar',
        'peak_floor': 1, 'spread': 1, 'peak_weight': 0.0,
        'weight': 10.0,
        'ac_bonus': 5,              # legendary boss-quest reward
        'max_enchant': 2,
    },
    'lionheart_shield': {
        'is_unique': True,
        'template_basis': 'kite_shield',
        'min_level': 1,
        'plot_locked': True, 'spawn_method': 'rare_drop',
        'peak_floor': 1, 'spread': 1, 'peak_weight': 0.0,
        'weight': 9.0,
        'ac_bonus': 4,
        'max_enchant': 2,
    },
    'shield_of_the_spartans': {
        'is_unique': True,
        'template_basis': 'heavy_wooden',
        'min_level': 12, 'peak_floor': 18, 'spread': 10, 'peak_weight': 0.45,
        'weight': 10.0,
        'ac_bonus': 3,
        'max_enchant': 2,
    },
    'ancile': {
        'is_unique': True,
        'template_basis': 'kite_shield',
        'min_level': 30, 'peak_floor': 36, 'spread': 12, 'peak_weight': 0.4,
        'weight': 6.0,
        'ac_bonus': 3,              # AC modest — power is in quiz_timer_bonus
        'max_enchant': 2,
    },
}


def main() -> None:
    with open(BANK_PATH, encoding='utf-8') as f:
        bank = json.load(f)
    updated = 0
    skipped_unknown = []
    for sid, fields in REBALANCE.items():
        if sid not in bank:
            skipped_unknown.append(sid)
            continue
        for k, v in fields.items():
            bank[sid][k] = v
        updated += 1
    with open(BANK_PATH, 'w', encoding='utf-8') as f:
        json.dump(bank, f, indent=2, ensure_ascii=False)
    print(f"Rebalanced {updated}/{len(REBALANCE)} unique shields.")
    if skipped_unknown:
        print(f"Not found in bank (skipped): {skipped_unknown}")
    # Sanity-check totals
    total = len(bank)
    uniques = sum(1 for v in bank.values() if v.get('is_unique'))
    plot_locked = sum(1 for v in bank.values() if v.get('plot_locked'))
    print(f"Bank now: {total} total, {uniques} unique, {plot_locked} plot-locked")


if __name__ == '__main__':
    main()
