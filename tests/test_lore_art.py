"""The subject's art on the lore pages (2026-10-16).

Brandon: "we have all this beautiful art, but when you actually go to the
lore page, it gives great text about items and monsters, but no image!"

The item / bestiary dossier (Identity pane) and the encyclopedia article
now head their text with the subject's picture (src/lore_art.py): the
item's own sprite through the central item resolver (identified or not:
the art is the item), or the LIVING creature a corpse was, on the dungeon
floor tile. Pixel art is enlarged by a whole number (3x at UI scale 1) so it
stays crisp. A subject with no art has no picture well at all, never a
glyph.
"""
import json
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import importlib.util  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import lore_art  # noqa: E402

pytestmark = pytest.mark.usefixtures('ui_theme_isolated')


def _load_capture():
    if 'pq_ui_capture' in sys.modules:
        return sys.modules['pq_ui_capture']
    spec = importlib.util.spec_from_file_location(
        'pq_ui_capture', _ROOT / 'tools' / 'ui' / 'capture.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['pq_ui_capture'] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _fresh_cache():
    lore_art.clear_cache()
    yield
    lore_art.clear_cache()


# -- pure resolution ---------------------------------------------------------

def test_a_corpse_shows_its_creature_and_an_item_shows_itself():
    from items import Corpse, load_items
    corpse = Corpse('giant rat', 'giant_rat', 0, 0)
    assert lore_art.subject_ref(corpse) == ('monster', 'giant_rat')
    potion = load_items('potion')[0]
    assert lore_art.subject_ref(potion) == ('item', potion.id)
    assert lore_art.subject_ref(None) is None


def test_encyclopedia_categories_map_to_their_art():
    assert lore_art.encyclopedia_ref('bestiary', {'_id': 'goblin'}) == ('monster', 'goblin')
    for cat in ('weapon', 'armor', 'accessory', 'scroll', 'wand', 'spellbook'):
        assert lore_art.encyclopedia_ref(cat, {'_id': 'x_id'}) == ('item', 'x_id')
    assert lore_art.encyclopedia_ref('scroll', {'id': 'scroll_of_light'}) == ('item', 'scroll_of_light')
    # No subject art: the chronicle, recalled hints and recipes.
    for cat in ('chronicle', 'lore_hints', 'recipes'):
        assert lore_art.encyclopedia_ref(cat, {'name': 'Something', 'lore': ''}) is None
    assert lore_art.encyclopedia_ref('bestiary', None) is None


def test_plate_is_a_whole_multiple_of_pixel_art():
    assert lore_art.plate_px(64, 64, 500, scale=1.0) == (192, 192)      # 3x
    assert lore_art.plate_px(64, 64, 500, scale=1.25) == (256, 256)     # 4x
    assert lore_art.plate_px(64, 64, 500, scale=1.5) == (320, 320)      # 5x
    assert lore_art.plate_px(64, 64, 150, scale=1.0) == (128, 128)      # the room caps it
    assert lore_art.plate_px(64, 64, 40, scale=1.0) == (64, 64)         # never below 1x
    # A painting is fitted, aspect kept, to the box 64 px art would take.
    assert lore_art.plate_px(512, 256, 500, scale=1.0) == (192, 96)


def test_every_monster_and_encyclopedia_item_has_art():
    data = _ROOT / 'data'
    monsters = json.loads((data / 'monsters.json').read_text(encoding='utf-8'))
    missing = [k for k, v in monsters.items()
               if isinstance(v, dict) and not lore_art.art_path('monster', k)]
    assert not missing, missing[:20]
    for cat in lore_art.ITEM_CATEGORIES:
        items = json.loads((data / 'items' / f'{cat}.json').read_text(encoding='utf-8'))
        ids = list(items) if isinstance(items, dict) else [e.get('id') for e in items]
        missing = [i for i in ids if not lore_art.art_path('item', i)]
        assert not missing, (cat, missing[:20])


def test_monster_art_is_the_living_creature_not_a_corpse():
    path = lore_art.art_path('monster', 'giant_rat')
    assert path and os.path.basename(path) == 'giant_rat.png'
    assert 'monsters' in path.replace('\\', '/')


# -- the pages draw the art ----------------------------------------------------

def _render(scene_name, size=(1280, 720), before=None):
    """Draw one capture scene; returns (game, screen, [(plate, body)] drawn)."""
    cap = _load_capture()
    import game_render
    drawn = []
    real = game_render.RenderMixin._draw_lore_plate

    def spy(self, surf, body, scroll, n, line_h):
        drawn.append((surf, pygame.Rect(body), scroll))
        return real(self, surf, body, scroll, n, line_h)

    sc = next(s for s in cap.SCENES if s.name == scene_name)
    with cap.harness():
        game_render.RenderMixin._draw_lore_plate = spy
        try:
            screen = cap.make_screen(size)
            cap.reset_sandbox()
            cap.reseed()
            cap.GLYPH_ICONS.clear()
            g = cap.build_game(screen, size)
            sc.setup(g)
            if before:
                before(g)
            screen.reset_trace()
            g.render()
            glyphs = list(cap.GLYPH_ICONS)
        finally:
            game_render.RenderMixin._draw_lore_plate = real
    return g, screen, drawn, glyphs


def _assert_plate_on_screen(screen, drawn, kind, sid):
    plates = [d for d in drawn if d[0] is not None]
    assert plates, "no picture drawn"
    surf, body, _scroll = plates[0]
    assert any(surf is p for p in lore_art.cached(kind, sid)), (kind, sid)
    # The plate's own pixels are on the screen, centred in the pane's text lane.
    w, h = surf.get_size()
    x = body.x + (body.w - _S(12)) // 2 - w // 2
    y = body.y + _S(lore_art_pad())
    for px, py in ((w // 2, h // 2), (w // 4, h // 2), (w // 2, h - 3)):
        assert screen.get_at((x + px, y + py))[:3] == surf.get_at((px, py))[:3]
    # A crisp whole multiple of the 64 px source.
    assert w % 64 == 0 and h % 64 == 0 and w >= 192


def _S(n):
    from ui_scale import px
    return px(n)


def lore_art_pad():
    import game_render
    return game_render.RenderMixin._LORE_PLATE_PAD


@pytest.mark.parametrize('scene', ['lore_item', 'lore_item_tab2'])
def test_item_dossier_draws_the_item(scene):
    g, screen, drawn, glyphs = _render(scene)
    _assert_plate_on_screen(screen, drawn, 'item', g._lore_subject.id)
    assert not glyphs


def test_unidentified_item_dossier_draws_the_real_item_art():
    g, screen, drawn, glyphs = _render('lore_item_unidentified')
    subject = g._lore_subject
    assert not getattr(subject, 'identified', True)
    _assert_plate_on_screen(screen, drawn, 'item', subject.id)
    assert not glyphs


def test_corpse_dossier_draws_the_living_creature():
    g, screen, drawn, _ = _render('lore_corpse')
    assert g._lore_subject.monster_id == 'giant_rat'
    _assert_plate_on_screen(screen, drawn, 'monster', 'giant_rat')
    assert not lore_art.cached('item', 'corpse_giant_rat')


def test_encyclopedia_bestiary_article_draws_the_creature():
    g, screen, drawn, _ = _render('menu_encyclopedia_entry')
    assert g.encyclopedia_category == 'bestiary'
    _assert_plate_on_screen(screen, drawn, 'monster', g._encyclopedia_entry['_id'])


def test_encyclopedia_weapon_article_draws_the_weapon():
    g, screen, drawn, _ = _render('menu_encyclopedia_weapon')
    assert g.encyclopedia_category == 'weapon'
    _assert_plate_on_screen(screen, drawn, 'item', g._encyclopedia_entry['_id'])


def test_encyclopedia_chronicle_has_no_picture():
    def chronicle(g):
        g._encyclopedia_load_entries('chronicle')
        g.encyclopedia_category = 'chronicle'
        g.encyclopedia_entries = [{'name': 'Entered the dungeon.', 'lore': ''}]
        g._encyclopedia_entry = g.encyclopedia_entries[0]
    _g, _screen, drawn, _ = _render('menu_encyclopedia_entry', before=chronicle)
    assert all(d[0] is None for d in drawn)


@pytest.mark.parametrize('size', [(1280, 720), (3440, 1440)])
def test_scrolled_article_slides_the_picture_away_cleanly(size):
    # The article scrolls line by line; the picture moves up with its text,
    # clipped to the pane (and no gate trips on the half-hidden well).
    def scrolled(g):
        g._encyclopedia_article_scroll = 3
    _g, screen, drawn, _ = _render('menu_encyclopedia_weapon', size, before=scrolled)
    assert drawn and drawn[0][2] > 0
    assert not screen.text_outside_panels()
    assert not screen.text_outside()


# -- missing art falls back cleanly ----------------------------------------------

@pytest.mark.parametrize('scene', ['lore_item', 'lore_corpse', 'menu_encyclopedia_entry'])
def test_missing_sprite_drops_the_picture_well(monkeypatch, scene):
    monkeypatch.setattr(lore_art, 'art_path', lambda kind, sid: None)
    g, screen, drawn, glyphs = _render(scene)
    assert drawn and all(d[0] is None for d in drawn)
    assert not glyphs
    # No well: the pane's first text line sits at the top of its body.
    body = drawn[0][1]
    first = min((r for r, t in screen.text_blits
                 if body.contains(r) and t.strip()), key=lambda r: r.y)
    assert first.y - body.y < _S(10)
    # No glyph stand-in either: no lone symbol drawn in the pane.
    assert not [t for r, t in screen.text_blits
                if body.colliderect(r) and len(t.strip()) == 1]
    assert not screen.text_outside_panels()


def test_unloadable_sprite_file_is_no_picture(tmp_path, monkeypatch):
    bad = tmp_path / 'broken.png'
    bad.write_bytes(b'not a png')
    monkeypatch.setattr(lore_art, 'art_path', lambda kind, sid: str(bad))
    pygame.display.set_mode((64, 64))
    assert lore_art.plate('item', 'whatever', 300) is None
