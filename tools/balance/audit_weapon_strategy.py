"""Honest audit: do all weapons have distinct reasons to use them, are
their distributions correct, are quiz tiers properly tied to math tier?"""
import json
from glob import glob
from collections import Counter, defaultdict
import math
import sys
sys.path.insert(0, 'tools/balance')
import curve

# ============================================================
# Q1: Do all base weapon templates have a distinct strategy?
# ============================================================
print("=" * 78)
print(" Q1: WEAPON TEMPLATE STRATEGIC DISTINCTION")
print("=" * 78)
templates = {}
for fn in sorted(glob('data/templates/weapons/*.json')):
    with open(fn) as f:
        t = json.load(f)
    templates[t['id']] = t

# Group by mechanic — duplicates are a problem
by_mech = defaultdict(list)
for tid, t in templates.items():
    by_mech[t.get('class_mechanic', '')].append((tid, t.get('weapon_class_chain', '?')))

print("\nMechanic clusters (anything with >1 template is a potential duplicate):")
for mech, tids in sorted(by_mech.items(), key=lambda kv: (-len(kv[1]), kv[0])):
    is_real_dupe = len(tids) > 1
    flag = "  <-- DUPLICATE MECHANIC" if is_real_dupe else ""
    flavor = "  (passive/flavor, no chain reward)" if mech in (
        'primitive', 'clean', 'ranged_precision', 'cheap_ammo', 'versatile',
        'ignores_shield', 'reach_1', 'reach_2', 'finesse_dex',
        'str_bonus_range_7', 'range_8', 'ignores_half_armor', 'ignores_all_armor',
        'reach_disarm',
    ) else ""
    print(f"  {mech:<28}  -> {[t[0] for t in tids]}{flag}{flavor}")

# Flag strategic gaps
print("\nWeapons with NO mechanical differentiator (only flavor/passive):")
weak_mechanics = {'primitive', 'clean', 'ranged_precision', 'cheap_ammo'}
for tid, t in templates.items():
    if t.get('class_mechanic', '') in weak_mechanics:
        print(f"  - {tid} ({t.get('weapon_class_chain')}, class_mechanic='{t.get('class_mechanic')}')")

print()
print("=" * 78)
print(" Q2: TEMPLATE STRATEGIC DISTINCTION SUMMARY")
print("=" * 78)
print("Distinct mechanics with real combat impact:")
real_impacts = set()
for t in templates.values():
    mech = t.get('class_mechanic', '')
    if mech and mech not in weak_mechanics:
        real_impacts.add(mech)
print(f"  Count: {len(real_impacts)} / {len(templates)} templates have distinct combat-impacting mechanics")
print(f"  Templates with mere flavor/passive (no chain reward): {sum(1 for t in templates.values() if t.get('class_mechanic') in weak_mechanics)}")

# ============================================================
# Q3: Material peak_floor distribution / spawn bell health
# ============================================================
print()
print("=" * 78)
print(" Q3: MATERIAL SPAWN BELL — distribution at each floor band")
print("=" * 78)
materials = []
for fn in sorted(glob('data/materials/weapons/*.json')):
    with open(fn) as f:
        m = json.load(f)
    materials.append(m)

def spawn_weight(mat, floor):
    peak = mat.get('peak_floor', 1)
    spread = max(1, mat.get('spread', 10))
    pw = float(mat.get('peak_weight', 0))
    if pw <= 0: return 0
    dist = floor - peak
    bell = math.exp(-(dist**2)/(2*spread**2))
    return max(0.02, pw * bell) if bell > 0.005 else 0

print(f"  {'floor':>5}  {'top_3_materials_by_weight':<60}  {'total_eligible_mats'}")
for f in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
    weighted = [(m['id'], spawn_weight(m, f)) for m in materials]
    weighted = [w for w in weighted if w[1] > 0]
    top3 = sorted(weighted, key=lambda x: -x[1])[:3]
    top3_str = ", ".join(f"{n}({w:.1f})" for n, w in top3)
    print(f"  {f:>5}  {top3_str:<60}  {len(weighted)}")

# ============================================================
# Q4: Quiz tier tied to material strength
# ============================================================
print()
print("=" * 78)
print(" Q4: WEAPON QUIZ_TIER vs MATERIAL TIER (math difficulty progression)")
print("=" * 78)
print("Material -> quiz_tier mapping (derived from material.peak_floor // 20 + 1):")
print(f"  {'material':<14}  {'peak_floor':>10}  {'quiz_tier':>9}  {'spawn_band':<14}")
for m in sorted(materials, key=lambda x: x.get('peak_floor', 0)):
    pf = m.get('peak_floor', 1)
    qt = max(1, pf // 20 + 1)
    sp = m.get('spread', 10)
    band = f"F{max(1,pf-sp)}-F{min(100,pf+sp)}"
    print(f"  {m['id']:<14}  {pf:>10}  {qt:>9}  {band:<14}")
