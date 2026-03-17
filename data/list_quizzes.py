"""Generate a complete list of all quizzes in Philosopher's Quest."""
import json
import os

DATA = os.path.dirname(os.path.abspath(__file__))
ITEMS = os.path.join(DATA, 'items')

rows = []

def add(action, subject, mode, tier, threshold_or_chain):
    rows.append((subject, action, mode, tier, threshold_or_chain))

# ── Item files ──────────────────────────────────────────────────────────────

def load(fname):
    with open(os.path.join(ITEMS, fname), encoding='utf-8') as f:
        data = json.load(f)
    # Normalize: both list-of-dicts and dict-of-dicts supported
    if isinstance(data, dict):
        return list(data.values())
    return data

# Weapons (combat = math chain)
for item in load('weapon.json'):
    t = item.get('quiz_tier', item.get('tier', 1))
    add(f"Weapon: {item['name']}", 'math', 'chain', t, f"chain (score=dmg)")

# Armor (geography threshold)
for item in load('armor.json'):
    t = item.get('quiz_tier', item.get('tier', 1))
    th = item.get('equip_threshold', t + 1)
    add(f"Armor: {item['name']}", 'geography', 'threshold', t, th)

# Shields (geography threshold)
for item in load('shield.json'):
    t = item.get('quiz_tier', item.get('tier', 1))
    th = item.get('equip_threshold', t + 1)
    add(f"Shield: {item['name']}", 'geography', 'threshold', t, th)

# Accessories (history threshold)
for item in load('accessory.json'):
    t = item.get('quiz_tier', item.get('tier', 1))
    th = item.get('equip_threshold', t + 1)
    add(f"Accessory: {item['name']}", 'history', 'threshold', t, th)

# Wands (science threshold)
for item in load('wand.json'):
    t = item.get('quiz_tier', item.get('tier', 1))
    th = item.get('use_threshold', t + 1)
    add(f"Wand: {item['name']}", 'science', 'threshold', t, th)

# Scrolls (grammar threshold)
for item in load('scroll.json'):
    t = item.get('quiz_tier', item.get('tier', 1))
    th = item.get('read_threshold', t + 1)
    add(f"Scroll: {item['name']}", 'grammar', 'threshold', t, th)

# Spellbooks (grammar threshold)
for item in load('spellbook.json'):
    t = item.get('quiz_tier', item.get('tier', 1))
    th = item.get('read_threshold', t + 1)
    add(f"Spellbook: {item['name']}", 'grammar', 'threshold', t, th)

# Ingredients / harvesting (animal threshold)
ing_path = os.path.join(ITEMS, 'ingredient.json')
with open(ing_path, encoding='utf-8') as f:
    ingredients = json.load(f)
for ing_id, ing in ingredients.items():
    t = ing.get('harvest_tier', 1)
    th = ing.get('harvest_threshold', 2)
    add(f"Harvest: {ing.get('name', ing_id)}", 'animal', 'threshold', t, th)

# ── Non-item quiz triggers ───────────────────────────────────────────────────

# Cooking — escalator_chain per ingredient tier
for ing_id, ing in ingredients.items():
    t = ing.get('harvest_tier', 1)
    add(f"Cook: {ing.get('name', ing_id)}", 'cooking', 'escalator_chain', t, 'chain (score=quality)')

# Lockpicking — economics threshold (tiers 1-5 mapped to dungeon level)
for tier in range(1, 6):
    add(f"Lockpick (T{tier} lock)", 'economics', 'threshold', tier, tier + 1)

# Identification — philosophy threshold
for tier in range(1, 6):
    add(f"Identify item (T{tier})", 'philosophy', 'threshold', tier, tier + 1)

# Corpse lore — philosophy threshold
for tier in range(1, 6):
    add(f"Corpse lore (harvest T{tier})", 'philosophy', 'threshold', tier, tier + 2)

# Prayer — theology threshold (tier scales with dungeon level L1-20=T1 ... L81-100=T5)
for tier in range(1, 6):
    levels = f"L{(tier-1)*20+1}-{tier*20}"
    add(f"Pray ({levels})", 'theology', 'threshold', tier, tier + 1)

# Recall Lore — history escalator_chain
add("Recall Lore (N key)", 'history', 'escalator_chain', '1-5', 'chain (score=cooldown)')

# Mysteries — philosophy escalator_threshold
add("Mystery approach", 'philosophy', 'escalator_threshold', '1-5', 'escalating threshold')

# Combat spells (cast from spellbook, math chain)
add("Cast spell (spellbook)", 'math', 'chain', '1-5', 'chain (score=dmg)')

# ── Print sorted table ───────────────────────────────────────────────────────

SUBJECT_ORDER = ['math', 'geography', 'history', 'animal', 'cooking',
                 'science', 'philosophy', 'grammar', 'economics', 'theology']

MODE_ABBREV = {
    'chain':                'flat chain',
    'threshold':            'flat threshold',
    'escalator_chain':      'escalating chain',
    'escalator_threshold':  'escalating threshold',
}

rows.sort(key=lambda r: (SUBJECT_ORDER.index(r[0]) if r[0] in SUBJECT_ORDER else 99,
                          str(r[3]), r[1]))

current_subject = None
for subject, action, mode, tier, th in rows:
    if subject != current_subject:
        print(f"\n{'='*78}")
        print(f"  SUBJECT: {subject.upper()}")
        print(f"{'='*78}")
        print(f"  {'Action':<45} {'Mode':<22} {'Tier':<6} {'Threshold/Chain'}")
        print(f"  {'-'*45} {'-'*22} {'-'*6} {'-'*15}")
        current_subject = subject
    mode_str = MODE_ABBREV.get(mode, mode)
    print(f"  {action:<45} {mode_str:<22} {str(tier):<6} {th}")

print(f"\n{'='*78}")
print(f"  Total quiz triggers: {len(rows)}")
print(f"{'='*78}\n")
