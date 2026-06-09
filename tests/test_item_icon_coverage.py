"""EVERY spawnable item must resolve to a real sprite icon -- never a glyph
(2026-06-07, comprehensive audit).

The renderer draws item.id; ids with no `<id>.png` fell back to an ASCII glyph.
This swept the entire spawnable space and found the gaps:
  * 550+ cooking ingredients (prime cuts/parts/trophies/foraged) -> '~'/'*'
  * a few art-less uniques (hand_of_glory, duck_of_doom, aladdins_lamp,
    pandoras_box, wand_of_wonder_legendary)
renderer._resolve_item_sprite_path now covers them (ingredient meat-cut icon +
explicit unique stand-ins). This test re-runs the WHOLE sweep so a new
material/template/unique/ingredient that ships without art fails CI.
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from items import load_templates, load_materials  # noqa: E402
from renderer import _resolve_item_sprite_path  # noqa: E402

# prime_cuts.json keys 'meta'/'primes' are structure, not item ids; the real
# prime ids live in ingredient.json (and are covered there). DISABLED items are
# orphaned (never spawn) so they need no icon -- and code must not reference
# them (test_quest_item_lifecycle), so they CAN'T get a fallback either.
_DISABLED = {'pandoras_box', 'aladdins_lamp', 'wand_of_wonder_legendary'}
_NON_ITEM_KEYS = {'meta', 'primes'} | _DISABLED


def _resolves(item_id: str) -> bool:
    p = _resolve_item_sprite_path(item_id)
    return bool(p and os.path.exists(p))


def _composite_ids():
    out = []
    pools = {'weapons': load_materials('weapons'), 'armor': load_materials('armor')}
    for cat, mat_key in (('weapons', 'weapons'), ('armor', 'armor'), ('shields', 'armor')):
        tpls = load_templates(cat)
        mats = dict(pools[mat_key])
        if cat == 'shields':
            mats.update(pools['weapons'])
        for tid, tpl in tpls.items():
            compat = set(tpl.get('compatible_material_classes') or [])
            for mid, mat in mats.items():
                mcls = mat.get('material_class') or mat.get('class')
                if compat and mcls and mcls not in compat:
                    continue
                out.append(f"{mid}_{tid}")
    return out


def _json_item_ids():
    out = []
    for fn in ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll',
               'spellbook', 'potion', 'ammo', 'lockpick', 'container',
               'artifact', 'food', 'ingredient'):
        p = ROOT / 'data' / 'items' / f'{fn}.json'
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding='utf-8'))
        ids = d.keys() if isinstance(d, dict) else [x.get('id', '') for x in d]
        out += [i for i in ids if i and i not in _NON_ITEM_KEYS]
    return out


def test_every_composite_item_has_an_icon():
    missing = [i for i in _composite_ids() if not _resolves(i)]
    assert not missing, f"{len(missing)} composite items glyph-render: {missing[:20]}"


def test_every_json_item_has_an_icon():
    missing = [i for i in _json_item_ids() if not _resolves(i)]
    assert not missing, f"{len(missing)} catalogued items glyph-render: {missing[:20]}"


def test_all_ingredients_have_an_icon():
    d = json.loads((ROOT / 'data' / 'items' / 'ingredient.json').read_text(encoding='utf-8'))
    missing = [i for i in d if not _resolves(i)]
    assert not missing, f"{len(missing)} ingredients glyph-render: {missing[:20]}"


def test_active_artless_uniques_resolve():
    # the two ACTIVE art-less uniques get an icon; the three disabled ones are
    # orphaned and intentionally have no fallback (see _DISABLED).
    for uid in ('hand_of_glory', 'duck_of_doom'):
        assert _resolves(uid), f"{uid} still has no icon"


def test_menu_icon_path_uses_the_central_resolver():
    """The MENU sprite path (_get_menu_sprite) must resolve the SAME items as
    the map path. They diverged: the menu path matched only '<id>.png' + corpse,
    so a willow longbow / prime cut / collapsed ring showed a glyph in the
    inventory/equip/cook menus while the floor showed the icon -- the real root
    cause behind "still no icon". One representative per fallback branch.
    """
    import pygame
    pygame.init()
    try:
        pygame.display.set_mode((64, 64))
    except Exception:
        pass
    from main import Game

    class _Stub:
        pass
    g = _Stub()
    g.MENU_ICON_SIZE = 32
    g._menu_sprite_cache = {}
    samples = [
        'willow_longbow',        # composite weapon, no per-id art -> base fallback
        'giant_rat_prime',       # ingredient (prime cut) -> meat-cut fallback
        'medusa_gorgon_trophy',  # ingredient (trophy)
        'ring_of_searching',     # collapsed ring -> effect-art fallback
        'amulet_of_searching',   # collapsed amulet
        'hand_of_glory',         # art-less active unique
        'iron_dagger',           # plain exact-match (control)
    ]
    glyphed = [s for s in samples if Game._get_menu_sprite(g, s) is None]
    assert not glyphed, f"menu path returns a glyph (None) for: {glyphed}"
