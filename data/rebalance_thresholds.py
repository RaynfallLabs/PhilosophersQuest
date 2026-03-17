"""
Rebalance quiz thresholds so they reflect the complexity of the ACTION,
not just the tier of the item.

Rules:
  Tier   = question difficulty (1-5), unchanged
  Threshold = number of correct answers required to succeed

After this pass every tier will have a spread of thresholds (1-5),
creating the mix the designer wants.
"""
import json, os

ITEMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'items')

def load(fname):
    path = os.path.join(ITEMS, fname)
    with open(path, encoding='utf-8') as f:
        return json.load(f), path

def save(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'  saved {os.path.basename(path)}')

changed = 0

# ─────────────────────────────────────────────────────────────────────────────
# ARMOR  (geography threshold)
# Threshold is determined by slot / weight-class, NOT by tier.
# Body armour is sub-classified by tier since tier tracks weight class there.
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== ARMOR ===')
armor, armor_path = load('armor.json')

SLOT_THRESH = {
    'shirt':  1,
    'cloak':  1,
    'hands':  2,
    'feet':   2,
    'arms':   2,
    'legs':   3,
    'head':   3,
}

def body_thresh(tier):
    """Light → 3, medium → 4, heavy/artifact → 5"""
    if tier <= 1:
        return 3
    if tier <= 3:
        return 4
    return 5

for key, item in armor.items():
    slot = item.get('slot', '?')
    tier = item.get('tier', item.get('quiz_tier', 1))
    if slot == 'body':
        new_t = body_thresh(tier)
    else:
        new_t = SLOT_THRESH.get(slot, 3)
    old_t = item.get('equip_threshold', '?')
    if old_t != new_t:
        item['equip_threshold'] = new_t
        changed += 1
        print(f'  {item["name"]:40s} slot={slot} T{tier}  {old_t} -> {new_t}')

save(armor, armor_path)

# ─────────────────────────────────────────────────────────────────────────────
# SHIELDS  (geography threshold)
# Threshold by shield weight/size.
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== SHIELDS ===')
shields, shields_path = load('shield.json')

def shield_thresh(tier):
    if tier <= 1: return 2
    if tier <= 3: return 3
    if tier == 4: return 4
    return 5

for key, item in shields.items():
    tier = item.get('tier', item.get('quiz_tier', 1))
    new_t = shield_thresh(tier)
    old_t = item.get('equip_threshold', '?')
    if old_t != new_t:
        item['equip_threshold'] = new_t
        changed += 1
        print(f'  {item["name"]:40s} T{tier}  {old_t} -> {new_t}')

save(shields, shields_path)

# ─────────────────────────────────────────────────────────────────────────────
# ACCESSORIES  (history threshold)
# Rings: always thresh 2 (T1-3) or 3 (T4-5)
# Amulets: always thresh 3 (T1-3) or 4 (T4-5)
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== ACCESSORIES ===')
accs, accs_path = load('accessory.json')

def acc_thresh(slot, tier):
    if slot == 'ring':
        return 2 if tier <= 3 else 3
    else:  # amulet
        return 3 if tier <= 3 else 4

for key, item in accs.items():
    slot  = item.get('slot', 'ring')
    tier  = item.get('quiz_tier', item.get('tier', 1))
    new_t = acc_thresh(slot, tier)
    old_t = item.get('equip_threshold', '?')
    if old_t != new_t:
        item['equip_threshold'] = new_t
        changed += 1
        print(f'  {item["name"]:45s} {slot} T{tier}  {old_t} -> {new_t}')

save(accs, accs_path)

# ─────────────────────────────────────────────────────────────────────────────
# WANDS  (science threshold)
# Threshold by EFFECT power, not tier.
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== WANDS ===')
wands, wands_path = load('wand.json')

WAND_THRESH_BY_EFFECT = {
    # ── UTILITY / DETECTION  (thresh=2) ─────────────────────────────────
    'light':             2,
    'detect_monsters':   2,
    'detect_treasure':   2,
    'digging':           2,
    'mapping':           2,
    'identify_item':     2,
    'clairvoyance':      2,
    # ── DEFENSIVE / SUPPORT  (thresh=3) ─────────────────────────────────
    'heal':              3,
    'extra_heal':        3,
    'restore_body':      3,
    'sleep_monster':     3,
    'slow_monster':      3,
    'haste_self':        3,
    'levitation_self':   3,
    'invisibility_self': 3,
    'shield_self':       3,
    'fire_shield':       3,
    'cold_shield':       3,
    'reflect_self':      3,
    'phase_self':        3,
    'regeneration_self': 3,
    'dispel_magic':      3,
    'cancellation':      3,
    'teleport_self':     3,
    'boost_str':         3,
    'boost_con':         3,
    'boost_int':         3,
    # ── OFFENSIVE  (thresh=4) ────────────────────────────────────────────
    'fire_bolt':         4,
    'cold_bolt':         4,
    'lightning_bolt':    4,
    'acid_spray':        4,
    'magic_missile':     4,
    'striking':          4,
    'confuse_monster':   4,
    'fear_monster':      4,
    'blind_monster':     4,
    'charm_monster':     4,
    'curse_monster':     4,
    'poison_monster':    4,
    'disease_monster':   4,
    'weaken_monster':    4,
    'paralyze_monster':  4,
    'teleport_monster':  4,
    'create_monster':    4,
    'polymorph_monster': 4,
    'drain_magic':       4,
    'enchant_weapon':    4,
    'iron_mortar':       4,
    # ── DEADLY / POWERFUL  (thresh=5) ───────────────────────────────────
    'death_ray':         5,
    'stoning':           5,
    'disintegrate':      5,
    'nova':              5,
    'drain_life':        5,
    'life_transfer':     5,
    'earthquake':        5,
    'explosion':         5,
    'time_stop':         5,
    'wish':              5,
    'mass_confuse':      5,
    'mass_sleep':        5,
    'mass_slow':         5,
    'abjuration':        5,
}

for key, item in wands.items():
    effect  = item.get('effect', '')
    new_t   = WAND_THRESH_BY_EFFECT.get(effect)
    if new_t is None:
        print(f'  [WARN] no rule for effect={effect!r} on {item["name"]}')
        continue
    old_t = item.get('quiz_threshold', '?')
    if old_t != new_t:
        item['quiz_threshold'] = new_t
        changed += 1
        print(f'  {item["name"]:45s} effect={effect:25s}  {old_t} -> {new_t}')

save(wands, wands_path)

# ─────────────────────────────────────────────────────────────────────────────
# SCROLLS  (grammar threshold)
# Threshold by scroll content / danger.
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== SCROLLS ===')
scrolls, scrolls_path = load('scroll.json')

SCROLL_THRESH = {
    'scroll_of_heal':          2,
    'scroll_of_mapping':       2,
    'scroll_of_identify':      2,
    'scroll_of_the_labyrinth': 2,
    'scroll_of_the_gorgon':    2,
    'scroll_of_the_hoard':     2,
    'scroll_of_ragnarok':      2,
    'scroll_of_the_abyss':     2,
    'scroll_of_enchant_weapon':    3,
    'scroll_of_remove_curse':      3,
    'scroll_of_confuse_monsters':  3,
    'scroll_of_sleep':             3,
    'scroll_of_haste':             3,
    'scroll_of_enchant_armor':     3,
    'scroll_of_enchantment':       3,
    'scroll_of_teleportation':     4,
    'scroll_of_charging':          4,
    'scroll_of_identify_all':      4,
    'scroll_of_annihilation':      5,
    'scroll_of_time_stop':         5,
    'scroll_of_great_power':       5,
}

for key, item in scrolls.items():
    new_t = SCROLL_THRESH.get(key)
    if new_t is None:
        print(f'  [WARN] no rule for scroll {key!r}')
        continue
    old_t = item.get('read_threshold', '?')
    if old_t != new_t:
        item['read_threshold'] = new_t
        changed += 1
        print(f'  {item["name"]:40s}  {old_t} -> {new_t}')

save(scrolls, scrolls_path)

# ─────────────────────────────────────────────────────────────────────────────
# SPELLBOOKS  (grammar threshold)
# Threshold by spell complexity.
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== SPELLBOOKS ===')
books, books_path = load('spellbook.json')

BOOK_THRESH = {
    'spellbook_magic_missile': 2,
    'spellbook_sleep':         2,
    'spellbook_light':         2,
    'spellbook_shield':        3,
    'spellbook_fire_bolt':     3,
    'spellbook_haste':         3,
    'spellbook_heal':          3,
    'spellbook_invisibility':  3,
    'spellbook_confusion':     4,
    'spellbook_lightning':     4,
    'spellbook_displacement':  4,
    'spellbook_ice_storm':     5,
    'spellbook_paralyze':      5,
}

for key, item in books.items():
    new_t = BOOK_THRESH.get(key)
    if new_t is None:
        print(f'  [WARN] no rule for spellbook {key!r}')
        continue
    old_t = item.get('read_threshold', '?')
    if old_t != new_t:
        item['read_threshold'] = new_t
        changed += 1
        print(f'  {item["name"]:40s}  {old_t} -> {new_t}')

save(books, books_path)

print(f'\nTotal fields changed: {changed}')
