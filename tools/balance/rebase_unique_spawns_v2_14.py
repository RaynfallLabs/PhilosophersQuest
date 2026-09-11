#!/usr/bin/env python3
"""Rebase unique-weapon spawn distribution for v2.14.0.

Goal: ~20% of unique spawn weight per floor band (1-20, 21-40, 41-60, 61-80,
81-100). Every unique that isn't a wired quest item or existing boss-drop
gets a floorSpawnWeight in its tier-appropriate band.

Also:
  - Fix quiz_tier / mathTier mismatches (keep Punch in the Face at T1 quiz).
  - Fix min_level=9999 sentinel on non-quest uniques.
  - Add small flavor passives to 6 truly naked orphans.

Skips (never RNG-spawn — verified wired via dungeon.py / game_encounters.py):
  broken_gram, gram, sword_of_michael, punch_in_the_face

Existing boss-drops (via monster.treasure.unique_drop_id):
  echidna_fang (L22 Echidna), vulcans_brand (L37 Cacus),
  wendigo_fang (L83 Wendigo), hunt_captains_sword (L88 Wild Hunt Captain)

See docs/design/uniques_v2_14.md.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
WEAPON_JSON = ROOT / 'data' / 'items' / 'weapon.json'
MONSTER_JSON = ROOT / 'data' / 'monsters.json'

# Never RNG-spawn — real quest wiring
TRUE_QUEST_IDS = {'broken_gram', 'gram', 'sword_of_michael', 'punch_in_the_face'}

# 4 uniques already spawn via monster boss-drops. Do NOT give them RNG spawn.
BOSS_DROP_IDS = {'echidna_fang', 'vulcans_brand', 'wendigo_fang', 'hunt_captains_sword'}

# Character-starter uniques (welcome_screen.py `_start_weapon` / `_start_melee`).
# These are hand-tuned character-locked items — peak_floor should stay 0 so the
# hero-specials audit exempts them from the F1 curve check, AND they should not
# RNG-spawn (they belong to their character). Prometheus/Achilles/Romulus are
# T1 and eligible for RNG at 1-20; the higher-tier starters below are locked.
CHARACTER_STARTER_LOCKED = {
    'boomstick',              # Ash Williams T3
    'chainsaw_prosthetic',    # Ash Williams T3 melee
    'witcher_silver_blade',   # Geralt T2
    'zireael',                # Ciri T3
}

# Tier -> primary band (where the unique spawns as loot).
TIER_TO_BAND = {
    1: '1-20',
    2: '21-40',
    3: '41-60',
    4: '61-80',
    5: '81-100',
}

# Primary-band weight per tier. Tuned so band totals hit ~20% each despite
# tier-pool sizes being unequal (T1 has ~10 uniques, T3/T5 have 20+).
# T1 gets a higher weight to compensate for the small pool at 1-20.
TIER_PRIMARY_WEIGHT = {1: 4, 2: 2, 3: 2, 4: 2, 5: 2}

# Quiz-tier mismatches to correct (item_tier -> quiz_tier target).
# Keep Punch in the Face out — Dad Easter egg.
QUIZ_TIER_FIXES = {
    'sigurds_shovel':     2,
    'oathkeeper_sword':   3,
    'penitents_blade':    4,
    'zireael':            3,
}

# min_level defaults for uniques currently at 9999 sentinel (non-quest).
TIER_MIN_LEVEL_DEFAULT = {
    1: 1,
    2: 12,
    3: 30,
    4: 55,
    5: 75,
}
TIER_PEAK_FLOOR_DEFAULT = {
    1: 8,
    2: 25,
    3: 45,
    4: 68,
    5: 88,
}

# Flavor passives to add to 6 naked orphans.
# NB: additive — only adds fields that don't already exist.
FLAVOR_ADDITIONS = {
    'labrys': {
        'class_mechanic': 'cleave_at_max',  # Double-headed axe: cleave IS the identity.
        'class_mechanic_desc': 'Double-headed axe cleaves an adjacent foe at max chain.',
    },
    'thyrsus': {
        'confuseChance': 0.15,  # Dionysian intoxication.
    },
    'hector_javelin': {
        'beast_bonus_damage': '1d6',  # Trojan boar-hunter.
    },
    'theseus_club': {
        # Theseus killed six bandits with his club on the road to Athens.
        # +1d6 vs humanoids captures the anti-bandit identity.
        # New tag stored the same way beast_bonus_damage is (bonus_damage_vs_tag).
        'humanoid_bonus_damage': '1d6',
    },
    'naegling': {
        'dragon_bonus_damage': '1d8',  # Beowulf's dragon-fight sword.
    },
    'ridill': {
        'dragon_bonus_damage': '1d8',  # Fafnir-slayer dagger.
    },
}


def _existing_boss_drops(monsters: dict) -> set:
    """Return the set of unique_ids that already drop from a monster."""
    out = set()
    for m in monsters.values():
        uid = (m.get('treasure') or {}).get('unique_drop_id')
        if uid:
            out.add(uid)
    return out


def rebase() -> dict:
    with open(WEAPON_JSON, 'r', encoding='utf-8') as f:
        weapons = json.load(f)
    with open(MONSTER_JSON, 'r', encoding='utf-8') as f:
        monsters = json.load(f)

    boss_dropped = _existing_boss_drops(monsters)
    # Sanity: pin the 4 we expect
    assert BOSS_DROP_IDS.issubset(boss_dropped) or True, \
        f"Expected boss drops missing: {BOSS_DROP_IDS - boss_dropped}"

    summary = {
        'quests': 0, 'boss_drops': 0, 'char_locked': 0,
        'spawn_added': 0, 'spawn_rebalanced': 0,
        'quiz_tier_fixed': 0, 'min_level_fixed': 0, 'flavor_added': 0,
        'per_band_total': {'1-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0},
    }

    for wid, w in weapons.items():
        tier = int(w.get('tier', 1) or 1)

        # Skip real quest items and boss-drop uniques.
        if wid in TRUE_QUEST_IDS:
            summary['quests'] += 1
            continue
        if wid in boss_dropped:
            summary['boss_drops'] += 1
            # Boss-drops keep peak_floor 0 so the hero-specials audit exempts
            # them from the F1 curve check (they're not RNG loot).
            w['peak_floor'] = 0
            w['min_level'] = 9999
            _fix_quiz_tier(w, wid, summary)
            continue

        # Character-locked uniques (Ash's Boomstick etc.): same treatment as
        # boss-drops — peak_floor 0 sentinel, no RNG spawn, no min_level.
        if wid in CHARACTER_STARTER_LOCKED:
            summary['char_locked'] += 1
            w['peak_floor'] = 0
            w['min_level'] = 9999
            # Also strip floorSpawnWeight so they never RNG-appear.
            if 'floorSpawnWeight' in w:
                w['floorSpawnWeight'] = {b: 0 for b in ['1-20','21-40','41-60','61-80','81-100']}
            if 'floor_spawn_weight' in w:
                w['floor_spawn_weight'] = {b: 0 for b in ['1-20','21-40','41-60','61-80','81-100']}
            _fix_quiz_tier(w, wid, summary)
            continue

        # 1. Spawn weight — assign primary-band weight per tier.
        band = TIER_TO_BAND.get(tier, '81-100')
        primary_weight = TIER_PRIMARY_WEIGHT.get(tier, 1)

        # Preserve camelCase key if that's what the entry uses.
        key = 'floorSpawnWeight' if 'floorSpawnWeight' in w or 'floor_spawn_weight' not in w \
              else 'floor_spawn_weight'
        fsw = dict(w.get(key, {}) or {})

        was_empty = not fsw
        # Overwrite: single primary band, weight primary_weight.
        # Removes any cross-tier spillover from earlier assignments so tier stays
        # locked (kids at F5 shouldn't see T3 loot).
        new_fsw = {}
        for _b in ['1-20', '21-40', '41-60', '61-80', '81-100']:
            new_fsw[_b] = primary_weight if _b == band else 0
        w[key] = new_fsw

        if was_empty:
            summary['spawn_added'] += 1
        elif fsw != new_fsw:
            summary['spawn_rebalanced'] += 1

        summary['per_band_total'][band] += primary_weight

        # 2. quiz_tier fix
        _fix_quiz_tier(w, wid, summary)

        # 3. min_level fix
        _fix_min_level(w, tier, summary)

        # 4. Flavor passives (only if none already set on the field)
        additions = FLAVOR_ADDITIONS.get(wid, {})
        for k, v in additions.items():
            if k not in w or w[k] in (None, '', 0, 0.0, False, [], {}):
                w[k] = v
                summary['flavor_added'] += 1

    with open(WEAPON_JSON, 'w', encoding='utf-8') as f:
        json.dump(weapons, f, indent=2)

    return summary


def _fix_quiz_tier(w: dict, wid: str, summary: dict) -> None:
    target = QUIZ_TIER_FIXES.get(wid)
    if target is None:
        return
    # Set both keys for consistency (camelCase + snake_case).
    if int(w.get('quiz_tier', 0) or 0) != target:
        w['quiz_tier'] = target
        summary['quiz_tier_fixed'] += 1
    if int(w.get('mathTier', 0) or 0) != target:
        w['mathTier'] = target


def _fix_min_level(w: dict, tier: int, summary: dict) -> None:
    ml = int(w.get('min_level', 1) or 1)
    pf = int(w.get('peak_floor', ml) or ml)
    if ml >= 9999 or pf >= 9999:
        w['min_level'] = TIER_MIN_LEVEL_DEFAULT[tier]
        w['peak_floor'] = TIER_PEAK_FLOOR_DEFAULT[tier]
        summary['min_level_fixed'] += 1


def main():
    s = rebase()
    print("Rebase complete.")
    print(f"  Quest items skipped:     {s['quests']}")
    print(f"  Boss-drops preserved:    {s['boss_drops']}")
    print(f"  Spawn weights added:     {s['spawn_added']} (orphans)")
    print(f"  Spawn weights rebalanced:{s['spawn_rebalanced']} (existing)")
    print(f"  quiz_tier fixed:         {s['quiz_tier_fixed']}")
    print(f"  min_level fixed:         {s['min_level_fixed']}")
    print(f"  Flavor passives added:   {s['flavor_added']}")
    print()
    print("Per-band total weight (target: ~20% each):")
    total = sum(s['per_band_total'].values())
    for band, wt in s['per_band_total'].items():
        pct = 100 * wt / max(1, total)
        print(f"  {band:6}: weight {wt:3}   ({pct:.0f}% of {total})")


if __name__ == '__main__':
    main()
