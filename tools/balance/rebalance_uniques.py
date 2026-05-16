"""Two-pass rebalance:
  1. Un-flag 19 common-tier 'uniques' (lowercase names) that are template-like
     generic weapon types. They keep their floor_spawn_weight and base_damage,
     but stop counting against unique-band quotas and stop biasing the audit.

  2. For the floor-spawning bands that drifted off the 1.3-2.0x curve target:
       - F90-99: rescale dmg UP toward 1.55x curve(peak_floor) (was 1.11x avg)
     Leave F40-89 untouched (already in band) and F10-39 mostly untouched after
     the un-flagging (most over-tuned entries were the mislabeled commons).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import curve

repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
weapons_path = os.path.join(repo, 'data', 'items', 'weapon.json')

with open(weapons_path, encoding='utf-8') as f:
    weapons = json.load(f)


# --- Pass 1: un-flag mislabeled common-tier 'uniques' --------------------
COMMON_TIER_IDS = {
    'gladius', 'pugio', 'kopis', 'francisca', 'sica',           # F10-19 starters
    'falchion', 'cinquedea', 'estoc', 'kukri', 'war_scythe',    # F30-39 commons
    'bastard_sword',
    'katana', 'dao', 'naginata', 'claymore', 'partisan',        # F50-59 commons
    'mameluke_saber', 'flamberge', 'executioners_sword',        # F70-79 commons
}
unflagged = 0
for wid in COMMON_TIER_IDS:
    if wid in weapons:
        if weapons[wid].get('is_unique'):
            weapons[wid]['is_unique'] = False
            unflagged += 1
print(f"Un-flagged {unflagged} mislabeled commons (now is_unique=False)")


# --- Pass 2: rescale under-band uniques (F90-99 at 1.11x avg) ---------
# Target: 1.55x curve at peak_floor.
TARGET_RATIO = 1.55
RESCALE_BAND = (90, 100)
adjusted = []
for k, v in weapons.items():
    if not v.get('is_unique'):
        continue
    ml = v.get('min_level', 0)
    if ml >= 100:
        continue  # plot-locked
    pf = v.get('peak_floor', 1)
    if not (RESCALE_BAND[0] <= pf < RESCALE_BAND[1]):
        continue
    expected = curve.weapon_base_damage(pf)
    current = int(v.get('baseDamage', v.get('base_damage', 0)))
    target = int(round(expected * TARGET_RATIO))
    if target > current:
        v['baseDamage'] = target
        v['base_damage'] = target
        adjusted.append((k, v.get('name'), pf, current, target))

print(f"\nRescaled {len(adjusted)} F{RESCALE_BAND[0]}-{RESCALE_BAND[1]-1} uniques up to ~{TARGET_RATIO}x curve:")
for k, name, pf, old, new in adjusted:
    print(f"  peak{pf:>3}  {name:<22}  dmg {old} -> {new}")


# --- Pass 3: cap any remaining over-tuned uniques in floor-spawn range -
# Cap at 2.0x curve(peak_floor). Don't touch plot-locked. Don't touch items
# already <=2.0x — preserve curated tuning where designers chose it.
CAP_RATIO = 2.0
capped = []
for k, v in weapons.items():
    if not v.get('is_unique'):
        continue
    ml = v.get('min_level', 0)
    if ml >= 100:
        continue
    pf = v.get('peak_floor', 1)
    expected = curve.weapon_base_damage(pf)
    current = int(v.get('baseDamage', v.get('base_damage', 0)))
    cap = int(round(expected * CAP_RATIO))
    if current > cap and cap >= 1:
        v['baseDamage'] = cap
        v['base_damage'] = cap
        capped.append((k, v.get('name'), pf, current, cap))

print(f"\nCapped {len(capped)} over-tuned uniques at {CAP_RATIO}x curve(peak_floor):")
for k, name, pf, old, new in capped:
    print(f"  peak{pf:>3}  {name:<28}  dmg {old} -> {new}")


with open(weapons_path, 'w', encoding='utf-8') as f:
    json.dump(weapons, f, indent=2, ensure_ascii=False)
print(f"\nweapon.json saved: {len(weapons)} total entries, "
      f"{sum(1 for v in weapons.values() if v.get('is_unique'))} now flagged unique.")
