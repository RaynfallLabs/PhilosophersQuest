"""The installed UI art kit (assets/ui, Midnight Codex, 2026-10-16).

* It loads with zero problems: every piece and icon in the manifest is
  accepted, and ``load()`` logs no warning.
* Every piece the manifest ships is actually drawn by some screen of the
  game (tools/ui/capture.py renders all of them), and so is every icon:
  the 12 subject icons (quiz headers, the welcome ring, study mode), the
  15 stat icons (the sidebar) and the status-effect icons (the sidebar's
  effect chips; every one names a real status effect).
"""
import json
import logging
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import importlib.util  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import pygame  # noqa: E402
import pytest  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

import ui_theme  # noqa: E402

pygame.init()
MANIFEST = _ROOT / 'assets' / 'ui' / 'manifest.json'

pytestmark = pytest.mark.usefixtures('ui_theme_isolated')


def _manifest():
    return json.loads(MANIFEST.read_text(encoding='utf-8'))


def _capture():
    if 'pq_ui_capture' in sys.modules:
        return sys.modules['pq_ui_capture']
    spec = importlib.util.spec_from_file_location(
        'pq_ui_capture', _ROOT / 'tools' / 'ui' / 'capture.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['pq_ui_capture'] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize('size', [(1280, 720), (3440, 1440)])
def test_installed_kit_loads_with_zero_warnings(size, caplog):
    import ui_scale
    pygame.display.set_mode(size)
    m = _manifest()
    try:
        ui_scale.set_for_window(*size)
        with caplog.at_level(logging.WARNING, logger='ui_theme'):
            k = ui_theme.load()
        assert k.errors == []
        assert not [r for r in caplog.records if r.name == 'ui_theme']
        assert set(k.pieces) == set(m['pieces'])
        assert set(k.icon_src) == set(m['icons']['files'])
        # The frame band the header plaque is inset by: 16 px at UI scale 1.
        assert ui_theme.band('panel') == ui_scale.px(16)
        assert ui_theme.band('quiz') == ui_scale.px(16)
        # Every manifest icon size is pre-scaled at load (no scaling on a draw).
        for name in m['icons']['files']:
            for sz in m['icons']['sizes']:
                assert (name, ui_scale.font_px(sz)) in k.icons, (name, sz)
    finally:
        ui_scale.set_scale(1.0)
        pygame.display.set_mode((64, 64))


def test_status_effect_icons_name_real_effects():
    from status_effects import EFFECT_INFO
    fx = [n for n in _manifest()['icons']['files'] if n.startswith('fx_')]
    assert fx
    assert [n for n in fx if n[3:] not in EFFECT_INFO] == []


def test_every_manifest_piece_and_icon_is_drawn_by_the_game(monkeypatch):
    cap = _capture()
    used_pieces, used_icons = set(), set()
    real_piece, real_icon = ui_theme.draw_piece, ui_theme.draw_icon

    def spy_piece(surf, name, rect, **kw):
        ok = real_piece(surf, name, rect, **kw)
        if ok:
            used_pieces.add(name)
        return ok

    def spy_icon(surf, name, rect):
        ok = real_icon(surf, name, rect)
        if ok:
            used_icons.add(name)
        return ok

    monkeypatch.setattr(ui_theme, 'draw_piece', spy_piece)
    monkeypatch.setattr(ui_theme, 'draw_icon', spy_icon)
    with cap.harness():
        assert ui_theme.kit().errors == []
        for sc in cap.SCENES:
            cap.render_scene(sc, (1280, 720))
        # The quiz card's "selected" state lasts only between the key press
        # and the result, so no still capture shows it: draw it through the
        # quiz's own card helper.
        import fantasy_ui
        f = fantasy_ui.get_font('body', 20)
        fantasy_ui.draw_choice_button(pygame.Surface((500, 100)), (0, 0, 400, 60),
                                      '2', ['An answer'], f, f, selected=True)
    m = _manifest()
    unused = sorted(set(m['pieces']) - used_pieces)
    assert not unused, f"manifest pieces no screen draws: {unused}"
    icons = set(m['icons']['files'])
    missing = sorted(n for n in icons - used_icons if not n.startswith('fx_'))
    assert not missing, f"subject / stat icons no screen draws: {missing}"
    # Effect icons appear for the effects the player has; the capture
    # scenes carry four. The rest are covered by the name test above and
    # by the chip test below.
    assert {n for n in used_icons if n.startswith('fx_')}


def test_every_effect_chip_draws_its_icon():
    """The sidebar's effect chip asks for ``fx_<effect id>``: with the kit
    each of the manifest's effect icons is drawn for its effect."""
    import ui
    pygame.display.set_mode((400, 300))
    ui_theme.load()
    drawn = []
    real = ui_theme.draw_icon
    try:
        ui_theme.draw_icon = lambda s, n, r: drawn.append(n) or real(s, n, r)
        sb = ui.Sidebar(pygame.Surface((400, 300)), 0)
        fx = [n for n in _manifest()['icons']['files'] if n.startswith('fx_')]
        for name in fx:
            sb._effect_chip(10, 10, 160, 'X', (200, 200, 200), name[3:])
        assert drawn == fx
    finally:
        ui_theme.draw_icon = real
        pygame.display.set_mode((64, 64))
