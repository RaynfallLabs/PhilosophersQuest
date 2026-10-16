"""UI art foundation (2026-10-15): the theme kit and the fixes laid under it.

  1. MessageLog wraps each entry once (cache per entry, keyed on font + width).
  2. Every full-window overlay goes through one cached helper.
  4. The parchment texture is loaded once and scaled once per size.
  5. Header strips no longer paint over their panel's border; panel bodies
     are opaque.
  6. ``ui_theme``: the optional art kit (assets/ui/). Nine-slice from
     pre-scaled tiled pieces, accent layer, startup-only loading, and the
     FALLBACK GATE: with no art the helpers draw exactly what the old
     procedural helpers drew (reference copies below).

(3, the quiz answer-card position, lives in test_ui_measured_rows.py.)
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import json  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import pygame  # noqa: E402
import pytest  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

pygame.init()
pygame.display.set_mode((64, 64))

import fantasy_ui  # noqa: E402
import ui_theme  # noqa: E402
from fantasy_ui import FP  # noqa: E402


@pytest.fixture(autouse=True)
def _no_art():
    """Every test starts (and ends) with an empty kit, at UI scale 1: the
    pixel references below are today's drawing at 1280x720 (the UI scale,
    _genart/ui/SCALE_PLAN.md, is tested in test_ui_scale.py). conftest puts
    the layout back afterwards."""
    import layout
    layout.update(1280, 720)
    ui_theme.unload()
    ui_theme.clear_overlay_cache()
    yield
    ui_theme.unload()
    ui_theme.clear_overlay_cache()


def _bytes(surf):
    return pygame.image.tobytes(surf, 'RGB')


def _canvas(w=400, h=300, color=(37, 81, 23)):
    s = pygame.Surface((w, h))
    s.fill(color)
    return s


LONG = ("You strike the cave troll with the Sword of Saint Michael for 23 damage; it "
        "reels back, howling, and the torchlight shudders across the wet stone of the "
        "Labyrinth of Echoes as its blood hisses on the floor.")


# =============================================================================
# 1. Message log
# =============================================================================

def _full_log(n=60):
    from ui import MessageLog
    log = MessageLog()
    kinds = ('info', 'success', 'warning', 'danger', 'loot')
    for i in range(n):
        log.add(f"{LONG} ({i})", kinds[i % 5])
    return log


def _count_wraps(monkeypatch, log):
    calls = []
    real = log._wrap

    def counting(text, font, w):
        calls.append(text)
        return real(text, font, w)
    monkeypatch.setattr(log, '_wrap', counting)
    return calls


def test_log_wraps_each_entry_once(monkeypatch):
    log = _full_log()
    calls = _count_wraps(monkeypatch, log)
    scr = pygame.Surface((1600, 300))
    log.draw(scr, 0, 0, 1342, 200)
    first = len(calls)
    assert 0 < first <= 10, "only the entries that reach the screen are wrapped"
    log.draw(scr, 0, 0, 1342, 200)
    log.draw(scr, 0, 0, 1342, 200)
    assert len(calls) == first, "a warm frame must not re-wrap anything"
    log.add("A new message.")
    log.draw(scr, 0, 0, 1342, 200)
    assert calls[first:] == ["A new message."], "add() wraps only the new entry"


def test_log_rewraps_on_width_or_font_change(monkeypatch):
    log = _full_log(5)
    calls = _count_wraps(monkeypatch, log)
    scr = pygame.Surface((1600, 300))
    log.draw(scr, 0, 0, 1342, 400)
    n = len(calls)
    assert log._wrap_key[1] == 1342 - log.PAD_X * 2
    log.draw(scr, 0, 0, 700, 400)                      # window resized
    assert len(calls) > n and log._wrap_key[1] == 700 - log.PAD_X * 2
    assert all(w is None or all(log._font.size(t)[0] <= 684 for t in w[1])
               for w in log._wrapped)
    n = len(calls)
    log._font = fantasy_ui.get_font('body', 26)        # font swapped
    log.draw(scr, 0, 0, 700, 400)
    assert len(calls) > n and log._wrap_key[0] is log._font


def _reference_log_draw(log, screen, x, y, w, h):
    """The pre-cache MessageLog.draw (re-wraps everything), for comparison."""
    from ui import _MSG_COLORS
    pygame.draw.rect(screen, FP.MIDNIGHT, (x, y, w, h))
    pygame.draw.line(screen, FP.GOLD_DARK, (x, y), (x + w, y), 1)
    line_h = log.line_height()
    available_h = h - log.PAD_Y * 2
    if line_h <= 0 or available_h < line_h:
        return
    max_lines = available_h // line_h
    text_w = w - log.PAD_X * 2
    all_lines = []
    for text, msg_type in log.entries:
        for wl in log._wrap(text, log._font, text_w):
            all_lines.append((wl, msg_type))
    visible = all_lines[-max_lines:]
    for i, (text, msg_type) in enumerate(visible):
        age = len(visible) - 1 - i
        base = _MSG_COLORS.get(msg_type, _MSG_COLORS['info'])
        fade = max(0.35, 1.0 - age * 0.09)
        color = tuple(int(c * fade) for c in base)
        screen.blit(log._font.render(text, True, color),
                    (x + log.PAD_X, y + log.PAD_Y + i * line_h))


def test_log_cache_follows_a_replaced_or_edited_entries_list():
    """GROUNDWORK_REVIEW 7: the cache was invalidated only when the entry
    COUNT changed, so a same-length replacement (a restored log) or an entry
    edited in place ("message repeated x2") drew the old text."""
    log = _full_log()                                  # 60 entries: at the cap
    w, h = 1342, 200
    a = pygame.Surface((w + 20, h + 20))
    log.draw(a, 10, 10, w, h)                          # cache warm
    log.entries = [(f"Restored line {i}.", 'info') for i in range(60)]   # same length
    log.draw(a, 10, 10, w, h)
    b = pygame.Surface((w + 20, h + 20))
    _reference_log_draw(log, b, 10, 10, w, h)
    assert _bytes(a) == _bytes(b), "a replaced entries list must not draw stale text"
    log.entries[-1] = ("Restored line 59. (x2)", 'info')                  # edited in place
    log.draw(a, 10, 10, w, h)
    _reference_log_draw(log, b, 10, 10, w, h)
    assert _bytes(a) == _bytes(b), "an edited entry must not draw stale text"
    log.replace([("One.", 'info'), ("Two.", 'danger')])
    log.draw(a, 10, 10, w, h)
    _reference_log_draw(log, b, 10, 10, w, h)
    assert _bytes(a) == _bytes(b)
    log.clear()
    assert log.entries == [] and log._wrapped == []
    log.add("After clear.")
    log.draw(a, 10, 10, w, h)


@pytest.mark.parametrize('w,h', [(1342, 200), (400, 200), (180, 400), (2862, 200), (600, 30)])
def test_log_cached_draw_is_pixel_identical(w, h):
    log = _full_log(12)
    log.add("A" * 90)                       # oversized token: character breaks
    log.add("two\nlines", 'danger')
    a = pygame.Surface((w + 20, h + 20))
    b = pygame.Surface((w + 20, h + 20))
    log.draw(a, 10, 10, w, h)
    log.draw(a, 10, 10, w, h)               # warm (cached) frame
    _reference_log_draw(log, b, 10, 10, w, h)
    assert _bytes(a) == _bytes(b)


def test_log_full_60_entry_frame_is_fast():
    """A full log (60 long entries) at 1920x1080 (log pane 1342 x 200) and at
    3440x1440 (2862 x 200). Before the cache this re-wrapped all 60 entries
    every frame (about 5-8 ms, FOUNDATION_REVIEW 2.2); measured after: about
    0.3 / 0.5 ms. Budget 2 ms leaves room for a slow test machine."""
    log = _full_log()
    scr = pygame.display.set_mode((3440, 1440))
    try:
        for w in (1342, 2862):
            log.draw(scr, 248, 880, w, 200)
            ts = []
            for _ in range(15):
                t0 = time.perf_counter()
                log.draw(scr, 248, 880, w, 200)
                ts.append((time.perf_counter() - t0) * 1000)
            med = sorted(ts)[len(ts) // 2]
            assert med < 2.0, f"full-log frame at pane width {w}: {med:.2f} ms"
    finally:
        pygame.display.set_mode((64, 64))


# =============================================================================
# 2. Overlays
# =============================================================================

def _reference_overlay(surf, alpha, color=(0, 0, 0)):
    ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    ov.fill((*color, alpha))
    surf.blit(ov, (0, 0))


def _busy_canvas(w=300, h=200):
    s = pygame.Surface((w, h))
    for x in range(0, w, 7):
        pygame.draw.line(s, ((x * 3) % 256, (x * 7) % 256, 200), (x, 0), (w - x, h), 3)
    return s


@pytest.mark.parametrize('alpha,color', [(190, (0, 0, 0)), (95, (0, 0, 0)), (180, (50, 0, 0)),
                                         (190, (8, 6, 2)), (220, (0, 0, 0))])
def test_overlay_is_pixel_identical_to_a_fresh_surface(alpha, color):
    a, b = _busy_canvas(), _busy_canvas()
    fantasy_ui.draw_overlay(a, alpha, color)
    fantasy_ui.draw_overlay(a.copy(), alpha, color)      # second call: cached path
    a2 = _busy_canvas()
    fantasy_ui.draw_overlay(a2, alpha, color)
    _reference_overlay(b, alpha, color)
    assert _bytes(a) == _bytes(b) == _bytes(a2)


def test_overlay_surface_is_reused_and_bounded():
    s = _busy_canvas()
    fantasy_ui.draw_overlay(s, 190)
    first = dict(ui_theme._overlays)
    fantasy_ui.draw_overlay(s, 190)
    assert dict(ui_theme._overlays) == first, "same overlay must reuse its surface"
    for a in range(10, 250, 10):                         # an animated alpha
        fantasy_ui.draw_overlay(s, a)
    assert len(ui_theme._overlays) <= ui_theme._OVERLAY_MAX
    big = _busy_canvas(500, 400)                          # window resized
    fantasy_ui.draw_overlay(big, 190)
    assert all(k[0] == (500, 400) for k in ui_theme._overlays)


def test_overlay_cache_memory_is_bounded_at_3440x1440():
    """GROUNDWORK_REVIEW 5: four window-sized washes pinned ~79 MB at
    3440x1440. The game uses at least 7 (colour, alpha) keys; after all of
    them the cache must hold no more than ~40 MB, and stay pixel-identical."""
    scr = pygame.Surface((3440, 1440))
    keys = [(190, (0, 0, 0)), (200, (0, 0, 0)), (210, (0, 0, 0)), (220, (0, 0, 0)),
            (95, (0, 0, 0)), (180, (50, 0, 0)), (160, (40, 30, 5)), (123, (0, 0, 0))]
    for alpha, color in keys * 2:
        fantasy_ui.draw_overlay(scr, alpha, color)
        held = sum(o.get_width() * o.get_height() * o.get_bytesize()
                   for o in ui_theme._overlays.values())
        assert held <= 40 * 1024 * 1024, f"{held / 2**20:.0f} MB of overlays"
        assert held == ui_theme.overlay_cache_bytes()
    assert len(ui_theme._overlays) <= 2
    small = _busy_canvas()
    for alpha, color in keys:                          # thrashing stays correct
        a, b = small.copy(), small.copy()
        fantasy_ui.draw_overlay(a, alpha, color)
        _reference_overlay(b, alpha, color)
        assert _bytes(a) == _bytes(b)


def test_welcome_glow_and_vignette_are_built_once_per_size(monkeypatch):
    """GROUNDWORK_REVIEW 10: the title screen allocated two full-window
    SRCALPHA surfaces (radial glow + vignette) on every frame. They are
    static for a window size, so they are built once and kept; the pixels
    are unchanged and a resize rebuilds them."""
    from welcome_screen import WelcomeScreen
    scr = pygame.Surface((1280, 720))
    w = WelcomeScreen(scr, 'test')
    allocs = []
    real_surface = pygame.Surface

    class Counting(real_surface):
        def __init__(self, size, *a, **k):
            allocs.append(tuple(size))
            super().__init__(size, *a, **k)
    monkeypatch.setattr(pygame, 'Surface', Counting)

    def frame():
        scr.fill((20, 30, 40))
        w._draw_radial_glow(w.cx, w.cy)
        w._draw_vignette()
        return _bytes(scr)
    first = frame()
    del allocs[:]
    for _ in range(3):
        assert frame() == first
    assert (1280, 720) not in allocs, f"full-window surfaces allocated per frame: {allocs}"
    # Pixels match the per-frame build the screen used to do.
    monkeypatch.setattr(pygame, 'Surface', real_surface)
    ref = real_surface((1280, 720))
    ref.fill((20, 30, 40))
    glow = real_surface((1280, 720), pygame.SRCALPHA)
    for r, alpha in [(300, 12), (240, 18), (180, 22), (130, 28), (90, 20)]:
        pygame.draw.circle(glow, (*FP.ARCANE_DIM, alpha), (w.cx, w.cy), r)
    ref.blit(glow, (0, 0))
    vig = real_surface((1280, 720), pygame.SRCALPHA)
    for step in range(28):
        alpha, margin = int(220 * (step / 28) ** 2.2), int(step * 16)
        pygame.draw.rect(vig, (0, 0, 0, alpha), (margin, margin, 1280 - 2 * margin,
                                                 720 - 2 * margin), 10)
    ref.blit(vig, (0, 0))
    assert first == _bytes(ref)
    # A resize rebuilds at the new size.
    w.screen = scr = real_surface((1600, 900))
    w.W, w.H, w.cx, w.cy = 1600, 900, 800, 450
    frame()
    assert w._glow_cache[1].get_size() == (1600, 900)
    assert w._vignette_cache[1].get_size() == (1600, 900)


def test_no_hand_built_full_window_overlays_left():
    """FOUNDATION_REVIEW 2.3: eight overlays were hand-built. All of them now
    go through fantasy_ui.draw_overlay (cached)."""
    src = _ROOT / 'src'
    pat = re.compile(r"pygame\.Surface\(\(\s*layout\.WINDOW_W\s*,\s*layout\.WINDOW_H\s*\)")
    hits = [f"{p.name}:{i}" for p in src.rglob('*.py') if 'dev_tools' not in p.parts
            for i, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1)
            if pat.search(line)]
    assert not hits, hits


# =============================================================================
# 4. Parchment
# =============================================================================

def test_parchment_png_is_loaded_once_and_scaled_once_per_size(tmp_path, monkeypatch):
    img = pygame.Surface((64, 64))
    img.fill((200, 170, 120))
    pygame.image.save(img, str(tmp_path / 'parchment.png'))
    ui_theme.load(asset_dir=str(tmp_path / 'no_ui'), texture_dir=str(tmp_path))

    loads, scales = [], []
    real_scale = pygame.transform.smoothscale
    monkeypatch.setattr(pygame.image, 'load', lambda *a, **k: loads.append(a))
    monkeypatch.setattr(pygame.transform, 'smoothscale',
                        lambda *a, **k: (scales.append(a), real_scale(*a, **k))[1])
    monkeypatch.setattr(os.path, 'exists', lambda p: pytest.fail('stat during draw'))
    s = _canvas(600, 200)
    for _ in range(5):
        fantasy_ui.draw_panel(s, (10, 10, 500, 96), border_color=FP.GOLD)
    assert loads == [], "the texture must be loaded at startup, not when drawn"
    assert len(scales) == 1, "one scale per size, then cached"
    assert s.get_at((200, 60))[:3] != (37, 81, 23)


def test_parchment_absent_draws_procedural_without_touching_disk(monkeypatch):
    ui_theme.load(asset_dir='/nonexistent/ui', texture_dir='/nonexistent/tex')
    monkeypatch.setattr(os.path, 'exists', lambda p: pytest.fail('stat during draw'))
    monkeypatch.setattr(os.path, 'isfile', lambda p: pytest.fail('stat during draw'))
    s = _canvas(600, 200)
    fantasy_ui.draw_panel(s, (10, 10, 500, 96), border_color=FP.GOLD)
    ref = _canvas(600, 200)
    ref.blit(fantasy_ui.make_parchment(500, 96, alpha=238), (10, 10))
    fantasy_ui._parchment_panel_frame(ref, 10, 10, 500, 96, FP.GOLD)
    assert _bytes(s) == _bytes(ref)


# =============================================================================
# 5. Paint order + opacity
# =============================================================================

def test_header_strip_no_longer_covers_the_panel_border():
    accent = (195, 190, 215)
    s = _canvas(500, 300)
    panel = pygame.Rect(40, 40, 400, 220)
    fantasy_ui.draw_dark_panel(s, panel, border_color=accent)
    fantasy_ui.draw_header_bar(s, (panel.x, panel.y, panel.w, 44), text='TITLE',
                               font=fantasy_ui.get_font('heading', 20),
                               accent=accent, frame=(panel, accent))
    # Top border, left border and right border inside the header's height.
    assert s.get_at((panel.x + 100, panel.y))[:3] == accent
    assert s.get_at((panel.x, panel.y + 20))[:3] == accent
    assert s.get_at((panel.right - 1, panel.y + 20))[:3] == accent
    # The strip itself is still there in its interior.
    assert s.get_at((panel.x + 100, panel.y + 15))[:3] == FP.MIDNIGHT
    assert s.get_at((panel.x + 100, panel.y + 35))[:3] == FP.MIDNIGHT_MID


def test_header_without_frame_is_unchanged():
    """The sidebar's headers (no panel) draw exactly as before."""
    s = _canvas(300, 60)
    fantasy_ui.draw_header_bar(s, (10, 10, 228, 24), text='POWERS',
                               font=fantasy_ui.get_font('heading', 17),
                               accent=FP.GOLD_DARK, kind='header_small')
    ref = _canvas(300, 60)
    _ref_header_bar(ref, (10, 10, 228, 24), 'POWERS', fantasy_ui.get_font('heading', 17),
                    FP.GOLD_BRIGHT, FP.GOLD_DARK)
    assert _bytes(s) == _bytes(ref)


def test_frame_repaint_changes_nothing_outside_the_strip():
    accent = FP.GOLD
    panel = pygame.Rect(30, 30, 300, 200)
    a, b = _canvas(), _canvas()
    for s in (a, b):
        fantasy_ui.draw_dark_panel(s, panel, border_color=accent)
        fantasy_ui.draw_header_bar(s, (panel.x, panel.y, panel.w, 44), accent=accent,
                                   frame=(panel, accent) if s is a else None)
    a.set_clip(None)
    strip = pygame.Rect(panel.x, panel.y, panel.w, 44)
    for y in range(a.get_height()):
        for x in range(0, a.get_width(), 3):
            if not strip.collidepoint(x, y):
                assert a.get_at((x, y)) == b.get_at((x, y)), (x, y)


@pytest.mark.parametrize('kind', ['panel', 'quiz'])
def test_panel_body_is_opaque(kind):
    """Lead decision 2026-10-15: nothing behind a panel shows through it."""
    rect = pygame.Rect(20, 20, 300, 200)
    black, white = _canvas(color=(0, 0, 0)), _canvas(color=(255, 255, 255))
    for s in (black, white):
        fantasy_ui.draw_dark_panel(s, rect, border_color=FP.GOLD, kind=kind)
    inner = rect.inflate(-12, -12)
    assert _bytes(black.subsurface(inner)) == _bytes(white.subsurface(inner))
    assert black.get_at(inner.center)[:3] in (FP.MIDNIGHT,
                                               tuple(v + 4 for v in FP.MIDNIGHT))


def test_panel_never_leaves_the_clip_untouched_state():
    s = _canvas()
    s.set_clip(pygame.Rect(5, 5, 100, 100))
    fantasy_ui.draw_dark_panel(s, (20, 20, 200, 150))
    fantasy_ui.draw_header_bar(s, (20, 20, 200, 40), frame=((20, 20, 200, 150), FP.GOLD))
    assert s.get_clip() == pygame.Rect(5, 5, 100, 100)


# =============================================================================
# 6. The art kit
# =============================================================================

GOLD_ART = (201, 160, 40)
TL, TR, BL, BR = (250, 0, 0), (0, 250, 0), (0, 0, 250), (250, 250, 0)
EDGE, CENTER = (90, 60, 20), (20, 24, 50)


def _nine(size=48, b=12):
    """A test nine-slice: distinct corner colours, EDGE border, CENTER body."""
    img = pygame.Surface((size, size), pygame.SRCALPHA)
    img.fill(CENTER + (255,))
    pygame.draw.rect(img, EDGE + (255,), (0, 0, size, size), b)
    img.fill(TL + (255,), (0, 0, b, b))
    img.fill(TR + (255,), (size - b, 0, b, b))
    img.fill(BL + (255,), (0, size - b, b, b))
    img.fill(BR + (255,), (size - b, size - b, b, b))
    return img


def _make_kit(tmp_path, pieces, *, scale=1, extra=None):
    manifest = {'version': 1, 'scale': scale, 'pieces': {}}
    for name, (img, sl, more) in pieces.items():
        pygame.image.save(img, str(tmp_path / f'{name}.png'))
        manifest['pieces'][name] = {'file': f'{name}.png', 'slice': sl, **(more or {})}
    if extra:
        manifest.update(extra)
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    return ui_theme.load(asset_dir=str(tmp_path), texture_dir=str(tmp_path / 'none'))


def test_empty_assets_folder_loads_nothing():
    k = ui_theme.load()                     # the real assets/ui (README only)
    assert k.pieces == {} and k.errors == []


def test_nine_slice_draws_corners_edges_and_body_at_any_size(tmp_path, monkeypatch):
    _make_kit(tmp_path, {'panel': (_nine(), [12, 12, 12, 12], {'body': 'tile'})})
    assert ui_theme.has('panel')
    # Drawing must never load or rescale (FOUNDATION_REVIEW 2.5).
    for mod, name in ((pygame.image, 'load'), (pygame.transform, 'smoothscale'),
                      (pygame.transform, 'scale')):
        monkeypatch.setattr(mod, name, lambda *a, **k: pytest.fail('load/scale during draw'))
    for h in (40, 41, 157, 300, 299, 612):            # the quiz height changes per question
        s = _canvas(700, 700)
        r = pygame.Rect(30, 20, 501, h)
        fantasy_ui.draw_dark_panel(s, r, border_color=FP.GOLD)
        assert s.get_at((r.x, r.y))[:3] == TL
        assert s.get_at((r.right - 1, r.y))[:3] == TR
        assert s.get_at((r.x, r.bottom - 1))[:3] == BL
        assert s.get_at((r.right - 1, r.bottom - 1))[:3] == BR
        assert s.get_at((r.centerx, r.y + 3))[:3] == EDGE
        assert s.get_at((r.x + 3, r.centery))[:3] == EDGE
        if h > 24:
            assert s.get_at((r.centerx, r.centery))[:3] == CENTER
        assert s.get_at((r.right, r.centery))[:3] == (37, 81, 23), "drew outside the rect"
        assert s.get_at((r.x, r.bottom))[:3] == (37, 81, 23)


def test_art_body_is_opaque_even_if_the_painted_centre_is_not(tmp_path):
    img = _nine()
    img.fill((0, 0, 0, 0), (12, 12, 24, 24))          # a hole in the middle
    _make_kit(tmp_path, {'panel': (img, [12, 12, 12, 12], {})})
    s = _canvas(color=(255, 255, 255))
    fantasy_ui.draw_dark_panel(s, (10, 10, 200, 150))
    assert s.get_at((110, 85))[:3] == FP.MIDNIGHT


def test_box_smaller_than_the_corners_falls_back_to_procedural(tmp_path):
    _make_kit(tmp_path, {'chip': (_nine(), [12, 12, 12, 12], {})})
    s = _canvas()
    assert ui_theme.draw_piece(s, 'chip', (10, 10, 20, 20)) is False
    assert ui_theme.draw_piece(s, 'chip', (10, 10, 24, 24)) is True


def test_accent_layer_is_tinted_and_the_painted_frame_is_not(tmp_path):
    frame = _nine()
    frame.fill(GOLD_ART + (255,), (0, 0, 48, 12))      # painted gold top band
    accent = pygame.Surface((48, 48), pygame.SRCALPHA)
    accent.fill((0, 0, 0, 0))
    accent.fill((255, 255, 255, 255), (20, 0, 8, 6))   # a white gem in the top edge
    pygame.image.save(accent, str(tmp_path / 'quiz_accent.png'))
    _make_kit(tmp_path, {'quiz': (frame, [12, 12, 12, 12], {'accent': 'quiz_accent.png'})})
    subject = FP.SUBJECT['cooking']
    s = _canvas(400, 300)
    fantasy_ui.draw_dark_panel(s, (0, 0, 300, 200), border_color=subject, kind='quiz')
    # The gem pixels sit in the tiled top strip: every tile repeats it.
    assert s.get_at((20 + 2, 2))[:3] == subject
    assert s.get_at((5, 2))[:3] == GOLD_ART            # corner untouched
    assert s.get_at((30, 8))[:3] == GOLD_ART           # painted gold never tinted
    # A second subject reuses nothing wrong: different colour, same geometry.
    s2 = _canvas(400, 300)
    fantasy_ui.draw_dark_panel(s2, (0, 0, 300, 200), border_color=FP.SUBJECT['math'], kind='quiz')
    assert s2.get_at((22, 2))[:3] == FP.SUBJECT['math']


def test_header_frame_repaint_uses_the_art_frame(tmp_path):
    _make_kit(tmp_path, {'panel': (_nine(), [12, 12, 12, 12], {})})
    s = _canvas(500, 300)
    panel = pygame.Rect(40, 40, 400, 220)
    fantasy_ui.draw_dark_panel(s, panel)
    fantasy_ui.draw_header_bar(s, (panel.x, panel.y, panel.w, 44), frame=(panel, FP.GOLD))
    assert s.get_at((panel.x, panel.y))[:3] == TL
    assert s.get_at((panel.centerx, panel.y + 3))[:3] == EDGE
    assert s.get_at((panel.x + 3, panel.y + 30))[:3] == EDGE


def test_choice_card_frame_is_drawn_over_its_badge(tmp_path):
    badge = pygame.Surface((24, 24), pygame.SRCALPHA)
    badge.fill((10, 200, 200, 255))
    _make_kit(tmp_path, {'choice': (_nine(), [12, 12, 12, 12], {}),
                         'choice_badge': (badge, [0, 0, 0, 0], {})})
    s = _canvas(500, 200)
    fantasy_ui.draw_choice_button(s, (10, 10, 300, 60), '1', 'An answer',
                                  fantasy_ui.get_font('body', 20), fantasy_ui.get_font('body', 20))
    assert s.get_at((30, 13))[:3] == EDGE, "the card's top edge must sit over the badge"
    assert s.get_at((30, 40))[:3] == (10, 200, 200)


def test_scale_2_art_is_downscaled_once_at_load(tmp_path):
    _make_kit(tmp_path, {'panel': (_nine(96, 24), [24, 24, 24, 24], {})}, scale=2)
    p = ui_theme.kit().pieces['panel']
    assert (p.l, p.t, p.r, p.b) == (12, 12, 12, 12)
    assert p.tl.get_size() == (12, 12)


def test_divider_three_slice(tmp_path):
    img = pygame.Surface((60, 6), pygame.SRCALPHA)
    img.fill((150, 110, 30, 255))
    img.fill((255, 0, 0, 255), (0, 0, 10, 6))
    img.fill((0, 255, 0, 255), (50, 0, 10, 6))
    _make_kit(tmp_path, {'divider': (img, [10, 0, 10, 0], {})})
    s = _canvas(400, 60)
    fantasy_ui.draw_divider(s, 20, 30, 300)
    assert s.get_at((22, 30))[:3] == (255, 0, 0)
    assert s.get_at((317, 30))[:3] == (0, 255, 0)
    assert s.get_at((170, 30))[:3] == (150, 110, 30)
    assert s.get_at((170, 24))[:3] == (37, 81, 23)      # 6 px tall, centred on y


def test_bad_manifest_entries_are_reported_not_fatal(tmp_path):
    k = _make_kit(tmp_path, {'panel': (_nine(), [40, 40, 40, 40], {}),   # slice too big
                             'nonsense': (_nine(), [1, 1, 1, 1], {})},
                  extra={'icons': {'sizes': [16], 'files': {'gone': 'icons/gone.png'}}})
    assert k.pieces == {}
    assert any('nonsense' in e for e in k.errors)
    assert any('panel' in e for e in k.errors)
    assert any('gone.png' in e for e in k.errors)
    (tmp_path / 'manifest.json').write_text('{"version": 9}', encoding='utf-8')
    assert ui_theme.load(asset_dir=str(tmp_path)).pieces == {}
    (tmp_path / 'manifest.json').write_text('{not json', encoding='utf-8')
    assert ui_theme.load(asset_dir=str(tmp_path)).errors


# -- Malformed manifests never crash (GROUNDWORK_REVIEW 1) -------------------

def _fuzz_folder(tmp_path):
    """A kit folder holding good, bad and awkward image files."""
    pygame.image.save(_nine(), str(tmp_path / 'panel.png'))
    pygame.image.save(_nine(), str(tmp_path / 'chip.png'))
    pal = pygame.Surface((48, 48), 0, 8)                  # 8-bit palette PNG
    pal.fill((120, 90, 30))
    pygame.image.save(pal, str(tmp_path / 'palette.png'))
    pygame.image.save(pygame.Surface((5000, 4)), str(tmp_path / 'huge.png'))
    small = pygame.Surface((10, 10), pygame.SRCALPHA)
    small.fill((255, 255, 255, 255))
    pygame.image.save(small, str(tmp_path / 'small.png'))
    (tmp_path / 'corrupt.png').write_bytes(b'\x89PNG\r\n\x1a\n this is not a png')
    (tmp_path / 'empty.png').write_bytes(b'')
    (tmp_path / 'text.png').write_text('hello', encoding='utf-8')
    (tmp_path / 'adir.png').mkdir()
    (tmp_path / 'icons').mkdir()
    pygame.image.save(small, str(tmp_path / 'icons' / 'hp.png'))
    return tmp_path


def _panel(**spec):
    return {'version': 1, 'pieces': {'panel': {'file': 'panel.png',
                                               'slice': [12, 12, 12, 12], **spec}}}


# The 12 manifests the reviewer showed crashing load() (GROUNDWORK_REVIEW 1),
# as raw JSON text.
REVIEWER_MANIFESTS = [
    '[]',
    '{"version": "one"}',
    '{"scale": "big"}',
    '{"pieces": {"panel": "panel.png"}}',
    '{"pieces": ["panel"]}',
    json.dumps(_panel(slice=5)),
    json.dumps(_panel(slice='abcd')),
    json.dumps(_panel(body_color='red')),
    json.dumps(_panel(file=None)),
    json.dumps({'version': 1, 'icons': {'sizes': [-4], 'files': {'hp': 'icons/hp.png'}}}),
    json.dumps({'version': 1, 'scale': -1, 'pieces': _panel()['pieces']}),
    json.dumps({'version': 1, 'scale': 0, 'pieces': _panel()['pieces']}),
]

MORE_MANIFESTS = [
    'null', '42', '"panel"', 'true', '{}', '{"version": null}', '{"version": true}',
    '{"version": 1.5}', '{"version": [1]}', '{"scale": NaN}', '{"scale": Infinity}',
    '{"scale": 1e-9}', '{"scale": 1e9}', '{"scale": true}', '{"scale": null}',
    '{"pixel_art": "yes"}', '{"pieces": null}', '{"pieces": 7}', '{"pieces": "panel"}',
    '{"icons": 3}', '{"icons": {"sizes": "16"}}', '{"icons": {"sizes": [0, 1e9, "8", true]}}',
    '{"icons": {"sizes": [16], "files": ["hp"]}}',
    '{"icons": {"sizes": [16], "files": {"hp": 5, "x": "corrupt.png", "y": "../hp.png"}}}',
    '{"icons": {"sizes": [100000], "files": {"hp": "icons/hp.png"}}}',
    json.dumps(_panel(slice=[1, 2, 3])),
    json.dumps(_panel(slice=[1, 2, 3, 4, 5])),
    json.dumps(_panel(slice=[-1, 0, 0, 0])),
    json.dumps(_panel(slice=[10 ** 12, 0, 0, 0])),
    json.dumps(_panel(slice=[True, 1, 1, 1])),
    json.dumps(_panel(slice=[1.5, 1, 1, 1])),
    json.dumps(_panel(slice=[None, 1, 1, 1])),
    json.dumps(_panel(slice={'l': 1})),
    json.dumps(_panel(slice=[30, 30, 30, 30])),             # oversized for a 48 px image
    json.dumps(_panel(file='corrupt.png')),
    json.dumps(_panel(file='empty.png')),
    json.dumps(_panel(file='text.png')),
    json.dumps(_panel(file='adir.png')),
    json.dumps(_panel(file='missing.png')),
    json.dumps(_panel(file='huge.png', slice=[0, 0, 0, 0])),
    json.dumps(_panel(file='../panel.png')),
    json.dumps(_panel(file='C:/Windows/win.ini')),
    json.dumps(_panel(file='/etc/passwd')),
    json.dumps(_panel(file='')),
    json.dumps(_panel(file=['panel.png'])),
    json.dumps(_panel(file={'name': 'panel.png'})),
    json.dumps(_panel(body=7)),
    json.dumps(_panel(body='glass')),
    json.dumps(_panel(body_color=[300, -1, 2])),
    json.dumps(_panel(body_color=[1, 2])),
    json.dumps(_panel(body_color=None)),
    json.dumps(_panel(pixel_art='no')),
    json.dumps(_panel(accent=5)),
    json.dumps(_panel(accent='small.png')),                  # wrong size
    json.dumps(_panel(accent='corrupt.png')),
    json.dumps(_panel(ornament=['x'])),
    json.dumps(_panel(ornament='corrupt.png')),
    json.dumps({'version': 1, 'scale': 2, 'pieces': {
        'panel': {'file': 'palette.png', 'slice': [12, 12, 12, 12]},   # 8-bit at scale 2
        'divider': {'file': 'palette.png', 'slice': [1, 0, 1, 0], 'ornament': 'palette.png'}}}),
    json.dumps({'version': 1, 'scale': 0.125, 'pieces': _panel()['pieces']}),
    json.dumps({'version': 1, 'pieces': {'nonsense': {}, 7: {}, 'panel': []}}),
    json.dumps({'version': 1, 'pieces': {n: None for n in ui_theme.PIECES}}),
    json.dumps({'version': 1, 'pieces': {n: {'file': 'chip.png', 'slice': [12, 12, 12, 12]}
                                         for n in ui_theme.PIECES}}),
]


def _fuzzed_manifests(n=150, seed=20261016):
    """Random mutations of a valid manifest: leaves swapped for junk."""
    import random
    rng = random.Random(seed)
    junk = [None, True, False, -1, 0, 1, 2, 3.7, -2.5, 10 ** 9, '', 'x', 'panel.png',
            'corrupt.png', '../x', [], [1], [1, 2, 3, 4], [-4, 0, 0, 0], ['a'] * 4, {},
            {'a': 1}, [[1]], 'NaN']
    out = []
    for _ in range(n):
        m = {'version': 1, 'scale': 1, 'pixel_art': False, 'pieces': {
            'panel': {'file': 'panel.png', 'slice': [12, 12, 12, 12], 'body': 'tile',
                      'body_color': [20, 24, 50], 'accent': 'panel.png'},
            'divider': {'file': 'chip.png', 'slice': [10, 0, 10, 0], 'ornament': 'small.png'}},
            'icons': {'sizes': [16, 32], 'files': {'hp': 'icons/hp.png'}}}
        for _k in range(rng.randint(1, 4)):
            node, path = m, []
            while isinstance(node, (dict, list)) and node and rng.random() < 0.75:
                keys = list(node) if isinstance(node, dict) else list(range(len(node)))
                key = rng.choice(keys)
                path.append((node, key))
                node = node[key]
            if path:
                parent, key = path[-1]
                parent[key] = rng.choice(junk)
            else:
                m = rng.choice(junk)
                break
        out.append(json.dumps(m))
    return out


def _draw_everything():
    """Every kit-aware helper, on a scratch canvas (must not raise)."""
    s = _canvas(500, 400)
    f = fantasy_ui.get_font('body', 20)
    for rect in ((10, 10, 300, 200), (0, 0, 3, 3), (5, 5, 40, 30)):
        fantasy_ui.draw_dark_panel(s, rect, kind='quiz')
        fantasy_ui.draw_dark_panel(s, rect)
        fantasy_ui.draw_header_bar(s, (rect[0], rect[1], rect[2], 30), text='T', font=f,
                                   frame=(rect, FP.GOLD))
    fantasy_ui.draw_divider(s, 10, 250, 300)
    fantasy_ui.draw_choice_button(s, (10, 260, 300, 60), '1', ['An answer'], f, f,
                                  selected=True)
    fantasy_ui.draw_input_box(s, (10, 330, 200, 30), 'x', f)
    ui_theme.draw_icon(s, 'hp', (400, 10, 32, 32))
    ui_theme.draw_icon(s, 'hp', (400, 10, 0, 0))


def _load_text(folder, text):
    (folder / 'manifest.json').write_text(text, encoding='utf-8')
    return ui_theme.load(asset_dir=str(folder), texture_dir=str(folder / 'none'))


@pytest.mark.parametrize('display', [True, False], ids=['display', 'no_display'])
def test_malformed_manifests_never_crash(tmp_path, caplog, display):
    folder = _fuzz_folder(tmp_path)
    cases = REVIEWER_MANIFESTS + MORE_MANIFESTS + _fuzzed_manifests()
    if not display:
        pygame.display.quit()
    try:
        crashes = []
        for text in cases:
            caplog.clear()
            try:
                with caplog.at_level('WARNING', logger='ui_theme'):
                    k = _load_text(folder, text)
                _draw_everything()
            except Exception as e:              # noqa: BLE001 -- the point of the test
                crashes.append(f"{text[:90]} -> {type(e).__name__}: {e}")
                continue
            warnings = [r for r in caplog.records if r.name == 'ui_theme']
            if k.errors and len(warnings) != 1:
                crashes.append(f"{text[:90]} -> {len(warnings)} warnings, want 1")
            if not k.errors and warnings:
                crashes.append(f"{text[:90]} -> warned with no errors")
        assert not crashes, f"{len(crashes)} of {len(cases)}:\n" + "\n".join(crashes[:40])
    finally:
        if not display:
            pygame.display.init()
            pygame.display.set_mode((64, 64))
    # The reviewer's twelve are each reported (not silently half-loaded).
    for text in REVIEWER_MANIFESTS:
        k = _load_text(folder, text)
        assert k.errors, text
        if 'body_color' not in text:        # a bad colour drops only the colour
            assert 'panel' not in k.pieces, text


def test_a_bad_piece_drops_only_itself(tmp_path, caplog):
    folder = _fuzz_folder(tmp_path)
    text = json.dumps({'version': 1, 'pieces': {
        'panel': {'file': 'panel.png', 'slice': [12, 12, 12, 12], 'body_color': 'red'},
        'chip': {'file': 'chip.png', 'slice': 'abcd'},
        'row': {'file': 'corrupt.png', 'slice': [1, 1, 1, 1]},
        'key': {'file': 'chip.png', 'slice': [12, 12, 12, 12]}},
        'icons': {'sizes': [-4, 16], 'files': {'hp': 'icons/hp.png', 'mp': None}}})
    with caplog.at_level('WARNING', logger='ui_theme'):
        k = _load_text(folder, text)
    assert set(k.pieces) == {'panel', 'key'}            # bad body_color is dropped, not the panel
    assert k.pieces['panel'].body_color is None
    assert set(k.icon_src) == {'hp'} and ('hp', 16) in k.icons
    assert len(k.errors) == 5, k.errors
    assert len([r for r in caplog.records if r.name == 'ui_theme']) == 1


def test_main_guards_the_kit_load():
    main_src = (_ROOT / 'src' / 'main.py').read_text(encoding='utf-8')
    m = main_src.index('def main(')
    seg = main_src[main_src.index('ui_theme.load()', m) - 120:main_src.index('ui_theme.load()', m) + 120]
    assert 'try:' in seg and 'except Exception' in seg and 'ui_theme.unload()' in seg


def test_icons_prescaled_at_load(tmp_path, monkeypatch):
    (tmp_path / 'icons').mkdir()
    ico = pygame.Surface((16, 16), pygame.SRCALPHA)
    ico.fill((255, 0, 0, 255))
    pygame.image.save(ico, str(tmp_path / 'icons' / 'hp.png'))
    _make_kit(tmp_path, {}, extra={'icons': {'sizes': [32], 'files': {'hp': 'icons/hp.png'}}})
    monkeypatch.setattr(pygame.transform, 'smoothscale', lambda *a, **k: pytest.fail('scale'))
    s = _canvas(100, 100)
    assert ui_theme.draw_icon(s, 'hp', (10, 10, 32, 32))
    assert s.get_at((26, 26))[:3] == (255, 0, 0)
    assert ui_theme.icon('missing', 32) is None


def test_load_is_wired_at_startup_and_never_in_draw_code():
    main_src = (_ROOT / 'src' / 'main.py').read_text(encoding='utf-8')
    assert 'ui_theme.load()' in main_src
    m = main_src.index('def main(')
    assert main_src.index('set_mode', m) < main_src.index('ui_theme.load()', m)
    for name in ('game_render.py', 'fantasy_ui.py', 'ui.py', 'welcome_screen.py', 'study_mode.py'):
        code = (_ROOT / 'src' / name).read_text(encoding='utf-8')
        assert not re.search(r'^\s*ui_theme\.load\(', code, re.M), name


def test_readme_documents_every_piece():
    readme = (_ROOT / 'assets' / 'ui' / 'README.md').read_text(encoding='utf-8')
    missing = [n for n in ui_theme.PIECES if f'`{n}`' not in readme]
    assert not missing, f"assets/ui/README.md does not document: {missing}"


# =============================================================================
# FALLBACK GATE (8d): no art -> exactly what the old helpers drew
# =============================================================================
# Reference copies of the procedural helpers as they were before the kit
# (main @ 7a8a6854), with ONLY the two intended changes applied:
#   * draw_dark_panel's body is opaque (fill + opaque texture lines);
#   * nothing else. (draw_header_bar's frame repaint is opt-in via frame=.)

def _ref_corner(surf, x, y, color, flip_x, flip_y, arm=20):
    sx = -1 if flip_x else 1
    sy = -1 if flip_y else 1
    pygame.draw.line(surf, color, (x, y), (x + sx * arm, y), 2)
    pygame.draw.line(surf, color, (x, y), (x, y + sy * arm), 2)
    pygame.draw.line(surf, FP.GOLD_DARK, (x + sx * 7, y + sy * 2), (x + sx * 2, y + sy * 7), 1)
    d = 5
    pygame.draw.polygon(surf, color, [(x, y - sy*d), (x + sx*d, y), (x, y + sy*d), (x - sx*d, y)])


def _ref_diamond(surf, x, y, color, vertical, size=6):
    d = size
    pts = ([(x-d, y), (x, y-d), (x+d, y), (x, y+d)] if vertical
           else [(x, y-d), (x+d, y), (x, y+d), (x-d, y)])
    pygame.draw.polygon(surf, color, pts)


def _ref_dark_panel(surf, rect, border_color):
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return
    surf.fill(FP.MIDNIGHT, (x, y, w, h))
    for row in range(0, h, 5):
        if row + 2 < h and (row // 5) % 2 == 0:
            c = tuple(min(255, v + 4) for v in FP.MIDNIGHT)
            pygame.draw.line(surf, c, (x + 3, y + row + 2), (x + w - 3, y + row + 2))
    pygame.draw.rect(surf, border_color, (x, y, w, h), 2, border_radius=4)
    pygame.draw.rect(surf, FP.GOLD_DARK, (x+5, y+5, w-10, h-10), 1, border_radius=2)
    _ref_corner(surf, x, y, border_color, False, False)
    _ref_corner(surf, x+w - 1, y, border_color, True, False)
    _ref_corner(surf, x, y+h - 1, border_color, False, True)
    _ref_corner(surf, x+w - 1, y+h - 1, border_color, True, True)
    for pos, vert in [((x + w//2, y), False), ((x + w//2, y+h - 1), False),
                      ((x, y + h//2), True), ((x+w - 1, y + h//2), True)]:
        _ref_diamond(surf, pos[0], pos[1], border_color, vert)


def _ref_header_bar(surf, rect, text, font, text_color, accent, right_reserve=0):
    x, y, w, h = rect
    pygame.draw.rect(surf, FP.MIDNIGHT, (x, y, w, h // 2))
    pygame.draw.rect(surf, FP.MIDNIGHT_MID, (x, y+h//2, w, h - h//2))
    pygame.draw.line(surf, accent, (x + 8, y + h - 1), (x + w - 8, y + h - 1), 1)
    for ax in [x + 14, x + w - 15]:
        _ref_diamond(surf, ax, y + h//2, accent, vertical=True, size=4)
    if text and font:
        text = fantasy_ui.fit_text(text, font, max(20, w - 56 - right_reserve))
        ts = font.render(text, True, text_color)
        sx = x + (w - right_reserve)//2 - ts.get_width()//2
        sy = y + h//2 - ts.get_height()//2
        surf.blit(font.render(text, True, FP.INK), (sx + 2, sy + 2))
        surf.blit(ts, (sx, sy))


def _ref_divider(surf, x, y, w, color):
    cx = x + w // 2
    pygame.draw.line(surf, color, (x + 18, y), (cx - 14, y), 1)
    pygame.draw.line(surf, color, (cx + 14, y), (x + w - 18, y), 1)
    d = 5
    pygame.draw.polygon(surf, color, [(cx-d*2, y), (cx, y-d), (cx+d*2, y), (cx, y+d)])


def _ref_choice_button(surf, rect, key_label, lines, key_font, text_font, state):
    x, y, w, h = rect
    bg_col, border_col = {
        'correct': ((20, 65, 22), FP.SUCCESS_TEXT),
        'incorrect': ((70, 14, 14), FP.DANGER_TEXT),
        'selected': (FP.MIDNIGHT_MID, FP.GOLD),
        'idle': (FP.MIDNIGHT, FP.GOLD_DARK)}[state]
    bg_s = pygame.Surface((w, h), pygame.SRCALPHA)
    bg_s.fill((*bg_col, 220))
    surf.blit(bg_s, (x, y))
    pygame.draw.rect(surf, border_col, (x, y, w, h), 1, border_radius=3)
    pygame.draw.rect(surf, FP.GOLD_DARK, (x + 3, y + 3, w - 6, h - 6), 1, border_radius=2)
    badge_w = 44
    badge_s = pygame.Surface((badge_w, h), pygame.SRCALPHA)
    badge_s.fill((*FP.MIDNIGHT_MID, 200))
    surf.blit(badge_s, (x, y))
    pygame.draw.line(surf, border_col, (x + badge_w, y), (x + badge_w, y + h), 1)
    k = key_font.render(key_label, True, FP.GOLD_BRIGHT)
    surf.blit(k, (x + badge_w//2 - k.get_width()//2, y + h//2 - k.get_height()//2))
    line_h = text_font.get_height() + 3
    ty = y + (h - len(lines) * line_h) // 2
    for line in lines:
        surf.blit(text_font.render(line, True, FP.PARCHMENT_LIGHT), (x + badge_w + 10, ty))
        ty += line_h


def _ref_input_box(surf, rect, value, font, border_color):
    x, y, w, h = rect
    pygame.draw.rect(surf, FP.MIDNIGHT_LIGHT, (x, y, w, h), border_radius=4)
    pygame.draw.rect(surf, border_color, (x, y, w, h), 1, border_radius=4)
    v = font.render(value or '_', True, FP.PARCHMENT_LIGHT)
    surf.blit(v, (x + 10, y + (h - v.get_height()) // 2))


_PANEL_RECTS = [(10, 10, 380, 280), (0, 0, 400, 300), (50, 60, 41, 23), (5, 5, 333, 157)]
_COLORS = [FP.GOLD, FP.SUBJECT['math'], FP.LORE_BLUE_BORDER, (200, 18, 18)]


@pytest.mark.parametrize('rect', _PANEL_RECTS)
@pytest.mark.parametrize('color', _COLORS)
@pytest.mark.parametrize('kind', ['panel', 'quiz'])
def test_fallback_dark_panel_matches_reference(rect, color, kind):
    a, b = _busy_canvas(400, 300), _busy_canvas(400, 300)
    fantasy_ui.draw_dark_panel(a, rect, border_color=color, kind=kind)
    _ref_dark_panel(b, rect, color)
    assert _bytes(a) == _bytes(b)


@pytest.mark.parametrize('h', [24, 32, 36, 44, 48])
@pytest.mark.parametrize('reserve', [0, 120])
def test_fallback_header_matches_reference(h, reserve):
    f = fantasy_ui.get_font('heading', 20)
    a, b = _busy_canvas(400, 100), _busy_canvas(400, 100)
    fantasy_ui.draw_header_bar(a, (10, 10, 360, h), text='EQUIP / UNEQUIP A VERY LONG TITLE',
                               font=f, text_color=FP.GOLD_BRIGHT, accent=FP.GOLD,
                               right_reserve=reserve)
    _ref_header_bar(b, (10, 10, 360, h), 'EQUIP / UNEQUIP A VERY LONG TITLE', f,
                    FP.GOLD_BRIGHT, FP.GOLD, reserve)
    assert _bytes(a) == _bytes(b)


def test_fallback_header_with_frame_is_reference_plus_clipped_frame():
    """The frame repaint is the one intended change: the reference header,
    then the reference panel frame clipped to the strip, then the title."""
    f = fantasy_ui.get_font('heading', 20)
    panel = pygame.Rect(10, 10, 360, 260)
    a, b = _busy_canvas(400, 300), _busy_canvas(400, 300)
    fantasy_ui.draw_dark_panel(a, panel, border_color=FP.GOLD)
    fantasy_ui.draw_header_bar(a, (10, 10, 360, 44), text='TITLE', font=f,
                               frame=(panel, FP.GOLD))
    _ref_dark_panel(b, panel, FP.GOLD)
    pygame.draw.rect(b, FP.MIDNIGHT, (10, 10, 360, 22))         # the two-tone strip
    pygame.draw.rect(b, FP.MIDNIGHT_MID, (10, 32, 360, 22))
    b.set_clip(pygame.Rect(10, 10, 360, 44))
    _ref_dark_panel_frame_only(b, panel, FP.GOLD)
    b.set_clip(None)
    # The separator + side diamonds, then the title, go on top of the frame.
    _ref_header_bar_chrome(b, (10, 10, 360, 44), FP.GOLD)
    _ref_header_bar_text(b, (10, 10, 360, 44), 'TITLE', f)
    assert _bytes(a) == _bytes(b)


def _ref_dark_panel_frame_only(surf, rect, color):
    x, y, w, h = rect
    pygame.draw.rect(surf, color, (x, y, w, h), 2, border_radius=4)
    pygame.draw.rect(surf, FP.GOLD_DARK, (x+5, y+5, w-10, h-10), 1, border_radius=2)
    _ref_corner(surf, x, y, color, False, False)
    _ref_corner(surf, x+w - 1, y, color, True, False)
    _ref_corner(surf, x, y+h - 1, color, False, True)
    _ref_corner(surf, x+w - 1, y+h - 1, color, True, True)
    for pos, vert in [((x + w//2, y), False), ((x + w//2, y+h - 1), False),
                      ((x, y + h//2), True), ((x+w - 1, y + h//2), True)]:
        _ref_diamond(surf, pos[0], pos[1], color, vert)


def _ref_header_bar_chrome(surf, rect, accent):
    x, y, w, h = rect
    pygame.draw.line(surf, accent, (x + 8, y + h - 1), (x + w - 8, y + h - 1), 1)
    for ax in [x + 14, x + w - 15]:
        _ref_diamond(surf, ax, y + h//2, accent, vertical=True, size=4)


def _ref_header_bar_text(surf, rect, text, font):
    x, y, w, h = rect
    ts = font.render(text, True, FP.GOLD_BRIGHT)
    sx = x + w//2 - ts.get_width()//2
    sy = y + h//2 - ts.get_height()//2
    surf.blit(font.render(text, True, FP.INK), (sx + 2, sy + 2))
    surf.blit(ts, (sx, sy))


@pytest.mark.parametrize('w', [60, 300, 777])
def test_fallback_divider_matches_reference(w):
    a, b = _busy_canvas(800, 60), _busy_canvas(800, 60)
    fantasy_ui.draw_divider(a, 10, 30, w, FP.GOLD_DARK)
    _ref_divider(b, 10, 30, w, FP.GOLD_DARK)
    assert _bytes(a) == _bytes(b)


@pytest.mark.parametrize('state', ['idle', 'selected', 'correct', 'incorrect'])
def test_fallback_choice_button_matches_reference(state):
    kf, tf = fantasy_ui.get_font('body', 26), fantasy_ui.get_font('body', 20)
    lines = ['It was forged into', 'the steel itself.']
    a, b = _busy_canvas(500, 120), _busy_canvas(500, 120)
    fantasy_ui.draw_choice_button(a, (10, 10, 460, 80), '2', lines, kf, tf,
                                  selected=state == 'selected',
                                  correct=True if state == 'correct' else None,
                                  incorrect=True if state == 'incorrect' else None)
    _ref_choice_button(b, (10, 10, 460, 80), '2', lines, kf, tf, state)
    assert _bytes(a) == _bytes(b)


def test_fallback_input_box_matches_reference():
    f = fantasy_ui.get_font('body', 26)
    a, b = _busy_canvas(), _busy_canvas()
    fantasy_ui.draw_input_box(a, (20, 20, 240, 38), '250', f, border_color=FP.GOLD)
    _ref_input_box(b, (20, 20, 240, 38), '250', f, FP.GOLD)
    assert _bytes(a) == _bytes(b)


class _UIHost:
    """Just enough of a Game for the RenderMixin._ui_* helpers."""


def _ui_host(surf):
    from game_render import RenderMixin
    host = type('Host', (RenderMixin,), {})
    g = host.__new__(host)
    g.screen = surf
    return g


def test_fallback_ui_kit_helpers_match_reference():
    """_ui_subpanel / _ui_chip / _ui_action_row / _ui_scrollbar /
    _ui_progress_bar with no art draw the old procedural chrome."""
    get_font = fantasy_ui.get_font
    a, b = _busy_canvas(500, 400), _busy_canvas(500, 400)
    g = _ui_host(a)
    g._ui_subpanel(pygame.Rect(10, 10, 300, 150), 'Choices', border_color=FP.GOLD_DARK)
    g._ui_chip(pygame.Rect(320, 10, 110, 28), 'Weapons', active=True, color=FP.GOLD)
    g._ui_chip(pygame.Rect(320, 50, 110, 28), 'Armor', active=False)
    g._ui_action_row(pygame.Rect(10, 200, 400, 48), 'Y', 'Accept the offer',
                     color=FP.BODY_TEXT, selected=True)
    g._ui_action_row(pygame.Rect(10, 260, 400, 48), 'N', 'Refuse', selected=False)
    g._ui_scrollbar(pygame.Rect(440, 100, 40, 200), 3, 40, 10)
    g._ui_progress_bar(pygame.Rect(20, 340, 300, 10), 0.4, label='40 %')

    h = _ui_host(b)
    r = pygame.Rect(10, 10, 300, 150)
    pygame.draw.rect(b, FP.MIDNIGHT, r, border_radius=6)
    pygame.draw.rect(b, FP.GOLD_DARK, r, 1, border_radius=6)
    pygame.draw.rect(b, FP.MIDNIGHT_MID, pygame.Rect(11, 11, 298, 29), border_radius=6)
    h._ui_blit_text('CHOICES', get_font('small', 14, bold=True), FP.GOLD_BRIGHT,
                    r.centerx, r.y + 7, align='center')
    for rect, label, active, color in ((pygame.Rect(320, 10, 110, 28), 'Weapons', True, FP.GOLD),
                                       (pygame.Rect(320, 50, 110, 28), 'Armor', False, FP.GOLD)):
        pygame.draw.rect(b, FP.MIDNIGHT_MID if active else FP.MIDNIGHT, rect, border_radius=5)
        pygame.draw.rect(b, color if active else FP.GOLD_DARK, rect, 1, border_radius=5)
        h._ui_blit_text(label, get_font('small', 14, bold=True),
                        FP.GOLD_BRIGHT if active else FP.FADED_TEXT,
                        rect.centerx, rect.y + 6, align='center', max_width=rect.w - 10)
    for rect, key, label, sel in ((pygame.Rect(10, 200, 400, 48), 'Y', 'Accept the offer', True),
                                  (pygame.Rect(10, 260, 400, 48), 'N', 'Refuse', False)):
        pygame.draw.rect(b, FP.MIDNIGHT_MID if sel else FP.MIDNIGHT, rect, border_radius=6)
        pygame.draw.rect(b, FP.GOLD if sel else FP.ARCANE_DIM, rect, 1, border_radius=6)
        kf, lf = get_font('small', 14, bold=True), get_font('small', 15, bold=True)
        key_w = max(42, min(rect.w // 3, kf.size(key)[0] + 20))
        kr = pygame.Rect(rect.x + 8, rect.y + 8, key_w, rect.h - 16)
        pygame.draw.rect(b, (96, 34, 28), kr, border_radius=5)
        pygame.draw.rect(b, FP.BODY_TEXT, kr, 1, border_radius=5)
        h._ui_blit_text(key, kf, FP.BODY_TEXT, kr.centerx,
                        kr.y + max(4, (kr.h - kf.get_height()) // 2), align='center')
        h._ui_wrap_text(label, lf, FP.BODY_TEXT,
                        pygame.Rect(kr.right + 12, rect.y + 8, rect.right - kr.right - 22, rect.h - 16),
                        line_gap=0, max_lines=2)
    track = pygame.Rect(440 + 40 - 8, 100, 5, 200)
    pygame.draw.rect(b, FP.MIDNIGHT, track, border_radius=3)
    thumb_h = max(20, int(track.h * 10 / 40))
    thumb_y = track.y + int((track.h - thumb_h) * (3 / 30))
    pygame.draw.rect(b, FP.GOLD_DARK, (track.x, thumb_y, track.w, thumb_h), border_radius=3)
    pr = pygame.Rect(20, 340, 300, 10)
    pygame.draw.rect(b, FP.MIDNIGHT, pr, border_radius=4)
    pygame.draw.rect(b, FP.ARCANE_BRIGHT, (20, 340, 120, 10), border_radius=4)
    pygame.draw.rect(b, FP.ARCANE_DIM, pr, 1, border_radius=4)
    h._ui_blit_text('40 %', get_font('small', 12), FP.BODY_TEXT, pr.centerx, pr.y - 2,
                    align='center')
    assert _bytes(a) == _bytes(b)


# =============================================================================
# A full synthetic kit through the real screens
# =============================================================================

def _full_kit_dir(tmp_path):
    """Every piece the game asks for, as a small 4-px-border nine-slice."""
    manifest = {'version': 1, 'scale': 1, 'pieces': {}}
    for i, name in enumerate(ui_theme.PIECES):
        img = pygame.Surface((12, 12), pygame.SRCALPHA)
        img.fill((30 + i * 9, 20, 60, 255))
        pygame.draw.rect(img, (200, 150 + i * 4, 40, 255), (0, 0, 12, 12), 4)
        pygame.image.save(img, str(tmp_path / f'{name}.png'))
        spec = {'file': f'{name}.png', 'slice': [4, 4, 4, 4]}
        if name == 'divider':
            spec['slice'] = [4, 0, 4, 0]
        if name in ('quiz', 'panel'):
            acc = pygame.Surface((12, 12), pygame.SRCALPHA)
            acc.fill((0, 0, 0, 0))
            acc.fill((255, 255, 255, 255), (5, 0, 2, 2))
            pygame.image.save(acc, str(tmp_path / f'{name}_accent.png'))
            spec['accent'] = f'{name}_accent.png'
        manifest['pieces'][name] = spec
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    return tmp_path


def _load_capture():
    import importlib.util
    if 'pq_ui_capture' in sys.modules:
        return sys.modules['pq_ui_capture']
    spec = importlib.util.spec_from_file_location(
        'pq_ui_capture', _ROOT / 'tools' / 'ui' / 'capture.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['pq_ui_capture'] = mod
    spec.loader.exec_module(mod)
    return mod


def test_key_screens_draw_with_a_full_kit_and_the_quiz_never_loads_art(tmp_path, monkeypatch):
    cap = _load_capture()
    monkeypatch.setattr(ui_theme, 'ASSET_DIR', str(_full_kit_dir(tmp_path)))
    key = [s for s in cap.SCENES if s.key]
    with cap.harness():
        assert set(ui_theme.loaded_names()) == set(ui_theme.PIECES), ui_theme.kit().errors
        for sc in key:
            surf, _ = cap.render_scene(sc, (1280, 720))
            assert not cap.is_blank(surf), sc.name
            assert not surf.text_outside(), sc.name
        # A warm quiz frame: no image load, no rescale (they would come off
        # the combat timer; FOUNDATION_REVIEW 2.5).
        sc = next(s for s in cap.SCENES if s.name == 'quiz_chain_combat')
        screen = cap.make_screen((1280, 720))
        g = cap.build_game(screen, (1280, 720))
        sc.setup(g)
        g.render()
        for mod, name in ((pygame.image, 'load'), (pygame.transform, 'smoothscale'),
                          (pygame.transform, 'scale')):
            monkeypatch.setattr(mod, name, lambda *a, **k: pytest.fail('art loaded in a draw'))
        g.quiz_engine.current_question = dict(g.quiz_engine.current_question,
                                              question='7 x 8 = ?')   # new height
        g.render()
        g.render()


def test_capture_harness_restores_the_kit_and_window(tmp_path, monkeypatch):
    """GROUNDWORK_REVIEW 9: the harness loaded assets/ui/ and resized the
    window and left both behind, so once real art lands every test that ran
    after it would draw WITH art (order-dependent tests)."""
    cap = _load_capture()
    sentinel = ui_theme.Kit()
    monkeypatch.setattr(ui_theme, '_kit', sentinel)
    monkeypatch.setattr(ui_theme, 'ASSET_DIR', str(_full_kit_dir(tmp_path)))
    pygame.display.set_mode((321, 123))
    try:
        with cap.harness():
            assert set(ui_theme.loaded_names()) == set(ui_theme.PIECES)   # art inside
        assert ui_theme._kit is sentinel, "the harness must put the caller's kit back"
        assert ui_theme.loaded_names() == set()
        assert pygame.display.get_surface().get_size() == (321, 123)
        # Also when the body raises.
        with pytest.raises(RuntimeError):
            with cap.harness():
                raise RuntimeError('boom')
        assert ui_theme._kit is sentinel
    finally:
        pygame.display.set_mode((64, 64))
