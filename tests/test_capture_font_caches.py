"""The capture tool records text whatever ran before it (3.5.0's failed CI).

fantasy_ui keeps three font caches: the logical one, the fixed-pixel one,
and `_fonts_by_px`, which a UI-scale change refills the logical one from.
The capture harness (tools/ui/capture.py) emptied only the logical one. A
test earlier in the same process that resized the window to a smaller scale
(test_hint_pool, test_cook_menu) left plain Fonts in `_fonts_by_px`, so at
that scale the harness drew with fonts it does not trace and recorded no
text: the Journal at 1093x614 came back empty and
test_journal.py::test_timeline_scrolled_to_the_end_shows_the_farm failed in
CI's single-process run while passing alone and under xdist.

This test does exactly what those tests did, then captures the Journal.
"""
import importlib.util
import os
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

import pygame  # noqa: E402


def _capture():
    if 'pq_ui_capture' in sys.modules:
        return sys.modules['pq_ui_capture']
    spec = importlib.util.spec_from_file_location('pq_ui_capture',
                                                  ROOT / 'tools' / 'ui' / 'capture.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['pq_ui_capture'] = mod
    spec.loader.exec_module(mod)
    return mod


def test_a_resize_before_the_capture_never_hides_its_text():
    import fantasy_ui
    import layout
    pygame.init()
    snap = layout.snapshot()
    try:
        # What an earlier test does: resize across a scale step and draw, so
        # the by-pixel cache holds plain fonts at the small scale.
        # (A font in the cache when the scale changes is what the rescale
        # listener rebuilds into _fonts_by_px, as plain fonts.)
        pygame.display.set_mode((1280, 720))
        layout.update(1280, 720)
        for role, size, bold in (('body', 17, False), ('heading', 18, True), ('italic', 18, False),
                                 ('body', 16, False), ('body', 17, True)):
            fantasy_ui.get_font(role, size, bold)
        pygame.display.set_mode((1093, 614))
        layout.update(1093, 614)
        pygame.display.set_mode((1280, 720))
        layout.update(1280, 720)
        assert any(type(f).__name__ == 'Font' for f in fantasy_ui._fonts_by_px.values())
    finally:
        layout.restore(snap)
    cap = _capture()
    sc = next(s for s in cap.SCENES if s.name == 'menu_journal_timeline')
    counts = {}
    with cap.harness():
        for size in ((1280, 720), (1093, 614)):
            surf, _state = cap.render_scene(sc, size)
            counts[size] = len(surf.text_blits)
    assert counts[(1093, 614)] > 50, counts                  # the page's text, recorded
    assert abs(counts[(1093, 614)] - counts[(1280, 720)]) < 20, counts
