"""Verify chain damage produces sane kill-turn counts vs curve targets."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import curve

# Sample weapon templates' chain multipliers (from generated templates)
TEMPLATES = {
    'dagger':    {'mod': 0.7, 'mults': [0.7, 1.5, 2.5, 4.0], 'max_rung': 4},
    'longsword': {'mod': 1.0, 'mults': [0.5, 1.0, 1.5, 2.5, 4.0, 6.0], 'max_rung': 6},
    'greatsword':{'mod': 1.45,'mults': [0.5, 1.0, 1.6, 2.7, 4.5, 6.5], 'max_rung': 6},
    'great_axe': {'mod': 1.5, 'mults': [0.5, 1.2, 2.0, 3.5, 6.5], 'max_rung': 5},
}

# Sample material multipliers
MATERIALS = {
    'copper':     0.7,
    'iron':       1.0,
    'steel':      1.15,
    'mithril':    1.2,
    'adamantine': 1.4,
    'orichalcum': 1.6,
}

def compute_kill_turns(floor, template, material, chain_rung):
    """Turns to kill a median monster at floor with given weapon+chain."""
    base = curve.weapon_base_damage(floor)
    weapon_dmg = base * template['mod'] * material
    chain_mult = template['mults'][min(chain_rung - 1, len(template['mults']) - 1)]
    chain_dmg = weapon_dmg * chain_mult
    monster_hp = curve.monster_hp_med(floor)
    monster_hp_tough = curve.monster_hp_tough(floor)
    boss_hp = curve.boss_hp_naive(floor) if floor in (20, 40, 60, 80, 100) else None
    return chain_dmg, monster_hp / chain_dmg, monster_hp_tough / chain_dmg, (boss_hp / chain_dmg if boss_hp else None)

# Headline check: iron longsword at chain 5 across the floor curve
print("=" * 90)
print("CHAIN-MATH CHECK — Iron longsword at chain rung 5, across the floor curve")
print("=" * 90)
print(f"{'Floor':>6}  {'mob_HP':>7}  {'tough':>6}  {'boss_HP':>8}  "
      f"{'chain5_dmg':>11}  {'kill_med':>9}  {'kill_tough':>11}  {'kill_boss':>10}")
print("-" * 90)
for f in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
    dmg, kt_med, kt_tough, kt_boss = compute_kill_turns(f, TEMPLATES['longsword'], MATERIALS['iron'], 5)
    boss_str = f"{curve.boss_hp_naive(f) if f in (20,40,60,80,100) else 0}".rjust(8) if f in (20,40,60,80,100) else "       -"
    kt_boss_str = f"{kt_boss:>10.1f}" if kt_boss else "         -"
    print(f"{f:>6}  {curve.monster_hp_med(f):>7}  {curve.monster_hp_tough(f):>6}  {boss_str}  "
          f"{dmg:>11.1f}  {kt_med:>9.2f}  {kt_tough:>11.2f}  {kt_boss_str}")

# Same check, but at floor-appropriate material
print()
print("=" * 90)
print("CHAIN-MATH — Floor-appropriate material at chain rung 5 (realistic play)")
print("=" * 90)
print(f"{'Floor':>6}  {'material':>11}  {'wpn_dmg':>8}  {'chain5':>7}  {'kill_med':>9}  {'kill_tough':>11}")
print("-" * 90)
floor_mats = {
    1: 'iron', 10: 'iron', 20: 'iron', 30: 'steel', 40: 'steel', 50: 'mithril',
    60: 'mithril', 70: 'mithril', 80: 'adamantine', 90: 'adamantine', 100: 'orichalcum',
}
for f, mat in floor_mats.items():
    base = curve.weapon_base_damage(f)
    wpn_dmg = base * 1.0 * MATERIALS[mat]
    chain5 = wpn_dmg * 6.0
    kt_med = curve.monster_hp_med(f) / chain5
    kt_tough = curve.monster_hp_tough(f) / chain5
    print(f"{f:>6}  {mat:>11}  {wpn_dmg:>8.2f}  {chain5:>7.1f}  {kt_med:>9.2f}  {kt_tough:>11.2f}")

# Common-play check: chain 3 (typical for a competent player)
print()
print("=" * 90)
print("CHAIN-MATH — Floor-appropriate material at chain rung 3 (TYPICAL play)")
print("=" * 90)
print(f"{'Floor':>6}  {'material':>11}  {'chain3':>7}  {'kill_med':>9}  {'kill_tough':>11}")
print("-" * 90)
for f, mat in floor_mats.items():
    base = curve.weapon_base_damage(f)
    chain3 = base * 1.0 * MATERIALS[mat] * 1.5
    kt_med = curve.monster_hp_med(f) / chain3
    kt_tough = curve.monster_hp_tough(f) / chain3
    print(f"{f:>6}  {mat:>11}  {chain3:>7.1f}  {kt_med:>9.2f}  {kt_tough:>11.2f}")

# Chain 1 — "barely scratching" check (first answer wrong, only that hit registers)
print()
print("=" * 90)
print("CHAIN-MATH — chain rung 1 (one correct answer — minimum effective hit)")
print("=" * 90)
print(f"{'Floor':>6}  {'material':>11}  {'chain1':>7}  {'kill_med':>9}  {'kill_tough':>11}")
print("-" * 90)
for f, mat in floor_mats.items():
    base = curve.weapon_base_damage(f)
    chain1 = base * 1.0 * MATERIALS[mat] * 0.5
    kt_med = curve.monster_hp_med(f) / chain1 if chain1 > 0 else 999
    kt_tough = curve.monster_hp_tough(f) / chain1 if chain1 > 0 else 999
    print(f"{f:>6}  {mat:>11}  {chain1:>7.1f}  {kt_med:>9.1f}  {kt_tough:>11.1f}")

# Boss summary at chain 5
print()
print("=" * 90)
print("BOSS KILL-TURN — chain 5 with floor-appropriate weapon")
print("=" * 90)
print(f"{'Boss':>15}  {'Floor':>5}  {'HP':>5}  {'chain5':>7}  {'naive_turns':>12}  {'with_quest':>10}")
print("-" * 90)
boss_floors = {'Asterion': 20, 'Medusa': 40, 'Fafnir': 60, 'Fenrir': 80, 'Abaddon': 100}
for name, f in boss_floors.items():
    mat = floor_mats[f]
    base = curve.weapon_base_damage(f)
    chain5 = base * 1.0 * MATERIALS[mat] * 6.0
    boss_hp = curve.boss_hp_naive(f)
    naive_turns = boss_hp / chain5
    quest_mod = 0.20  # max stack
    quest_turns = (boss_hp * quest_mod) / chain5
    print(f"{name:>15}  {f:>5}  {boss_hp:>5}  {chain5:>7.1f}  {naive_turns:>12.1f}  {quest_turns:>10.1f}")
