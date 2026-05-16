"""One-shot script: merge per-file generated uniques into the legacy JSON banks.
Run from project root."""
import json
import os
import shutil
from glob import glob


def merge_into_bank(bank_path: str, uniques_dir: str, *, replace_all: bool = False):
    """Merge per-file uniques in uniques_dir into bank_path. By default,
    overwrites existing entries by id and preserves anything else (common-tier).
    With replace_all=True, the bank is replaced entirely."""
    with open(bank_path, encoding='utf-8') as f:
        bank = json.load(f)
    if replace_all:
        bank = {}
    files = sorted(glob(os.path.join(uniques_dir, '*.json')))
    added = 0
    overwritten = 0
    for fn in files:
        with open(fn, encoding='utf-8') as f:
            entry = json.load(f)
        item_id = entry.get('id') or os.path.splitext(os.path.basename(fn))[0]
        if item_id in bank:
            overwritten += 1
        else:
            added += 1
        # strip 'id' from the value (it's already the key)
        defn = {k: v for k, v in entry.items() if k != 'id'}
        bank[item_id] = defn
    with open(bank_path, 'w', encoding='utf-8') as f:
        json.dump(bank, f, indent=2, ensure_ascii=False)
    return len(bank), added, overwritten


def replace_bank(bank_path: str, source_path: str):
    """Replace a bank file with a generated single-file bank."""
    shutil.copy(source_path, bank_path)


# Merge unique weapons into weapon.json (preserve legacy common-tier for start kits)
total, added, overwritten = merge_into_bank(
    'data/items/weapon.json',
    'tools/balance/generated/uniques/weapons',
)
print(f"weapon.json: {total} entries total ({added} new, {overwritten} overwritten)")

# Merge unique artifacts (some are new entries like Vidar's Sandal — keep legacy too)
total, added, overwritten = merge_into_bank(
    'data/items/artifact.json',
    'tools/balance/generated/uniques/artifacts',
)
print(f"artifact.json: {total} entries total ({added} new, {overwritten} overwritten)")

# Replace single-file banks wholesale (these have been completely regenerated)
for bank, src in [
    ('data/items/wand.json',       'tools/balance/generated/data/wand.json.culled'),
    ('data/items/scroll.json',     'tools/balance/generated/data/scroll.json'),
    ('data/items/spellbook.json',  'tools/balance/generated/data/spellbook.json'),
    ('data/items/ingredient.json', 'tools/balance/generated/data/ingredient.json'),
    ('data/items/recipes.json',    'tools/balance/generated/data/recipes.json'),
]:
    replace_bank(bank, src)
    with open(bank, encoding='utf-8') as f:
        count = len(json.load(f))
    print(f"{bank}: replaced wholesale, now {count} entries")

# Accessories: replace from per-file generated entries (Agent D wrote 195 individual files)
import json as _j
out = {}
for fn in sorted(glob('tools/balance/generated/uniques/accessories/*.json')):
    with open(fn) as f:
        e = _j.load(f)
    out[e['id']] = {k: v for k, v in e.items() if k != 'id'}
with open('data/items/accessory.json', 'w', encoding='utf-8') as f:
    _j.dump(out, f, indent=2, ensure_ascii=False)
print(f"accessory.json: replaced wholesale, now {len(out)} entries")
