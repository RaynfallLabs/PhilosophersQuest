"""One-shot cleanup:
  1. Remove svalinn_shield duplicate (svalinn is canonical — has fire_reflect)
  2. Promote dragonscale_armor and dragonscale_cloak from set-pieces to uniques
     (drop the dead-content set_id, capitalize names, mark is_unique=true,
      add proper spawn fields).
"""
import json

# --- 1. Shield duplicate cleanup ---
with open('data/items/shield.json', encoding='utf-8') as f:
    shields = json.load(f)

# Confirm canonical 'svalinn' has fire_reflect (its identity)
canonical = shields.get('svalinn', {})
print(f"Canonical svalinn fire_reflect: {canonical.get('fire_reflect')}")

# Remove the stats-only duplicate
if 'svalinn_shield' in shields:
    del shields['svalinn_shield']
    print("Removed svalinn_shield (duplicate, no special property)")

# Strip the _duplicate_of marker from svalinn (no longer needed)
if '_duplicate_of' in shields.get('svalinn', {}):
    del shields['svalinn']['_duplicate_of']
    print("Cleared _duplicate_of marker on svalinn")

with open('data/items/shield.json', 'w', encoding='utf-8') as f:
    json.dump(shields, f, indent=2, ensure_ascii=False)
print(f"shield.json now has {len(shields)} entries")
print()

# --- 2. Dragonscale promotion ---
with open('data/items/armor.json', encoding='utf-8') as f:
    armor = json.load(f)

for old_id, new_name, new_id, template_basis, ac_bump in (
    ('dragonscale_armor', 'Dragonscale Plate', 'dragonscale_plate', 'plate', 8),
    ('dragonscale_cloak', 'Dragonscale Cloak', 'dragonscale_cloak', 'cloak', 3),
):
    if old_id not in armor:
        print(f"Skipping {old_id} (not found)")
        continue
    entry = armor[old_id]
    # Capitalize name to mark as proper unique
    entry['name'] = new_name
    entry['is_unique'] = True
    entry['template_basis'] = template_basis
    entry['ac_bonus'] = ac_bump
    # Drop the dead-set mechanic — single-member sets have no payoff
    entry.pop('set_id', None)
    entry.pop('set_name', None)
    # Add soft spawn fields (these are floor-spawning uniques, not plot-locked)
    entry['peak_floor'] = 88
    entry['spread'] = 10
    entry['peak_weight'] = 0.35
    entry['max_enchant'] = 3 if template_basis == 'plate' else 2
    # Keep fire/acid resistances (the actual identity)
    # Move to canonical id if needed (no rename — both already use sensible IDs)
    if old_id != new_id:
        armor[new_id] = entry
        del armor[old_id]
    print(f"Promoted {old_id} -> '{new_name}' (is_unique, ac={ac_bump}, peak F88)")

with open('data/items/armor.json', 'w', encoding='utf-8') as f:
    json.dump(armor, f, indent=2, ensure_ascii=False)
print(f"armor.json now has {len(armor)} entries")
