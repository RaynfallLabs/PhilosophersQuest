"""Key UI screens render through the headless capture tool (tools/ui/capture.py).

The capture tool is the measuring stick for the UI art pass: it draws every
screen with the game's real render code from a fresh, seeded game. This test
runs a handful of key screens at the default window size and checks that each
one draws without raising, is not a blank frame, and puts no text outside the
window. It also checks the tool is repeatable (same scene twice -> same pixels).

The full capture (every screen, three sizes, PNGs + contact sheets) takes about
a minute; it runs only when PQ_UI_CAPTURE_FULL=1 is set.
"""
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


def _load_capture():
    spec = importlib.util.spec_from_file_location(
        'pq_ui_capture', _ROOT / 'tools' / 'ui' / 'capture.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['pq_ui_capture'] = mod
    spec.loader.exec_module(mod)
    return mod


capture = _load_capture()

# Every test starts with an empty UI art kit and restores the previous one
# (the capture harness loads assets/ui/; GROUNDWORK_REVIEW 9).
pytestmark = pytest.mark.usefixtures('ui_theme_isolated')
KEY_SCENES = [s for s in capture.SCENES if s.key]


def test_key_scene_list_covers_the_main_kinds():
    groups = {s.group for s in KEY_SCENES}
    assert {'Title', 'Play', 'Menus', 'Quiz', 'Endings'} <= groups
    assert len(KEY_SCENES) >= 12
    names = [s.name for s in capture.SCENES]
    assert len(names) == len(set(names)), "duplicate screen names"


@pytest.fixture(scope='module')
def key_shots():
    return capture.capture(KEY_SCENES, [capture.default_size()],
                           save=False, verbose=False)


@pytest.mark.parametrize('name', [s.name for s in KEY_SCENES])
def test_key_screen_renders(key_shots, name):
    shot = next(s for s in key_shots if s.scene.name == name)
    assert shot.ok, f"{name} failed to render: {shot.error}"
    surf = shot.surface
    assert surf.get_size() == capture.default_size()
    assert not capture.is_blank(surf), f"{name} rendered a blank frame"
    assert not shot.outside, (
        f"{name}: text drawn outside the window: "
        + "; ".join(f"{t[:40]!r} at {tuple(r)}" for r, t in shot.outside[:5]))


def test_capture_is_repeatable():
    sc = next(s for s in capture.SCENES if s.name == 'quiz_chain_combat')
    size = capture.default_size()
    with capture.harness():
        a, _ = capture.render_scene(sc, size)
        a = pygame.image.tobytes(a, 'RGB')
        b, _ = capture.render_scene(sc, size)
        b = pygame.image.tobytes(b, 'RGB')
    assert a == b, "the same screen drawn twice came out different"


def test_text_tracing_sees_text():
    """Guard the guard: the out-of-window check only means something if the
    harness actually sees the game's text blits."""
    sc = next(s for s in capture.SCENES if s.name == 'play_main')
    with capture.harness():
        surf, _ = capture.render_scene(sc, capture.default_size())
    texts = [t for _r, t in surf.text_blits]
    assert len(texts) > 20
    assert any(capture.PLAYER_NAME in t for t in texts)


@pytest.mark.skipif(os.environ.get('PQ_UI_CAPTURE_FULL') != '1',
                    reason='full UI capture is slow; set PQ_UI_CAPTURE_FULL=1')
def test_full_capture_every_screen_every_size(tmp_path):
    shots = capture.capture(capture.SCENES, capture.all_sizes(), tmp_path,
                            verbose=False)
    bad = [f"{s.scene.name}@{capture.size_tag(s.size)}: {s.error}"
           for s in shots if not s.ok]
    assert not bad, "\n".join(bad)
