"""Merge all monster batch files into monsters.json, deduplicating by ID."""
import json
import sys

def load(path):
    try:
        return json.load(open(path, encoding='utf-8'))
    except FileNotFoundError:
        print(f"  SKIP (not found): {path}")
        return {}

base = load('data/monsters.json')
batches = [
    'data/monsters_batch_mythology.json',
    'data/monsters_batch_dnd.json',
    'data/monsters_batch_undead.json',
    'data/monsters_batch_beasts.json',
    'data/monsters_batch_humanoids.json',
]

base_ids = set(base.keys())
added = 0
skipped = []

for path in batches:
    batch = load(path)
    for mid, mdef in batch.items():
        if mid in base_ids:
            skipped.append(mid)
        else:
            base[mid] = mdef
            base_ids.add(mid)
            added += 1

print(f"Base monsters: {len(base) - added}")
print(f"Added: {added}")
print(f"Skipped duplicates ({len(skipped)}): {', '.join(skipped[:20])}")
print(f"Total: {len(base)}")

# Validate all required fields
required = ['name', 'symbol', 'color', 'hp', 'speed', 'ai_pattern',
            'min_level', 'thac0', 'frequency', 'attacks',
            'resistances', 'weaknesses', 'harvest_tier', 'harvest_threshold']
issues = []
for mid, m in base.items():
    for field in required:
        if field not in m:
            issues.append(f"{mid}: missing {field}")

if issues:
    print(f"\nVALIDATION ISSUES ({len(issues)}):")
    for i in issues[:30]:
        print(f"  {i}")
else:
    print("\nAll monsters valid.")

with open('data/monsters.json', 'w', encoding='utf-8') as f:
    json.dump(base, f, indent=2, ensure_ascii=False)
print("Saved monsters.json")
