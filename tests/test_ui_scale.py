"""UI scale (_genart/ui/SCALE_PLAN.md): the factor, the layout it drives, and
a window resized at runtime.

The render-based checks (every modal centred at 1280x720 / 1920x1080 /
3440x1440, text never smaller than at 1280x720, the contrast and layout
gates at every size) live in tests/test_ui_gates.py, which already renders
every screen through the capture harness.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import pygame  # noqa: E402
import pytest  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

import fantasy_ui  # noqa: E402
import layout  # noqa: E402
import ui_scale  # noqa: E402
import ui_theme  # noqa: E402

pygame.init()
pytestmark = pytest.mark.usefixtures('ui_theme_isolated')


# =============================================================================
# The factor
# =============================================================================

@pytest.mark.parametrize('size, expected', [
    ((1280, 720), 1.0),
    ((1600, 900), 1.125),
    ((1920, 1080), 1.25),
    ((2560, 1440), 1.5),
    ((3440, 1440), 1.5),          # Brandon's monitor: height-bound, like 2560x1440
    ((1093, 614), 1.0),           # a small display at 125-150 % scaling
    ((800, 600), 1.0),
    ((3840, 2160), 2.0),
    ((7680, 4320), 2.0),          # the cap
    ((1280, 1440), 1.0),          # tall and narrow: the width decides
])
def test_scale_for_window(size, expected):
    assert ui_scale.scale_for(*size) == expected


def test_scale_grows_smoothly_and_never_shrinks():
    """Monotonic in both axes, in 1/16 steps, and never below 1.0."""
    prev = 0.0
    for w in range(1280, 3841, 40):
        h = round(w * 9 / 16)
        s = ui_scale.scale_for(w, h)
        assert s >= prev and s >= 1.0
        assert s * 16 == int(s * 16)
        assert s - prev <= 1 / 16 + 1e-9 or prev == 0.0
        prev = s


def test_px_is_the_identity_at_scale_one():
    layout.update(1280, 720)
    assert ui_scale.get() == 1.0
    for n in (0, 1, 2, 7, 18, 48, 1060, 1440):
        assert ui_scale.px(n) == n
        assert ui_scale.font_px(n or 1) == (n or 1)
    assert ui_scale.px(-12) == -12


def test_layout_update_drives_the_rails_and_log():
    layout.update(1280, 720)
    assert (layout.LEFT_SIDEBAR_W, layout.SIDEBAR_W, layout.MSG_H) == (248, 330, 200)
    assert layout.GAME_W == 1280 - 330 and layout.MAP_X == 248
    layout.update(3440, 1440)
    assert layout.UI_SCALE == 1.5
    assert (layout.LEFT_SIDEBAR_W, layout.SIDEBAR_W, layout.MSG_H) == (372, 495, 300)
    assert layout.RIGHT_X == 3440 - 495 and layout.GAME_H == 1440 - 300
    # The map tiles do not scale: the viewport is simply what is left.
    from renderer import TILE_SIZE
    assert layout.VIEWPORT_W == layout.MAP_W // TILE_SIZE


def test_get_font_applies_the_scale_by_role():
    layout.update(1280, 720)
    small = fantasy_ui.get_font('body', 20).get_height()
    layout.update(3440, 1440)
    big = fantasy_ui.get_font('body', 20).get_height()
    assert big > small
    assert big == fantasy_ui._make_font('body', 30, False).get_height()
    # unscaled=True is a fixed pixel size at any scale
    assert (fantasy_ui.get_font('body', 20, unscaled=True).get_height()
            == fantasy_ui._make_font('body', 20, False).get_height())


# =============================================================================
# Runtime resize
# =============================================================================

@pytest.fixture
def game_at_1280():
    screen = pygame.display.set_mode((1280, 720))
    layout.update(1280, 720)
    from main import Game
    g = Game(screen, player_name='ScaleTest')
    g.on_resize(1280, 720)
    return g


def _resize(g, w, h):
    """The real path: the window changes, SDL sends WINDOWRESIZED, the game
    handles it."""
    pygame.display.set_mode((w, h))
    g.handle_event(pygame.event.Event(pygame.WINDOWRESIZED, x=w, y=h))


def _no_stale_fonts():
    for (role, size, bold), font in fantasy_ui._font_cache.items():
        want = fantasy_ui._make_font(role, ui_scale.font_px(size), bold).get_height()
        assert font.get_height() == want, ((role, size, bold), font.get_height(), want)


def test_resize_rescales_everything_and_leaves_nothing_stale(game_at_1280):
    g = game_at_1280
    g.render()
    h_sm, h_lg = g.font_sm.get_height(), g.font_lg.get_height()
    log_h = g.msg_log.line_height()
    g._menu_sprite_cache[('some_item', 32)] = None

    _resize(g, 3440, 1440)
    assert ui_scale.get() == 1.5 and layout.WINDOW_W == 3440
    assert g.sidebar.right_x == layout.RIGHT_X == 3440 - 495
    assert g.font_sm.get_height() > h_sm and g.font_lg.get_height() > h_lg
    assert g.msg_log.line_height() > log_h
    assert ('some_item', 32) not in g._menu_sprite_cache      # icons of the old size dropped
    assert g.MENU_ICON_SIZE == 48
    _no_stale_fonts()
    g.render()                                                 # draws at the new size
    assert g.msg_log._wrap_key[0] is fantasy_ui.get_font('body', 20)

    _resize(g, 1280, 720)                                      # and back
    assert ui_scale.get() == 1.0
    assert (g.font_sm.get_height(), g.font_lg.get_height()) == (h_sm, h_lg)
    assert g.msg_log.line_height() == log_h
    _no_stale_fonts()


def test_window_size_changed_event_is_handled_too(game_at_1280):
    g = game_at_1280
    pygame.display.set_mode((1920, 1080))
    g.handle_event(pygame.event.Event(pygame.WINDOWSIZECHANGED, x=1920, y=1080))
    assert layout.WINDOW_W == 1920 and ui_scale.get() == 1.25


def test_fonts_are_rebuilt_during_the_resize_not_on_a_draw(game_at_1280, monkeypatch):
    """Every font the game has used is made at the new size inside the
    resize, so the first frame afterwards (maybe a timed quiz) creates none."""
    g = game_at_1280
    g.render()
    _resize(g, 3440, 1440)

    def boom(*_a, **_k):
        raise AssertionError("a font was created on a draw after the resize")
    monkeypatch.setattr(fantasy_ui, '_make_font', boom)
    g.render()
    for key in list(fantasy_ui._font_cache):
        fantasy_ui.get_font(*key)


def test_resize_never_costs_quiz_seconds(game_at_1280, monkeypatch):
    """A resize (a blocked window drag, a font rebuild) is a long frame; the
    quiz clock is given at most one nominal frame for the next two updates."""
    from game_states import STATE_QUIZ
    g = game_at_1280
    seen = []
    monkeypatch.setattr(g.quiz_engine, 'update', lambda dt: seen.append(dt))
    g._necro_qs = None
    g.state = STATE_QUIZ
    _resize(g, 3440, 1440)
    for dt in (4.0, 2.5, 0.5):
        g.state = STATE_QUIZ
        g.update(dt)
    assert seen[0] <= 1.0 / layout.FPS + 1e-9
    assert seen[1] <= 1.0 / layout.FPS + 1e-9
    assert seen[2] == 0.5                       # the grace ends; normal time again


def test_art_kit_follows_the_scale_from_memory(tmp_path):
    """A kit authored at 2x is re-cut for a new UI scale from the images it
    loaded at startup: no disk access at the resize (the files are deleted
    first to prove it), never on a draw."""
    pygame.display.set_mode((1280, 720))
    layout.update(1280, 720)
    img = pygame.Surface((32, 32), pygame.SRCALPHA)
    img.fill((200, 160, 40, 255))
    pygame.image.save(img, str(tmp_path / 'panel.png'))
    (tmp_path / 'manifest.json').write_text(json.dumps(
        {'version': 1, 'scale': 2, 'pieces': {'panel': {'file': 'panel.png',
                                                        'slice': [8, 8, 8, 8]}}}))
    ui_theme.load(str(tmp_path))
    assert ui_theme.kit().pieces['panel'].l == 4            # 8 art px at 2x -> 4 at scale 1
    for f in tmp_path.iterdir():
        f.unlink()
    layout.update(3440, 1440)
    assert ui_theme.kit().pieces['panel'].l == 6            # 8 / 2 * 1.5
    assert not ui_theme.kit().errors
    layout.update(1280, 720)
    assert ui_theme.kit().pieces['panel'].l == 4


def test_a_kit_loaded_at_an_explicit_scale_stays_there(tmp_path):
    pygame.display.set_mode((1280, 720))
    layout.update(1280, 720)
    img = pygame.Surface((32, 32), pygame.SRCALPHA)
    img.fill((200, 160, 40, 255))
    pygame.image.save(img, str(tmp_path / 'panel.png'))
    (tmp_path / 'manifest.json').write_text(json.dumps(
        {'version': 1, 'scale': 2, 'pieces': {'panel': {'file': 'panel.png',
                                                        'slice': [8, 8, 8, 8]}}}))
    ui_theme.load(str(tmp_path), ui_scale=1.0)
    layout.update(3440, 1440)
    assert ui_theme.kit().pieces['panel'].l == 4
