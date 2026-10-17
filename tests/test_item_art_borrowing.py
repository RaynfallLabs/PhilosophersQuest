"""No item may show another item's picture with a contradictory meaning
(bug bash 4, call 17 / finding UI-23, 2026-10-17).

renderer._resolve_item_sprite_path falls back to a family picture when an item
has no <id>.png of its own: wands by effect, scrolls by effect, spellbooks by
spell family, collapsed rings and amulets by stat, a few uniques by hand. The bug
bash found 193 items borrowing that way, some with the opposite meaning: the
weaken-monster wand drew the empowerment wand, Solomon's signet drew a
dexterity ring.

The rule pinned here:
  1. An item from the item data files that does not ship its own picture may only
     borrow one named in DELIBERATE_SHARED, and must resolve to exactly that one.
  2. No borrowed picture, and no entry of the renderer's family maps, may carry a
     word whose opposite is in the item's own name or effect (OPPOSITES).

Corpses, cooking ingredients and template x material weapons and armour are
outside this rule: their sharing is by design (one corpse picture, tinted
templates) and they are covered by test_art_pass.
"""
import glob
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import renderer  # noqa: E402

ITEMS = os.path.join(ROOT, 'data', 'items')
SKIP_FILES = {'accessory_appearances', 'cook_outcomes', 'recipes', 'ingredient', 'prime_cuts'}

# Pictures shared on purpose: the borrowed picture shows the same thing.
# {item id: picture it shows}. Keep this list short and explain each entry.
DELIBERATE_SHARED = {
    # none: every wand, scroll, spellbook, ring and amulet now ships its own picture (2026-10-17)
}

# Word pairs that must never meet: an item whose name or effect carries one side
# may not show a picture whose name carries the other.
OPPOSITES = [
    ('weaken', 'empower'), ('weaken', 'strength'), ('curse', 'bless'), ('uncurse', 'curse'),
    ('slow', 'haste'), ('slow', 'speed'), ('sleep', 'wake'), ('fire', 'frost'), ('fire', 'cold'),
    ('fire', 'ice'), ('heal', 'drain'), ('heal', 'death'), ('heal', 'disease'), ('light', 'dark'),
    ('light', 'blind'), ('protection', 'annihilat'), ('recall', 'teleport_monster'),
    ('identify', 'confus'), ('charm', 'fear'), ('life', 'death'),
]


def _item_ids():
    ids = {}
    for path in glob.glob(os.path.join(ITEMS, '*.json')):
        name = os.path.basename(path)[:-5]
        if name in SKIP_FILES:
            continue
        with open(path, encoding='utf-8') as f:
            for k, v in json.load(f).items():
                if isinstance(v, dict):
                    ids[k] = v
    return ids


def _words(item_id, data):
    eff = data.get('effect') or data.get('spell_id') or ''
    return f'{item_id} {eff}'.lower()


def _clash(own, picture):
    """The opposite pair this picture name contradicts, or None."""
    for a, b in OPPOSITES:
        for mine, theirs in ((a, b), (b, a)):
            if mine in own and theirs in picture and theirs not in own:
                return (mine, theirs)
    return None


def _borrowers():
    out = {}
    for iid, data in _item_ids().items():
        p = renderer._resolve_item_sprite_path(iid)
        if p and os.path.basename(p) != f'{iid}.png':
            out[iid] = os.path.basename(p)[:-4]
    return out


def test_every_borrowed_picture_is_a_listed_deliberate_share():
    borrowers = _borrowers()
    unlisted = {k: v for k, v in borrowers.items() if k not in DELIBERATE_SHARED}
    assert not unlisted, f'{len(unlisted)} items show another item\'s picture: {sorted(unlisted.items())[:12]}'
    wrong = {k: (borrowers.get(k), v) for k, v in DELIBERATE_SHARED.items() if borrowers.get(k) != v}
    assert not wrong, f'allow-list entries that no longer resolve as listed (remove or fix): {sorted(wrong.items())[:12]}'


def test_no_item_shows_a_picture_with_the_opposite_meaning():
    ids = _item_ids()
    bad = []
    for iid, pic in _borrowers().items():
        c = _clash(_words(iid, ids[iid]), pic)
        if c:
            bad.append((iid, pic, c))
    assert not bad, bad


def test_family_maps_never_pair_an_effect_with_its_opposite():
    """The weaken_monster effect once mapped to wand_of_empowerment; every future
    wand, scroll or spellbook of an effect would inherit the clash."""
    bad = []
    for table in (renderer._WAND_EFFECT_SPRITE, renderer._SCROLL_EFFECT_SPRITE,
                  renderer._SPELLBOOK_FAMILY_SPRITE, renderer._UNIQUE_SPRITE_FALLBACK):
        for key, pic in table.items():
            c = _clash(key.lower(), pic.lower())
            if c:
                bad.append((key, pic, c))
    assert not bad, bad


def test_family_maps_point_at_pictures_that_exist():
    missing = []
    for table in (renderer._WAND_EFFECT_SPRITE, renderer._SCROLL_EFFECT_SPRITE,
                  renderer._SPELLBOOK_FAMILY_SPRITE, renderer._UNIQUE_SPRITE_FALLBACK):
        for key, pic in table.items():
            if not os.path.exists(os.path.join(renderer._ITEM_SPRITE_DIR, pic + '.png')):
                missing.append((key, pic))
    assert not missing, missing


def test_weaken_wand_shows_its_own_picture_not_empowerment():
    p = renderer._resolve_item_sprite_path('wand_of_weaken_monster')
    assert p and os.path.basename(p) == 'wand_of_weaken_monster.png', p


def test_no_two_magic_items_ship_the_same_picture():
    """A copied file is borrowing too: no two wands, scrolls, spellbooks, rings or
    amulets may ship byte-identical pictures (amulet_of_intellect once showed the
    Archmage's own amulet)."""
    import hashlib
    seen, dup = {}, []
    for name in ('wand', 'scroll', 'spellbook', 'accessory'):
        with open(os.path.join(ITEMS, f'{name}.json'), encoding='utf-8') as f:
            ids = [k for k, v in json.load(f).items() if isinstance(v, dict)]
        for iid in ids:
            p = os.path.join(renderer._ITEM_SPRITE_DIR, f'{iid}.png')
            if not os.path.exists(p):
                continue
            h = hashlib.sha1(open(p, 'rb').read()).hexdigest()
            if h in seen and (seen[h], iid) not in DELIBERATE_SAME_FILE:
                dup.append((seen[h], iid))
            seen.setdefault(h, iid)
    assert not dup, dup


# Pairs of items that ship the same picture on purpose. Keep it short.
DELIBERATE_SAME_FILE = set()
