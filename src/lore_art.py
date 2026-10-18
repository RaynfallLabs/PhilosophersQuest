"""lore_art.py -- the subject's picture on the lore pages.

The item / bestiary dossier and the encyclopedia article show the art of the
thing they describe: the item's own sprite (through the map's central
resolver, ``renderer._resolve_item_sprite_path``, so material art, uniques
and every fallback apply) or the LIVING creature's sprite
(``assets/tiles/monsters/<id>.png``),
never the corpse. An item looks the same identified or not: the art is keyed
on the item's real id, never on its unidentified appearance.

A picture is a "plate": the sprite enlarged by a WHOLE number (3x at UI scale
1, growing with the scale, capped by the room the page has) so every source
pixel stays a crisp square, composed once onto its backdrop -- the dungeon
floor tile, darkened, behind a creature (where the player meets it); the
kit's flat dark well behind an item. Plates are cached per (kind, id, size):
nothing is loaded or scaled on a frame after the first one at that size.
A subject with no art resolves to None, and the page simply has no picture
(never a letter glyph).
"""
from __future__ import annotations

import os
from collections import OrderedDict

import pygame

import renderer
import ui_scale

# Item-art categories of the encyclopedia (the Journal, Lore Hints and Recipes
# have no subject art).
ITEM_CATEGORIES = ('weapon', 'armor', 'accessory', 'scroll', 'wand', 'spellbook', 'treasure')
# Item-art categories drawn from several item files (Wonders: the Soul Spheres
# from artifact.json and the Draught of Mimir's Well from potion.json).
MIXED_ITEM_CATEGORIES = ('wonders',)
BASE_MULT = 3                   # 64 px art -> 192 px at UI scale 1
FLOOR_DIM = (140, 140, 150)     # the floor behind a creature, multiplied down: calm

# Both caches are bounded (least recently used goes first): every window
# size made new plates and every subject kept its full-size source, so a long
# session grew them by 80-230 MiB.
RAW_MAX = 8                     # source images kept (the floor tile among them)
PLATES_MAX = 48                 # finished plates kept
_raw: OrderedDict = OrderedDict()       # path -> Surface | None (the source file)
_plates: OrderedDict = OrderedDict()    # (kind, id, max_px) -> Surface | None


def _remember(cache: OrderedDict, key, value, cap: int):
    cache[key] = value
    cache.move_to_end(key)
    while len(cache) > cap:
        cache.popitem(last=False)
    return value


def subject_ref(subject):
    """(kind, id) of the art for a dossier subject, or None. A corpse shows
    the creature it was; any other item shows itself."""
    if subject is None:
        return None
    from items import Corpse
    if isinstance(subject, Corpse):
        mid = getattr(subject, 'monster_id', '') or ''
        return ('monster', mid) if mid else None
    iid = getattr(subject, 'id', '') or ''
    return ('item', iid) if iid else None


def encyclopedia_ref(category, entry):
    """(kind, id) of the art for an encyclopedia entry, or None."""
    if not entry:
        return None
    eid = entry.get('_id') or entry.get('id') or ''
    if not eid:
        return None
    if category == 'bestiary':
        return ('monster', eid)
    if category in ITEM_CATEGORIES or category in MIXED_ITEM_CATEGORIES:
        return ('item', eid)
    return None


def art_path(kind, sid):
    """The sprite file for (kind, id), or None when it has no art."""
    if not sid:
        return None
    if kind == 'item':
        return renderer._resolve_item_sprite_path(sid)
    if kind == 'monster':
        path = os.path.join(renderer._SPRITE_DIR, f"{sid}.png")
        if os.path.exists(path):
            return path
    return None


def _load(path):
    if path in _raw:
        _raw.move_to_end(path)
        return _raw[path]
    try:
        surf = pygame.image.load(path).convert_alpha() if path else None
    except (pygame.error, FileNotFoundError, OSError):
        surf = None
    return _remember(_raw, path, surf, RAW_MAX)


def plate_px(src_w, src_h, max_px, scale=None):
    """(w, h) of the plate for a ``src_w`` x ``src_h`` source that must fit in
    ``max_px``. Pixel art: a whole multiple of the source (``BASE_MULT`` at
    UI scale 1, rounded to the nearest whole step as the scale grows, at
    least 1x), as large as fits. A painting: fitted to the same box as 64 px
    art would be, aspect kept."""
    s = ui_scale.get() if scale is None else scale
    big = max(src_w, src_h)
    if big <= renderer.PIXEL_ART_MAX:
        mult = max(1, int(BASE_MULT * s + 0.5))
        mult = min(mult, max(1, max_px // big))
        return src_w * mult, src_h * mult
    box = min(max_px, int(renderer.PIXEL_ART_MAX * BASE_MULT * s + 0.5))
    k = box / big
    return max(1, int(src_w * k)), max(1, int(src_h * k))


def _backdrop(kind, w, h):
    from fantasy_ui import KT
    surf = pygame.Surface((w, h)).convert()
    surf.fill(KT.WELL)
    if kind == 'monster':
        floor = _load(os.path.join(renderer._ENV_SPRITE_DIR, 'floor.png'))
        if floor is not None:
            fw, fh = floor.get_size()
            # The floor at the creature's own enlargement, tiled to the plate.
            k = max(1, round(w / max(1, renderer.PIXEL_ART_MAX)))
            tile = renderer.fit_sprite(floor, fw * k, fh * k)
            for ty in range(0, h, tile.get_height()):
                for tx in range(0, w, tile.get_width()):
                    surf.blit(tile, (tx, ty))
            surf.fill(FLOOR_DIM, special_flags=pygame.BLEND_RGB_MULT)
    return surf


def plate(kind, sid, max_px):
    """The cached picture of (kind, id) no larger than ``max_px`` square, on
    its backdrop; None when it has no art (or ``max_px`` is too small)."""
    key = (kind, sid, int(max_px))
    if key in _plates:
        _plates.move_to_end(key)
        return _plates[key]
    out = None
    raw = _load(art_path(kind, sid)) if max_px >= 16 else None
    if raw is not None:
        w, h = plate_px(*raw.get_size(), int(max_px))
        sprite = renderer.fit_sprite(raw, w, h)
        out = _backdrop(kind, w, h)
        out.blit(sprite, (0, 0))
    return _remember(_plates, key, out, PLATES_MAX)


def cached(kind, sid):
    """Every plate built for (kind, id) (for tests: was this art drawn?)."""
    return [s for (k, i, _px), s in _plates.items() if k == kind and i == sid and s is not None]


def clear_cache():
    _raw.clear()
    _plates.clear()
