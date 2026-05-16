"""Merge generated unique stats INTO existing JSON entries (don't replace).
Preserves legacy symbol/color/lore/etc. and updates only the rebalanced
fields (base_damage, chain_multipliers, weight, etc.)."""
import json
import os
from glob import glob

# Fields that we want from the generated uniques (the rebalanced stats).
# Anything else (symbol, color, lore, special properties) stays from legacy.
WEAPON_REBALANCE_FIELDS = {
    'base_damage', 'chain_multipliers', 'max_chain_length',
    'weight', 'weight_lb', 'min_level', 'peak_floor', 'spread', 'peak_weight',
    'max_enchant', 'is_unique', 'weapon_class_chain', 'class_mechanic',
    'template_basis', 'damage_types', 'crit_multiplier',
}
ARTIFACT_REBALANCE_FIELDS = {
    'weight', 'weight_lb', 'min_level', 'peak_floor', 'spread', 'peak_weight',
    'is_unique', 'plot_locked', 'spawn_method', 'template_basis',
    'ac_bonus', 'special_properties',
}


def merge_fields(bank_path: str, uniques_dir: str, fields_to_update: set):
    """For each generated unique, UPDATE matching fields in the existing
    bank entry. If no existing entry, add the generated one outright."""
    with open(bank_path, encoding='utf-8') as f:
        bank = json.load(f)
    files = sorted(glob(os.path.join(uniques_dir, '*.json')))
    updated = 0
    added = 0
    for fn in files:
        with open(fn, encoding='utf-8') as f:
            entry = json.load(f)
        item_id = entry.get('id') or os.path.splitext(os.path.basename(fn))[0]
        # Normalize weight_lb -> weight (the code reads `weight`)
        if 'weight_lb' in entry and 'weight' not in entry:
            entry['weight'] = entry.pop('weight_lb')
        if item_id in bank:
            existing = bank[item_id]
            for k in fields_to_update:
                if k in entry:
                    existing[k] = entry[k]
            updated += 1
        else:
            # New entry — need to ensure it has all required Item fields
            # by pulling sane defaults from existing similar items if missing
            if 'symbol' not in entry: entry['symbol'] = '('
            if 'color' not in entry: entry['color'] = [180, 180, 180]
            if 'weight' not in entry: entry['weight'] = 1.0
            defn = {k: v for k, v in entry.items() if k != 'id'}
            bank[item_id] = defn
            added += 1
    with open(bank_path, 'w', encoding='utf-8') as f:
        json.dump(bank, f, indent=2, ensure_ascii=False)
    return len(bank), updated, added


total, updated, added = merge_fields(
    'data/items/weapon.json',
    'tools/balance/generated/uniques/weapons',
    WEAPON_REBALANCE_FIELDS,
)
print(f"weapon.json: {total} entries, {updated} updated, {added} added")

total, updated, added = merge_fields(
    'data/items/artifact.json',
    'tools/balance/generated/uniques/artifacts',
    ARTIFACT_REBALANCE_FIELDS,
)
print(f"artifact.json: {total} entries, {updated} updated, {added} added")
