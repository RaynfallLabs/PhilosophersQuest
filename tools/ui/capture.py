"""Headless screen capture for Philosopher's Quest.

The measuring stick for the UI art pass: every menu and UI screen is drawn by
the game's OWN draw code (``Game.render()``, ``WelcomeScreen._draw`` via its
real ``run`` loop, ``StudyMode`` via its real ``run`` loop) under
``SDL_VIDEODRIVER=dummy`` and saved as a PNG, one per screen per window size.

    python tools/ui/capture.py                     # every screen, 4 sizes
    python tools/ui/capture.py --sizes 1600x900    # one size
    python tools/ui/capture.py --only quiz_ equip  # screens whose name contains these
    python tools/ui/capture.py --list              # print the screen list

Output:
    _genart/ui/capture/<W>x<H>/<screen>.png
    _genart/ui/capture/SHEET_<W>x<H>.png          contact sheet, labelled
    _genart/ui/capture/SCREENS.md                 every screen: how reached, captured?

FAITHFUL: screens are reached the way a player reaches them wherever that is
possible -- real key events into ``Game.handle_event`` / the welcome and
study-mode loops, real ``_open_*`` / ``_start_*`` setters otherwise, real
quizzes answered through the real input path. Nothing is drawn by the harness
except the contact sheet.

REPEATABLE: every screen is drawn from a FRESH game built from the same seed.
The harness pins every source of variation it can see, without touching game
code:
  * ``random`` module seed, and every ``random.Random()`` the game creates
    without a seed (dungeon, boss rooms, effects) gets a seed from a fixed
    sequence;
  * ``pygame.time.get_ticks`` is frozen (the death/victory rune circles and
    the death-chase pulse read it);
  * the welcome / study loops get a fake clock with a fixed frame time;
  * save dir, quiz history, bones, high scores, logs all point at a throwaway
    sandbox, with a fixed high-score fixture, so the user's own files are
    never read or written;
  * string hashing: run as a script, the tool re-executes itself with
    ``PYTHONHASHSEED=0`` so set iteration order is the same every run.

TEXT CHECK: fonts are swapped for a ``pygame.font.Font`` subclass that only
remembers which surfaces are text, and the screen is a ``pygame.Surface``
subclass that records where text surfaces are blitted. Pixel output is
identical; the record lets the test assert no text lands outside the window.
(Text composed onto an intermediate surface first is not seen by the check.)
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import argparse          # noqa: E402
import contextlib        # noqa: E402
import copy              # noqa: E402
import json              # noqa: E402
import random            # noqa: E402
import shutil            # noqa: E402
import subprocess        # noqa: E402
import tempfile          # noqa: E402
import time              # noqa: E402
import traceback         # noqa: E402
import weakref           # noqa: E402
from dataclasses import dataclass, field  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'src'
OUT_DIR = ROOT / '_genart' / 'ui' / 'capture'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pygame  # noqa: E402

SEED = 20261015
FROZEN_TICKS_MS = 4_200          # what pygame.time.get_ticks() returns
FAKE_FRAME_MS = 1_700            # one welcome / study frame (sets the anim phase)
PLAYER_NAME = 'Aldric'

SMALL_SIZE = (1280, 720)         # main() holds the window at this minimum
LARGE_SIZE = (1920, 1080)
WIDE_SIZE = (3440, 1440)         # Brandon's monitor (UI scale 1.5)


def default_size() -> tuple[int, int]:
    """The window size main() opens at (layout.py's WINDOW_W x WINDOW_H).

    layout.WINDOW_W/H are mutated by layout.update() at runtime, so the
    module defaults are read from the source once."""
    global _DEFAULT
    if _DEFAULT is None:
        import re
        txt = (SRC / 'layout.py').read_text(encoding='utf-8')
        w = int(re.search(r'^WINDOW_W\s*=\s*(\d+)', txt, re.M).group(1))
        h = int(re.search(r'^WINDOW_H\s*=\s*(\d+)', txt, re.M).group(1))
        _DEFAULT = (w, h)
    return _DEFAULT


_DEFAULT = None


def all_sizes() -> list[tuple[int, int]]:
    return [default_size(), SMALL_SIZE, LARGE_SIZE, WIDE_SIZE]


def size_tag(size) -> str:
    return f"{size[0]}x{size[1]}"


# ---------------------------------------------------------------------------
# Text tracing (pixel-identical subclasses)
# ---------------------------------------------------------------------------

_TEXT = weakref.WeakKeyDictionary()     # text surface -> the string drawn
_TEXT_COLOR = weakref.WeakKeyDictionary()   # text surface -> (rgb, has_bg)
_TEXT_PT = weakref.WeakKeyDictionary()      # text surface -> the font's pixel size


class TracingFont(pygame.font.Font):
    """pygame Font that remembers which surfaces it rendered, and in which
    colour."""

    def render(self, text, *args, **kwargs):
        surf = super().render(text, *args, **kwargs)
        try:
            _TEXT[surf] = str(text)
            try:
                _TEXT_PT[surf] = int(self.point_size)
            except (AttributeError, pygame.error):
                pass
            color = args[1] if len(args) > 1 else kwargs.get('color')
            bg = args[2] if len(args) > 2 else kwargs.get('bgcolor')
            if color is not None:
                _TEXT_COLOR[surf] = (tuple(pygame.Color(color))[:3], bg is not None)
        except (TypeError, ValueError):
            pass
        return surf


def luminance(rgb) -> float:
    """WCAG relative luminance of an sRGB colour (0-255 channels)."""
    def ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast_ratio(a, b) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _lum_array(rgb):
    import numpy as np
    c = rgb.astype(np.float64) / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


class TracingSurface(pygame.Surface):
    """The game screen. Records every text blit's intended rectangle.

    Also records, per text blit (``text_info``, index-aligned with
    ``text_blits``): its colour, the clip in force, and -- when
    ``measure_contrast`` is on -- the contrast ratio between that colour and
    the pixels actually under its glyphs at the moment it was drawn (5th
    percentile over the glyph pixels). ``last_overlay`` is the index of the
    first text blit after the most recent full-window blit (an overlay):
    text before it lies under a dimming wash. ``panels`` lists the panels
    drawn, as (rect, index of the next text blit)."""

    measure_contrast = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_blits: list[tuple[pygame.Rect, str]] = []
        self.text_info: list[dict] = []
        self.panels: list[tuple[pygame.Rect, int]] = []
        self.last_overlay = 0
        self.last_overlay_panel = 0
        self.overlays = 0

    def reset_trace(self):
        self.text_blits.clear()
        self.text_info.clear()
        self.panels.clear()
        self.last_overlay = 0
        self.last_overlay_panel = 0
        self.overlays = 0

    def _contrast_under(self, source, x, y, area, color):
        import numpy as np
        sx0, sy0 = 0, 0
        if area is not None:
            sx0, sy0, w, h = pygame.Rect(area)
        else:
            w, h = source.get_size()
        drawn = pygame.Rect(x, y, w, h).clip(self.get_clip()).clip(self.get_rect())
        if drawn.w <= 0 or drawn.h <= 0:
            return None
        try:
            alpha = pygame.surfarray.array_alpha(source)
        except (ValueError, pygame.error):
            return None
        ox, oy = sx0 + drawn.x - x, sy0 + drawn.y - y
        mask = alpha[ox:ox + drawn.w, oy:oy + drawn.h] >= 160
        if not mask.any():
            return None
        bg = pygame.surfarray.array3d(self.subsurface(drawn))[mask]
        lt = luminance(color)
        lb = _lum_array(bg)
        ratio = (np.maximum(lt, lb) + 0.05) / (np.minimum(lt, lb) + 0.05)
        return float(np.percentile(ratio, 5))

    def _note(self, source, dest, area=None):
        if area is None and source.get_size() == self.get_size():
            self.last_overlay = len(self.text_blits)
            self.last_overlay_panel = len(self.panels)
            self.overlays += 1
            return
        text = _TEXT.get(source)
        if text is None or not text.strip():
            return
        if isinstance(dest, pygame.Rect):
            x, y = dest.x, dest.y
        else:
            x, y = dest[0], dest[1]
        if area is not None:
            a = pygame.Rect(area)
            w, h = a.w, a.h
        else:
            w, h = source.get_size()
        x, y = int(x), int(y)
        color, has_bg = _TEXT_COLOR.get(source, (None, False))
        ink = source.get_bounding_rect()
        if area is not None:
            ink = ink.clip(pygame.Rect(area)).move(-pygame.Rect(area).x, -pygame.Rect(area).y)
        info = {'color': color, 'has_bg': has_bg, 'contrast': None,
                'pt': _TEXT_PT.get(source),
                'clip': pygame.Rect(self.get_clip()),
                # The glyphs' own pixels (no line-box padding), on screen.
                'ink': ink.move(x, y)}
        if self.measure_contrast and color is not None and not has_bg:
            info['contrast'] = self._contrast_under(source, x, y, area, color)
        self.text_blits.append((pygame.Rect(x, y, w, h), text))
        self.text_info.append(info)

    def top_layer(self):
        """(text blits, infos, panels) drawn after the last full-window
        overlay: what the player actually reads on a modal screen."""
        i, j = self.last_overlay, self.last_overlay_panel
        return self.text_blits[i:], self.text_info[i:], self.panels[j:]

    def text_outside_panels(self) -> list[tuple[pygame.Rect, str, pygame.Rect]]:
        """Top-layer text whose ink overlaps a top-layer panel without lying
        inside it (text running over a panel's edge). Clipped text is judged
        by what its clip lets through."""
        blits, infos, panels = self.top_layer()
        out = []
        for (r, t), info in zip(blits, infos):
            vis = info['ink'].clip(info['clip'])
            if vis.w <= 0 or vis.h <= 0:
                continue
            hit = [p for p, _ in panels if p.colliderect(vis)]
            if hit and not any(p.contains(vis) for p in hit):
                out.append((vis, t, hit[-1]))
        return out

    def text_in_no_panel(self) -> list[tuple[pygame.Rect, str]]:
        """On a MODAL screen (a full-window overlay was drawn and at least
        one panel sits on top of it): top-layer text whose ink touches no
        top-layer panel at all -- text pushed wholly below or beside the
        panel it belongs to (the usual failure of a footer hint at the
        minimum window). ``text_outside_panels`` only sees text that
        overlaps a panel edge."""
        if not self.overlays:
            return []
        blits, infos, panels = self.top_layer()
        if not panels:
            return []
        out = []
        for (r, t), info in zip(blits, infos):
            vis = info['ink'].clip(info['clip'])
            if vis.w <= 0 or vis.h <= 0:
                continue
            if not any(p.colliderect(vis) for p, _ in panels):
                out.append((vis, t))
        return out

    def blit(self, source, dest, area=None, special_flags=0):
        self._note(source, dest, area)
        return super().blit(source, dest, area, special_flags)

    def blits(self, blit_sequence, doreturn=True):
        out = []
        for item in blit_sequence:
            out.append(self.blit(*item))
        return out if doreturn else None

    def text_outside(self) -> list[tuple[pygame.Rect, str]]:
        win = self.get_rect()
        return [(r, t) for r, t in self.text_blits
                if r.w > 0 and r.h > 0 and not win.contains(r)]


def _panel_spy(real):
    """Wrap a panel-drawing helper so a TracingSurface records the panel."""
    def spy(surf, rect, *a, **k):
        if isinstance(surf, TracingSurface):
            surf.panels.append((pygame.Rect(rect), len(surf.text_blits)))
        return real(surf, rect, *a, **k)
    spy.__wrapped__ = real
    return spy


# A box drawn as an OUTLINED ``pygame.draw.rect`` at least this big counts as
# a panel for the layout check: the hand-drawn prayer / boon / intercession
# boxes, ``_ui_subpanel``, the decision menu's CHOICES / DETAIL panes and
# rows, answer cards. Smaller outlines (key badges, chips, bar frames) and
# filled rects (backgrounds, bars, highlights) are not panels.
BOX_MIN_W, BOX_MIN_H = 120, 40


def _rect_spy(real):
    """Wrap pygame.draw.rect so an outlined box drawn on a TracingSurface
    is recorded as a panel (``TracingSurface.boxes`` too, for reports)."""
    def spy(surface, color, rect, width=0, *a, **k):
        if isinstance(surface, TracingSurface) and width > 0:
            try:
                r = pygame.Rect(rect)
            except (TypeError, ValueError):
                r = None
            if r is not None and r.w >= BOX_MIN_W and r.h >= BOX_MIN_H:
                surface.panels.append((r, len(surface.text_blits)))
        return real(surface, color, rect, width, *a, **k)
    spy.__wrapped__ = real
    return spy


# Menu icons drawn as a letter glyph (no sprite resolved) since the last
# reset: render_scene clears it per screen.
GLYPH_ICONS: list = []


# ---------------------------------------------------------------------------
# Determinism + sandbox
# ---------------------------------------------------------------------------

class _SeedSource:
    master = random.Random(SEED)


_RealRandom = random.Random


class DetRandom(_RealRandom):
    """random.Random whose no-argument construction is seeded from a fixed
    sequence instead of os.urandom."""

    def __init__(self, x=None):
        if x is None:
            x = _SeedSource.master.getrandbits(64)
        super().__init__(x)


def reseed(seed: int = SEED) -> None:
    random.seed(seed)
    _SeedSource.master = _RealRandom(seed ^ 0x5EED)


class FakeClock:
    """Stands in for pygame.time.Clock in the welcome / study loops."""

    def __init__(self, ms: int = FAKE_FRAME_MS):
        self.ms = ms

    def tick(self, *_a, **_k):
        return self.ms

    def get_fps(self):
        return 60.0


class _FrameDone(Exception):
    """Raised from the patched display.flip to stop a run() loop after one frame."""


_HIGHSCORE_FIXTURE = [
    {'name': 'Hypatia', 'score': 184_220, 'grade': 'A', 'level': 100, 'victory': True,
     'date': '2026-09-30'},
    {'name': 'Boethius', 'score': 92_400, 'grade': 'B', 'level': 61, 'victory': False,
     'date': '2026-09-21'},
    {'name': 'Anselm', 'score': 51_015, 'grade': 'B', 'level': 44, 'victory': False,
     'date': '2026-09-12'},
    {'name': 'Heloise', 'score': 23_870, 'grade': 'C', 'level': 27, 'victory': False,
     'date': '2026-08-30'},
    {'name': 'Alcuin', 'score': 8_410, 'grade': 'D', 'level': 12, 'victory': False,
     'date': '2026-08-14'},
    {'name': 'Bede', 'score': 1_960, 'grade': 'F', 'level': 4, 'victory': False,
     'date': '2026-08-02'},
]


_SANDBOX: Path | None = None


def reset_sandbox() -> None:
    """Put the sandbox back to its fixed starting contents. Called before
    every screen: an ending writes a high score, a quiz writes the
    cross-game question history, and neither may leak into the next shot."""
    tmp = _SANDBOX
    for sub in ('saves', 'quiz_history', 'bones', 'logs'):
        d = tmp / sub
        d.mkdir(exist_ok=True)
        for f in d.rglob('*'):
            if f.is_file():
                try:
                    f.unlink()
                except OSError:
                    # The game log and main.py's faulthandler.log stay open.
                    if f.suffix != '.log':
                        raise
    (tmp / 'highscores.json').write_text(json.dumps(_HIGHSCORE_FIXTURE), encoding='utf-8')
    for f in ('settings.json',):
        try:
            (tmp / f).unlink()
        except FileNotFoundError:
            pass


@contextlib.contextmanager
def harness(trace: bool = True):
    """Patch module globals for a deterministic, sandboxed capture; restore
    everything on exit. Game code is not modified.

    ``trace=False`` leaves pygame's Font class alone (no text tracing), which
    is what the frame-time measurement wants: the game's real fonts drawing
    onto the real display surface."""
    pygame.init()
    tmp = Path(tempfile.mkdtemp(prefix='pq_capture_'))
    saves = tmp / 'saves'
    score_file = tmp / 'highscores.json'
    global _SANDBOX
    _SANDBOX = tmp
    reset_sandbox()

    import paths
    import fantasy_ui
    import quiz_engine
    import highscore_system
    import save_system
    import bones
    import game_log
    import sound_system

    restore: list[tuple[object, str, object]] = []

    def patch(obj, attr, value):
        restore.append((obj, attr, getattr(obj, attr)))
        setattr(obj, attr, value)

    import ui_theme
    import layout
    saved_kit = ui_theme.save_state()
    saved_layout = layout.snapshot()      # window size + UI scale
    _disp = pygame.display.get_surface() if pygame.display.get_init() else None
    saved_display = _disp.get_size() if _disp is not None else None
    saved_env = {k: os.environ.get(k) for k in ('PQ_NO_BONES',)}
    os.environ['PQ_NO_BONES'] = '1'
    saved_font_cache = dict(fantasy_ui._font_cache)
    try:
        patch(paths, 'save_dir', lambda: str(saves))
        patch(save_system, 'save_dir', lambda: str(saves))
        patch(bones, '_bones_dir', lambda: str(tmp / 'bones'))
        patch(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp / 'quiz_history'))
        patch(highscore_system, '_SCORE_FILE', str(score_file))
        patch(game_log, '_LOG_DIR', str(tmp / 'logs'))
        if hasattr(sound_system, '_settings_path'):
            patch(sound_system, '_settings_path', lambda: str(tmp / 'settings.json'))
        patch(random, 'Random', DetRandom)
        patch(pygame.time, 'get_ticks', lambda: FROZEN_TICKS_MS)
        if trace:
            patch(pygame.font, 'Font', TracingFont)
            patch(pygame.sysfont, 'Font', TracingFont)
            import game_render
            import welcome_screen
            for mod in (fantasy_ui, game_render, welcome_screen):
                for fn in ('draw_dark_panel', 'draw_panel'):
                    if hasattr(mod, fn):
                        patch(mod, fn, _panel_spy(getattr(mod, fn)))
            patch(pygame.draw, 'rect', _rect_spy(pygame.draw.rect))
            # Item art is the item: count every menu icon drawn as a letter
            # glyph because no sprite resolved (tests/test_ui_gates.py).
            real_icon = game_render.RenderMixin._draw_menu_icon

            def icon_spy(self_, item, x, y, _real=real_icon):
                if self_._get_menu_sprite(getattr(item, 'id', '')) is None:
                    GLYPH_ICONS.append(getattr(item, 'id', '?'))
                return _real(self_, item, x, y)
            patch(game_render.RenderMixin, '_draw_menu_icon', icon_spy)
        fantasy_ui._font_cache.clear()
        # As main() does right after creating the window: load the UI art
        # kit (assets/ui/) once, up front. The caller's kit and window size
        # are put back on exit, so a test that runs after the harness draws
        # with whatever kit it had before (GROUNDWORK_REVIEW 9).
        pygame.display.set_mode(default_size())
        ui_theme.load()
        yield tmp
    finally:
        layout.restore(saved_layout)
        ui_theme.restore_state(saved_kit)
        if saved_display is not None:
            try:
                pygame.display.set_mode(saved_display)
            except pygame.error:
                pass
        for obj, attr, old in reversed(restore):
            setattr(obj, attr, old)
        fantasy_ui._font_cache.clear()
        fantasy_ui._font_cache.update(saved_font_cache)
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)


def make_screen(size, trace: bool = True):
    """The surface the game draws on. Traced: a TracingSurface (records text
    blits). Untraced: the real display surface, as in play."""
    display = pygame.display.set_mode(size)
    import layout
    layout.update(*size)
    if not trace:
        display.fill((0, 0, 0))
        return display
    surf = TracingSurface(size)
    surf.fill((0, 0, 0))
    return surf


# ---------------------------------------------------------------------------
# Input helpers (the game's real input path)
# ---------------------------------------------------------------------------

def key_event(key, unicode='', mod=0):
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode, mod=mod,
                              scancode=0)


def press(g, key, unicode=''):
    """One key press through Game.handle_event."""
    g.handle_event(key_event(key, unicode))


def type_text(g, text):
    for ch in text:
        press(g, pygame.key.key_code(ch) if ch.isalnum() else 0, ch)


def _correct_slot(qe) -> int | None:
    """Displayed position (0-3) of the right answer to the current question."""
    q = qe.current_question
    if not q:
        return None
    choices = q.get('choices', [])
    want = str(q.get('answer', '')).strip()
    order = qe.confused_order if (qe.confused_order and
                                  len(qe.confused_order) == len(choices)) else range(len(choices))
    for pos, actual in enumerate(order):
        if str(choices[actual]).strip() == want:
            return pos
    return None


_NUM_KEYS = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)


def answer(g, correct: bool):
    """Answer the quiz question on screen with a real number-key press."""
    from quiz_engine import QuizState
    qe = g.quiz_engine
    assert qe.state == QuizState.ASKING, f"quiz not asking (state={qe.state})"
    slot = _correct_slot(qe)
    if not correct:
        n = len(qe.current_question.get('choices', []))
        slot = next(i for i in range(n) if i != slot)
    press(g, _NUM_KEYS[slot])


def settle_quiz(g, max_steps=40):
    """Let a quiz's result flash run out (Game.update with a fixed dt) until
    it is asking again or has finished."""
    from quiz_engine import QuizState
    for _ in range(max_steps):
        if g.quiz_engine.state != QuizState.RESULT:
            return
        g.update(0.25)


def play_quiz(g, pattern: str):
    """Answer a sequence: 'c' = correct, 'w' = wrong, settling between."""
    from quiz_engine import QuizState
    for ch in pattern:
        if g.quiz_engine.state != QuizState.ASKING:
            break
        answer(g, ch == 'c')
        settle_quiz(g)


# ---------------------------------------------------------------------------
# The representative game
# ---------------------------------------------------------------------------

def _monster_defs() -> dict:
    from paths import data_path
    with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
        return json.load(f)


def _free_tiles_near(g, radius_min=1, radius_max=3):
    from geom import all_occupied_tiles
    occ = all_occupied_tiles(g.monsters)
    occ.add((g.player.x, g.player.y))
    occ |= {(p.x, p.y) for p in g.pets}
    occ |= {(i.x, i.y) for i in g.ground_items if hasattr(i, 'x')}
    px, py = g.player.x, g.player.y
    out = []
    for r in range(radius_min, radius_max + 1):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                x, y = px + dx, py + dy
                if (x, y) not in occ and g.dungeon.is_walkable(x, y):
                    out.append((x, y))
    return out


def _stock_inventory(g):
    from items import (load_items, Corpse, pick_random_weapon_for_floor,
                       pick_random_armor_for_floor, pick_random_shield_for_floor)
    p = g.player
    rng = random.Random(SEED)
    stock = []
    for cls, n in (('potion', 3), ('scroll', 3), ('wand', 2), ('spellbook', 2),
                   ('food', 3), ('accessory', 3), ('ammo', 1), ('ingredient', 3)):
        try:
            stock += load_items(cls)[:n]
        except Exception:
            pass
    for maker in (pick_random_weapon_for_floor, pick_random_shield_for_floor):
        item = maker(5, rng)
        if item is not None:
            stock.append(item)
    for floor, slot in ((5, 'body'), (5, 'head'), (30, 'body')):
        try:
            armor = pick_random_armor_for_floor(floor, rng, slot=slot)
        except Exception:
            armor = None
        if armor is not None:
            stock.append(armor)
    for it in stock:
        inst = copy.copy(it)
        if hasattr(g, 'apply_appearance'):
            try:
                g.apply_appearance(inst)
            except Exception:
                pass
        p.inventory.append(inst)
    # A stack, so "drop how many?" has something to ask about.
    for it in p.inventory:
        if getattr(it, 'item_class', '') in ('potion', 'food', 'ammo'):
            it.count = max(getattr(it, 'count', 1), 3)
            break
    # Wear the kit: the same two calls an equip quiz's success makes.
    from items import Weapon, Armor, Shield, Accessory
    worn = []
    for kind in (Weapon, Shield, Accessory):
        it = next((i for i in p.inventory if isinstance(i, kind)), None)
        if it is not None:
            worn.append(it)
    armors = [i for i in p.inventory if isinstance(i, Armor)]
    worn += armors[:-1]          # keep the last (heaviest, floor-30) in the pack
    for it in worn:
        try:
            p._apply_equip(it)
            p.remove_from_inventory(it)
        except Exception:
            pass
    corpse = Corpse('giant rat', 'giant_rat', p.x, p.y)
    p.inventory.append(corpse)
    g._capture_corpse = corpse


def _add_pet(g):
    from pet_system import Pet
    spots = _free_tiles_near(g, 1, 2)
    if not spots:
        return None
    x, y = spots[-1]
    pet = Pet('electric', x, y)
    pet.nickname = 'Sparky'
    # A companion that has evolved once (Voltpaw), so it has a special.
    for _ in range(2000):
        if pet.stage >= 1:
            break
        pet.gain_xp(25)
    g.pets.append(pet)
    return pet


def _add_monster(g, kind_pref=('goblin', 'kobold', 'giant_rat', 'jackal')):
    from monster import Monster
    defs = _monster_defs()
    kind = next((k for k in kind_pref if k in defs), next(iter(defs)))
    spots = _free_tiles_near(g, 2, 3)
    if not spots:
        return None
    x, y = spots[0]
    m = Monster({**defs[kind], 'id': kind}, x, y)
    g.monsters.append(m)
    return m


def _quiz_history(g):
    """Give the run a real answer history: questions drawn and answered by the
    real QuizEngine, recorded by the game's own on_answer hook (missed-question
    list, per-subject stats for Discoveries / study journal)."""
    qe = g.quiz_engine
    for subject, pattern in (('history', 'cw'), ('geography', 'wc'),
                             ('science', 'cwc'), ('philosophy', 'w'),
                             ('math', 'ccw')):
        qe.start_quiz(mode='threshold', subject=subject, tier=2,
                      callback=lambda _r: None, threshold=len(pattern),
                      total_qs=len(pattern), timed=False)
        for ch in pattern:
            from quiz_engine import QuizState
            if qe.state != QuizState.ASKING:
                break
            q = qe.current_question
            right = str(q.get('answer', ''))
            wrong = next(c for c in q.get('choices', []) if str(c).strip() != right.strip())
            qe.answer(right if ch == 'c' else wrong)
            qe.update(10.0)
        if qe.state != QuizState.COMPLETE:
            qe._end(success=False)


def _explore_around(g, steps=45):
    """Mid-floor, not first-step: mark as explored every walkable tile within
    `steps` moves of the hero, plus the walls touching them -- the set that
    walking those corridors would have added to dungeon.explored."""
    from collections import deque
    d = g.dungeon
    start = (g.player.x, g.player.y)
    seen = {start: 0}
    q = deque([start])
    while q:
        x, y = q.popleft()
        if seen[(x, y)] >= steps:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and 0 <= n[0] < d.width and 0 <= n[1] < d.height \
                    and d.is_walkable(*n):
                seen[n] = seen[(x, y)] + 1
                q.append(n)
    for (x, y) in seen:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < d.width and 0 <= ny < d.height:
                    d.explored.add((nx, ny))


_LOG_LINES = [
    ("You descend into the Labyrinth of Echoes.", 'info'),
    ("You hear the clatter of claws on stone.", 'warning'),
    ("You strike the goblin! (x3 chain) It staggers.", 'success'),
    ("The goblin hits you for 4 damage.", 'danger'),
    ("You find 37 gold pieces.", 'loot'),
    ("Sparky crackles and bites the goblin.", 'info'),
    ("You feel quick on your feet.", 'success'),
    ("You feel sick. The wound burns with poison.", 'danger'),
    ("You read the scroll. The words rearrange themselves.", 'info'),
    ("A cold draught blows from the stairs below.", 'warning'),
]


def build_game(screen, size):
    """A fresh, fully deterministic mid-game Game on `screen`."""
    import items
    import layout
    from main import Game
    import game_states as S
    reseed()
    layout.update(*size)
    items.bind_unique_registry(set())
    g = Game(screen, player_name=PLAYER_NAME)
    g.on_resize(*size)
    # on_resize arms a short quiz-clock grace (a player's resize must not
    # cost quiz seconds). This resize is setup, not play: scenes that advance
    # the clock with g.update() must see real time.
    g._resize_grace = 0
    p = g.player
    _stock_inventory(g)
    try:
        from spells import LEARNABLE_SPELLS
        for sid in list(LEARNABLE_SPELLS)[:3]:
            p.known_spells[sid] = LEARNABLE_SPELLS[sid]['mp_cost']
    except Exception:
        pass
    g.player_gold = 1_234
    # Earned traits: one passive and three active powers, initialised the
    # way QuirkSystem._award_power initialises them (minus the popup).
    from quirk_system import _ACTIVE_POWER_DEFS
    p.unlocked_quirks = set(getattr(p, 'unlocked_quirks', set()) or set())
    p.power_uses = dict(getattr(p, 'power_uses', {}) or {})
    p.power_cooldowns = dict(getattr(p, 'power_cooldowns', {}) or {})
    for qid in ('odin', 'metabolic', 'zeus_bolt', 'phoenix_rising'):
        p.unlocked_quirks.add(qid)
        pdef = _ACTIVE_POWER_DEFS.get(qid, {})
        if pdef.get('uses', 0) > 0:
            p.power_uses[qid] = pdef['uses']
        if pdef.get('cooldown', 0) > 0:
            p.power_cooldowns[qid] = 0
    g.turn_count = 412
    for name, dur in (('hasted', 40), ('poisoned', 12), ('see_invisible', 200),
                      ('empowered', 5)):
        p.add_effect(name, dur)
    _add_pet(g)
    g._capture_monster = _add_monster(g)
    _quiz_history(g)
    for text, kind in _LOG_LINES:
        g.add_message(text, kind)
    _explore_around(g, steps=45)
    g._refresh_fov()
    # The game opens on the dungeon-entrance story popup; dismiss it the way
    # the player does (Escape returns to popup_next_state).
    if g.state == S.STATE_STORY_POPUP:
        press(g, pygame.K_ESCAPE)
    return g


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------

@dataclass
class Scene:
    name: str
    group: str
    reach: str
    setup: object                  # callable
    kind: str = 'game'             # 'game' | 'welcome' | 'study'
    expect_state: str | None = None
    notes: str = ''
    key: bool = False              # part of the fast key-screen test


SCENES: list[Scene] = []


def scene(name, group, reach, *, kind='game', expect=None, notes='', key=False):
    def deco(fn):
        SCENES.append(Scene(name, group, reach, fn, kind, expect, notes, key))
        return fn
    return deco


def _S():
    import game_states as S
    return S


# -- Welcome / title ---------------------------------------------------------

def run_welcome_frame(screen, keys=(), notice=None, save_for=None):
    """Drive the REAL WelcomeScreen.run loop for one frame: post key events,
    let it handle them, and stop at its first display.flip()."""
    import layout
    from welcome_screen import WelcomeScreen
    if save_for:
        from save_system import _save_path
        Path(_save_path(save_for)).write_bytes(b'capture-fixture')
    w = WelcomeScreen(screen, layout.VERSION, notice=notice)
    _post_keys(keys)
    _run_one_frame(lambda: w.run(FakeClock()))
    return w


def _post_keys(keys):
    pygame.event.clear()
    for k in keys:
        if isinstance(k, str):
            code = pygame.key.key_code(k) if len(k) == 1 and k.isalnum() else 0
            pygame.event.post(key_event(code, k))
        else:
            pygame.event.post(key_event(k))


def _run_one_frame(fn):
    real_flip = pygame.display.flip

    def flip(*_a, **_k):
        raise _FrameDone

    pygame.display.flip = flip
    try:
        fn()
    except _FrameDone:
        pass
    else:
        raise RuntimeError("loop returned before drawing a frame")
    finally:
        pygame.display.flip = real_flip


@scene('title_welcome', 'Title', 'Launch the game: the welcome screen (high-score fixture loaded).',
       kind='welcome', key=True)
def _(screen):
    return run_welcome_frame(screen)


@scene('title_name_typed', 'Title', 'Welcome screen, type a name.', kind='welcome')
def _(screen):
    return run_welcome_frame(screen, keys=list(PLAYER_NAME))


@scene('title_secret_build', 'Title', 'Welcome screen, type a secret-build name (Corwin) -- badge appears.',
       kind='welcome')
def _(screen):
    return run_welcome_frame(screen, keys=list('Corwin'))


@scene('title_save_found', 'Title', 'Welcome screen, type the name of a hero with a saved journey.',
       kind='welcome')
def _(screen):
    return run_welcome_frame(screen, keys=list(PLAYER_NAME), save_for=PLAYER_NAME)


@scene('title_load_notice', 'Title', 'Welcome screen after a save failed to load (one-shot notice).',
       kind='welcome')
def _(screen):
    return run_welcome_frame(screen, notice=("That saved journey could not be restored. It has "
                                      "been kept as save_hero.pkl.unreadable-20261016-120000 "
                                      "and was not overwritten."))


@scene('title_alltime_scores', 'Title', 'Welcome screen, F2: all-time top 100.', kind='welcome')
def _(screen):
    return run_welcome_frame(screen, keys=[pygame.K_F2])


@scene('title_god_prompt', 'Title', "Welcome screen, type 'god' + Enter: \"Did you mean, 'Dad'?\"",
       kind='welcome')
def _(screen):
    return run_welcome_frame(screen, keys=list('god') + [pygame.K_RETURN])


# -- Study mode (from the title, F3) -----------------------------------------

def run_study_frame(screen, keys):
    from study_mode import StudyMode
    s = StudyMode(screen)
    _post_keys(keys)
    _run_one_frame(lambda: s.run(FakeClock()))
    return s


@scene('study_subjects', 'Study mode', 'Title, F3: study mode subject picker.', kind='study')
def _(screen):
    return run_study_frame(screen, [pygame.K_DOWN, pygame.K_DOWN])


@scene('study_tiers', 'Study mode', 'Study mode: pick History, Enter -> tier picker.', kind='study')
def _(screen):
    return run_study_frame(screen, [pygame.K_DOWN, pygame.K_DOWN, pygame.K_RETURN, pygame.K_DOWN])


@scene('study_question', 'Study mode', 'Study mode: History, Tier 2, Enter -> a question.',
       kind='study', key=True)
def _(screen):
    return run_study_frame(screen, [pygame.K_DOWN, pygame.K_DOWN, pygame.K_RETURN,
                             pygame.K_DOWN, pygame.K_RETURN])


def _study_answer_frame(screen, correct):
    from study_mode import StudyMode
    s = StudyMode(screen)
    _post_keys([pygame.K_DOWN, pygame.K_DOWN, pygame.K_RETURN, pygame.K_DOWN, pygame.K_RETURN])
    _run_one_frame(lambda: s.run(FakeClock()))
    q = s._questions[s._idx]
    choices = q.get('choices', [])
    want = str(q.get('answer', '')).strip()
    right = next(i for i, c in enumerate(choices) if str(c).strip() == want)
    pick = right if correct else (right + 1) % len(choices)
    _post_keys([(pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)[pick]])
    _run_one_frame(lambda: s.run(FakeClock()))
    return s


@scene('study_result_correct', 'Study mode', 'Study mode: answer a question correctly.', kind='study')
def _(screen):
    return _study_answer_frame(screen, True)


@scene('study_result_wrong', 'Study mode', 'Study mode: answer a question wrongly (shows the answer + context).',
       kind='study')
def _(screen):
    return _study_answer_frame(screen, False)


# -- Main play view ------------------------------------------------------------

@scene('play_main', 'Play', 'In a game: the map, left sidebar, right rail and message log.',
       expect='player', key=True)
def _(g):
    pass


@scene('play_zoom_medium', 'Play', 'In a game, Tab once: medium zoom.', expect='player')
def _(g):
    press(g, pygame.K_TAB)


@scene('play_zoom_close', 'Play', 'In a game, Tab twice: close-up zoom.', expect='player')
def _(g):
    press(g, pygame.K_TAB)
    press(g, pygame.K_TAB)


@scene('play_target_melee', 'Play', 'A: melee targeting cursor on the nearby monster.',
       expect='target')
def _(g):
    m = g._capture_monster
    # Melee targeting wants an adjacent foe: let it close in to the player.
    if m is not None:
        spots = [(x, y) for (x, y) in _free_tiles_near(g, 1, 1)]
        if spots:
            m.x, m.y = spots[0]
            g._refresh_fov()
    press(g, pygame.K_a)


@scene('play_target_observe', 'Play', 'O: observe cursor (look at a monster).', expect='target')
def _(g):
    press(g, pygame.K_o)


@scene('play_death_chase', 'Play', 'Ascending with the Stone, Death pursues: red vignette on the map.',
       expect='player', notes='The real _trigger_death_pursuit(), then Death placed two tiles away '
                              '(the L100 Stone climb is not reachable from floor 1).')
def _(g):
    # The game's own trigger (it used to set only ``death_pursues``: with no
    # DeathMonster the vignette never drew and the shot equalled play_main).
    g._trigger_death_pursuit()
    dm = g.death_monster
    x, y = _free_tiles_near(g, 2, 2)[0]
    dm.x, dm.y = x, y
    dm.alive = True
    dm._arrive_in = 0
    g._refresh_fov()


@scene('play_debug_overlay', 'Play', 'F2 with PQ_QA_MODE set: developer debug overlay.',
       expect='player', notes='Developer-only.')
def _(g):
    os.environ['PQ_QA_MODE'] = '1'
    try:
        press(g, pygame.K_F2)
    finally:
        os.environ.pop('PQ_QA_MODE', None)


# -- Popups ---------------------------------------------------------------------

@scene('popup_story_entrance', 'Popups', 'New game: the dungeon-entrance story popup.',
       expect='story_popup', key=True)
def _(g):
    g._show_story_popup('dungeon_entrance')


@scene('popup_story_boss', 'Popups', 'Kill a gate boss (Fafnir): boss story popup.', expect='story_popup')
def _(g):
    g._show_story_popup('boss_fafnir')


@scene('popup_story_exit_stone', 'Popups', 'Leave the dungeon with the Stone: ending story popup.',
       expect='story_popup')
def _(g):
    g._show_story_popup('exit_with_stone', _S().STATE_VICTORY)


@scene('popup_trait_unlocked', 'Popups', "Earn a quirk (Odin's Vigil): TRAIT UNLOCKED popup.",
       expect='story_popup')
def _(g):
    import quirk_system as Q
    from quirk_text import quirk_description
    qid = 'odin'
    g._show_quirk_unlock_popup(Q._QUIRK_NAMES[qid],
                               quirk_description(qid) or Q._QUIRK_EFFECTS.get(qid, ''),
                               Q._QUIRK_TRIGGER.get(qid, ''), Q._QUIRK_FLAVOR.get(qid, ''))


@scene('popup_load_summary', 'Popups', 'Load a saved game: the welcome-back summary popup.',
       expect='story_popup')
def _(g):
    g._show_load_summary_popup()


@scene('popup_confirm_exit', 'Popups', 'Esc in play (or the window X): save & quit dialog.',
       expect='confirm_exit', key=True)
def _(g):
    press(g, pygame.K_ESCAPE)


@scene('popup_exit_quest', 'Popups', 'Climb the L1 up-stairs carrying the Stone: complete your quest?',
       expect='exit_quest')
def _(g):
    g.state = _S().STATE_EXIT_QUEST


@scene('popup_abandon_quest', 'Popups', 'Climb the L1 up-stairs without the Stone: abandon your quest?',
       expect='abandon_quest')
def _(g):
    g.state = _S().STATE_ABANDON_QUEST


@scene('popup_chicken', 'Popups', 'Confirm abandoning: the McFly "chicken" popup.', expect='chicken')
def _(g):
    g.state = _S().STATE_CHICKEN


@scene('popup_xyzzy_input', 'Popups', 'Backquote: the hidden green terminal, word typed.',
       expect='xyzzy_input')
def _(g):
    press(g, pygame.K_BACKQUOTE)
    type_text(g, 'xyz')


@scene('popup_xyzzy_confirm', 'Popups', 'Backquote, type xyzzy, Enter: "Hack reality?" warning.',
       expect='xyzzy_confirm')
def _(g):
    press(g, pygame.K_BACKQUOTE)
    type_text(g, 'xyzzy')
    press(g, pygame.K_RETURN)


@scene('popup_drop_gold', 'Popups', 'D, pick "Drop Gold": how much gold?', expect='drop_gold_input')
def _(g):
    g._open_drop_menu()
    press(g, pygame.K_RETURN)        # first row is the gold entry
    type_text(g, '250')


@scene('popup_drop_qty', 'Popups', 'D, pick a stacked item: how many?', expect='drop_qty_input')
def _(g):
    stack = next(i for i in g.player.inventory if getattr(i, 'count', 1) > 1)
    g._do_drop_item(stack)
    type_text(g, '2')


@scene('popup_pet_name', 'Popups', 'A Soul Sphere hatches: name your companion.',
       expect='pet_name_input', notes='Hatch state set the way _throw_soul_sphere sets it.')
def _(g):
    pet = g.pets[0]
    g._naming_pet = pet
    g._pet_name_input_buffer = pet.species_name
    g.state = _S().STATE_PET_NAME_INPUT


@scene('popup_intercession', 'Popups', 'Shift+\\: Divine Intercession Y/N prompt.',
       expect='intercession_prompt')
def _(g):
    g._start_divine_intercession()


# -- Inventory / equip / use menus ----------------------------------------------

for _name, _key, _uni, _state, _desc, _iskey in (
    ('menu_equip', pygame.K_e, 'e', 'equip_menu', 'E: equip / unequip.', True),
    ('menu_kit', pygame.K_k, 'k', 'kit', 'K: kit panel (everything carried, by kind).', False),
    ('menu_discoveries', pygame.K_j, 'j', 'discoveries', 'J: discoveries / quiz stats.', False),
    ('menu_wand', pygame.K_z, 'z', 'wand_menu', 'Z: zap a wand.', False),
    ('menu_spell', pygame.K_m, 'm', 'spell_menu', 'M: cast a spell.', False),
    ('menu_scroll', pygame.K_r, 'r', 'scroll_menu', 'R: read a scroll / spellbook.', False),
    ('menu_identify', pygame.K_i, 'i', 'identify_menu', 'I: identify an item.', True),
    ('menu_cook', pygame.K_c, 'c', 'cook_menu', 'C: cook.', False),
    ('menu_eat', pygame.K_u, 'u', 'eat_menu', 'U: eat.', False),
    ('menu_quaff', pygame.K_q, 'q', 'quaff_menu', 'Q: quaff a potion.', False),
    ('menu_throw', pygame.K_t, 't', 'throw_menu', 'T: throw.', False),
    ('menu_examine', pygame.K_x, 'x', 'examine', 'X: examine an identified item.', False),
    ('menu_powers', pygame.K_v, 'v', 'power_menu', 'V: active powers.', False),
    ('menu_quirks', pygame.K_w, 'w', 'quirks', 'W: quirks / traits browser.', False),
    ('menu_encyclopedia', pygame.K_b, 'b', 'encyclopedia', 'B: encyclopedia.', False),
    ('menu_study_journal', pygame.K_SEMICOLON, ';', 'study', '; : study journal of missed questions.', False),
    ('menu_help', pygame.K_SLASH, '?', 'help', '? : help.', True),
    ('menu_message_log', pygame.K_l, 'l', 'message_log', 'L: message history (scroll-back log).', True),
):
    def _mk(key=_key, uni=_uni):
        def _setup(g):
            press(g, key, uni)
        return _setup
    SCENES.append(Scene(_name, 'Menus', _desc, _mk(), 'game', _state, '', _iskey))


@scene('menu_drop', 'Menus', 'D (off an altar/fountain): drop.', expect='drop_menu')
def _(g):
    g._open_drop_menu()


@scene('menu_charsheet', 'Menus', '@ : character sheet.', expect='character_sheet', key=True)
def _(g):
    g.handle_event(key_event(pygame.K_2, '@', pygame.KMOD_SHIFT))


def _make_burdened(g):
    """Spare mail shirts in the pack until past 75% of the limit (worn gear
    counts, 2026-10-16). The game's own per-turn check says so in the log."""
    from items import instantiate_armor
    p = g.player
    while not p.is_burdened():
        suit = instantiate_armor('chain_shirt', 'chain_steel')
        suit.buc_known, suit.id_level = True, 5
        if not p.can_carry(suit.weight):
            p.inventory.append(instantiate_armor('padded_shirt', 'linen'))
            continue
        p.add_to_inventory(suit)
    g._note_burden()


@scene('play_burdened', 'Play', 'In a game, carrying past 75% of the limit: Burdened '
       '(amber Carrying line, EFFECTS chip, log message).', expect='player')
def _(g):
    _make_burdened(g)


@scene('menu_charsheet_burdened', 'Menus', '@ while Burdened: header, Kit Summary and '
       'effect chip show it.', expect='character_sheet')
def _(g):
    _make_burdened(g)
    g.handle_event(key_event(pygame.K_2, '@', pygame.KMOD_SHIFT))


@scene('menu_kit_result', 'Menus',
       'K, Armor, E on the pack armor, pass the geography quiz: back on the Kit '
       'with the item worn and the result shown.', expect='kit')
def _(g):
    from items import Armor
    press(g, pygame.K_k)
    g._kit_tab = [t[1] for t in g._KIT_TABS].index('armor')
    rows = g._kit_rows_for_slug('armor')
    g._kit_sel = next(i for i, (src, it) in enumerate(rows)
                      if src == 'pack' and isinstance(it, Armor))
    press(g, pygame.K_e)
    play_quiz(g, 'cccccccc')


@scene('menu_charsheet_cursed', 'Menus',
       '@, Body: a worn armor known to be cursed (Unequip and Drop greyed, '
       'with the reason).', expect='character_sheet')
def _(g):
    from items import ARMOR_SLOTS
    body = g.player.armor_slots[ARMOR_SLOTS.index('body')]
    body.cursed, body.buc, body.buc_known = True, 'cursed', True
    g.handle_event(key_event(pygame.K_2, '@', pygame.KMOD_SHIFT))
    g._charsheet_loadout_idx = next(i for i, e in enumerate(g._charsheet_loadout_entries())
                                    if e['item'] is body)


@scene('menu_equip_tab2', 'Menus', 'E, Right: second equip tab.', expect='equip_menu')
def _(g):
    press(g, pygame.K_e)
    press(g, pygame.K_RIGHT)


@scene('menu_encyclopedia_entry', 'Menus',
       'B, Enter into the Bestiary, Enter on an entry (creatures met on the way down).',
       expect='encyclopedia')
def _(g):
    # The creatures a player has met by turn 412 (combat adds each kind it
    # sees to known_monster_ids); without them the Bestiary is empty.
    g.player.known_monster_ids.update(('giant_rat', 'goblin', 'jackal', 'kobold'))
    press(g, pygame.K_b)
    press(g, pygame.K_RETURN)
    press(g, pygame.K_RETURN)


@scene('menu_encyclopedia_weapon', 'Menus',
       'B, b: the Armory, Enter on an entry (weapons the player has learned).',
       expect='encyclopedia')
def _(g):
    g.player.known_item_ids.update(('excalibur', 'venomfang'))
    press(g, pygame.K_b)
    press(g, pygame.K_b, 'b')
    press(g, pygame.K_RETURN)


@scene('menu_pet', 'Pets', 'Shift+P: pet roster and actions.', expect='pet_menu')
def _(g):
    g.handle_event(key_event(pygame.K_p, 'P', pygame.KMOD_SHIFT))


@scene('menu_pet_feed', 'Pets', 'Shift+P, feed: pick a food.', expect='pet_feed')
def _(g):
    g._open_pet_menu()
    g._pet_open_feed(g._pet_menu_selected_pet())


@scene('menu_pet_heal', 'Pets', 'Shift+P, heal: pick a potion.', expect='pet_heal')
def _(g):
    g._open_pet_menu()
    g._pet_open_heal(g._pet_menu_selected_pet())


@scene('menu_pet_specials', 'Pets', 'Shift+P, specials: pick an unlocked special.', expect='pet_specials')
def _(g):
    g._open_pet_menu()
    g._pet_open_specials(g._pet_menu_selected_pet())


@scene('menu_prayer', 'Prayer', '\\ : choose a prayer.', expect='prayer_menu', key=True)
def _(g):
    g._start_pray()


@scene('menu_boon', 'Prayer', 'Kill a gate boss (Asterion): take one of three gifts.', expect='boon_menu')
def _(g):
    g.player.pending_boon = 'asterion_minotaur'
    g.update(0.0)             # Game.update opens the boon menu itself


@scene('lore_item', 'Lore', 'X, pick an item: item lore dossier.', expect='lore')
def _(g):
    g._lore_subject = next(i for i in g.player.inventory if hasattr(i, 'id_level'))
    g.state = _S().STATE_LORE


@scene('lore_item_tab2', 'Lore', 'Item dossier, Tab: second page.', expect='lore')
def _(g):
    g._lore_subject = next(i for i in g.player.inventory if hasattr(i, 'id_level'))
    g.state = _S().STATE_LORE
    press(g, pygame.K_TAB)


@scene('lore_item_unidentified', 'Lore',
       'X / lore on an item not yet identified: its dossier (the art is the item).',
       expect='lore')
def _(g):
    g._lore_subject = next(i for i in g.player.inventory
                           if hasattr(i, 'id_level') and not getattr(i, 'identified', True)
                           and getattr(i, 'id_level', 0) == 0)
    g.state = _S().STATE_LORE


@scene('lore_corpse', 'Lore', 'Identify a corpse: bestiary dossier.', expect='lore', key=True)
def _(g):
    g._lore_subject = g._capture_corpse
    g.state = _S().STATE_LORE


# -- Encounters ------------------------------------------------------------------

def _merchant(g):
    from mystery_system import MerchantNPC
    from items import load_items, pick_random_weapon_for_floor
    from economy import merchant_price
    rng = random.Random(SEED + 1)
    stock = [copy.copy(load_items('potion')[0]), copy.copy(load_items('scroll')[1]),
             copy.copy(load_items('accessory')[0]), pick_random_weapon_for_floor(5, rng),
             copy.copy(load_items('food')[0])]
    stock = [s for s in stock if s is not None]
    x, y = _free_tiles_near(g, 1, 1)[0]
    m = MerchantNPC(x, y, stock, [merchant_price(it, 5) for it in stock])
    g.ground_items.append(m)
    return m


@scene('shop', 'Encounters', 'Y beside a Deep Gnome Trader: shop.', expect='shop', key=True)
def _(g):
    _merchant(g)
    press(g, pygame.K_y)


def _npc_monster(g, enc):
    from monster import Monster
    defs = _monster_defs()
    kind = enc.get('monster_id') or enc.get('sprite') or 'giant_rat'
    d = defs.get(kind) or next(iter(defs.values()))
    x, y = _free_tiles_near(g, 1, 1)[0]
    m = Monster({**d, 'id': kind}, x, y)
    m._npc_encounter_tag = enc['tag']
    g.monsters.append(m)
    return m


@scene('npc_encounter', 'Encounters', 'Bump a moral-choice NPC: their story.', expect='npc_encounter')
def _(g):
    enc = next(iter(sorted(g._npc_encounter_levels.items())))[1]
    g._start_npc_encounter(_npc_monster(g, enc))


@scene('npc_encounter_options', 'Encounters', 'NPC encounter, Enter: the choices.', expect='npc_encounter')
def _(g):
    enc = next(iter(sorted(g._npc_encounter_levels.items())))[1]
    g._start_npc_encounter(_npc_monster(g, enc))
    press(g, pygame.K_RETURN)


@scene('npc_flavor', 'Encounters', 'Bump a flavour (non-karmic) NPC.', expect='npc_encounter')
def _(g):
    enc = next(iter(sorted(g._flavor_encounter_levels.items())))[1]
    m = _npc_monster(g, enc)
    m._flavor_encounter_tag = enc['tag']
    g._start_flavor_encounter(m)


@scene('cow_encounter', 'Encounters', 'Bump the secret cow.', expect='cow_encounter')
def _(g):
    from monster import Monster
    defs = _monster_defs()
    d = defs.get('cow') or next(iter(defs.values()))
    x, y = _free_tiles_near(g, 1, 1)[0]
    cow = Monster({**d, 'id': 'cow'}, x, y)
    cow._npc_encounter_tag = '_cow_dialog'
    g.monsters.append(cow)
    g._start_cow_encounter(cow)


def _emberpup(g, fed=False, food=2):
    """The abandoned Emberpup, placed by the game's own spawner beside the
    hero, with some food in the pack."""
    import emberpup_encounter as ep
    from items import load_items, Food
    g._emberpup = {'floor': g.dungeon_level, 'spawned': False, 'outcome': None}
    g._maybe_spawn_emberpup(g.dungeon_level)
    pup = next(m for m in g.monsters if ep.is_emberpup(m))
    pup.x, pup.y = _free_tiles_near(g, 1, 1)[0]
    pup._emberpup_fed = fed
    foods = [f for f in load_items('food') if isinstance(f, Food)]
    for f in foods[:food]:
        g.player.inventory.append(copy.copy(f))
    return pup


@scene('emberpup_story', 'Encounters', 'Bump the abandoned Emberpup (rare event, floors 3-8): its story.',
       expect='emberpup')
def _(g):
    g._start_emberpup_encounter(_emberpup(g))


@scene('emberpup_options', 'Encounters', 'Emberpup, Enter: the four choices.', expect='emberpup')
def _(g):
    g._start_emberpup_encounter(_emberpup(g))
    press(g, pygame.K_RETURN)


@scene('emberpup_food', 'Encounters', 'Emberpup choices, 1: pick a food to give it.', expect='emberpup')
def _(g):
    g._start_emberpup_encounter(_emberpup(g))
    press(g, pygame.K_RETURN)
    press(g, pygame.K_1)


@scene('emberpup_fed', 'Encounters', 'Emberpup food list, a: it eats and warms up.', expect='emberpup')
def _(g):
    g._start_emberpup_encounter(_emberpup(g))
    press(g, pygame.K_RETURN)
    press(g, pygame.K_1)
    press(g, pygame.K_a)


@scene('emberpup_quiz', 'Encounters', 'Fed Emberpup, 4 ("I choose you!"): the animal quiz.',
       expect='quiz')
def _(g):
    g._start_emberpup_encounter(_emberpup(g, fed=True))
    press(g, pygame.K_RETURN)
    press(g, pygame.K_4)


@scene('emberpup_joins', 'Encounters', 'Emberpup quiz passed: it comes down off its rock.',
       expect='emberpup', notes='The quiz is ended as passed through QuizEngine._end.')
def _(g):
    g._start_emberpup_encounter(_emberpup(g, fed=True))
    press(g, pygame.K_RETURN)
    press(g, pygame.K_4)
    g.quiz_engine._end(success=True)


@scene('emberpup_name', 'Popups', 'Emberpup joined, Enter: name your Emberpup.',
       expect='pet_name_input', notes='The quiz is ended as passed through QuizEngine._end.')
def _(g):
    g._start_emberpup_encounter(_emberpup(g, fed=True))
    press(g, pygame.K_RETURN)
    press(g, pygame.K_4)
    g.quiz_engine._end(success=True)
    press(g, pygame.K_RETURN)


@scene('emberpup_on_map', 'Encounters', 'The abandoned Emberpup on its rock, on the map.',
       expect='player')
def _(g):
    _emberpup(g)


def _black_knight(g, hits=0):
    """Down to floor 17 with the Black Knight on it (the game's own spawner
    builds his bridge), the hero beside him, close zoom, `hits` blows struck
    (one an action)."""
    import black_knight as bk
    g._black_knight = {'floor': 17, 'spawned': False, 'outcome': None, 'sword_dropped': False}
    g._change_level(17, enter_from_top=True)
    k = next(m for m in g.monsters if bk.is_black_knight(m))
    bt = getattr(g.dungeon, 'bridge_tiles', {}) or {}
    near = [(k.x + dx, k.y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    near = [t for t in near if g.dungeon.is_walkable(*t)]
    near.sort(key=lambda t: t not in bt)
    g.monsters[:] = [m for m in g.monsters if m is k or max(abs(m.x - k.x), abs(m.y - k.y)) > 8]
    g.player.x, g.player.y = near[0]
    g.zoom_mode = 'close'
    g._refresh_fov()
    g._advance_turn()                      # he sees you: "None shall pass."
    for _ in range(hits):
        k.take_damage(10 ** 6)
        g._advance_turn()
    return k


@scene('black_knight_bridge', 'Encounters',
       'The Black Knight on his bridge (rare event, floors 15-19): "None shall pass."', expect='player')
def _(g):
    _black_knight(g)


@scene('black_knight_one_arm', 'Encounters', 'Black Knight, one big hit: the left arm and shield are gone.',
       expect='player')
def _(g):
    _black_knight(g, 1)


@scene('black_knight_no_arms', 'Encounters', 'Black Knight, two hits: no arms, his sword on the bridge.',
       expect='player')
def _(g):
    _black_knight(g, 2)


@scene('black_knight_one_leg', 'Encounters', 'Black Knight, three hits: one leg, hopping.', expect='player')
def _(g):
    _black_knight(g, 3)


@scene('black_knight_torso', 'Encounters', 'Black Knight, five hits: a torso calling it a draw.',
       expect='player')
def _(g):
    _black_knight(g, 5)


@scene('mystery_approach', 'Encounters', 'Step onto a mystery altar (the Sphinx).', expect='mystery_approach')
def _(g):
    from mystery_system import MysteryAltar
    x, y = _free_tiles_near(g, 1, 1)[0]
    altar = MysteryAltar('sphinx', x, y)
    g.ground_items.append(altar)
    g._start_mystery(altar)


@scene('judgment', 'Encounters', 'L99: pray on the Altar of the Last Judgment.', expect='judgment')
def _(g):
    g.karma = 6
    g._resolve_judgment()


# -- Quizzes ----------------------------------------------------------------------

def _armor(g, heavy=False):
    """An armour from the pack: the first, or (heavy) the one needing the
    most right answers to put on."""
    from items import Armor
    pool = [i for i in g.player.inventory if isinstance(i, Armor)]
    if heavy:
        return max(pool, key=lambda i: getattr(i, 'equip_threshold', 1))
    return pool[0]


@scene('quiz_threshold_equip', 'Quiz', 'E, pick armour: geography THRESHOLD quiz (untimed).',
       expect='quiz', key=True)
def _(g):
    g._start_armor_quiz(_armor(g))


@scene('quiz_threshold_progress', 'Quiz', 'Heavy armour (threshold 2+) after one right answer: progress shown.',
       expect='quiz')
def _(g):
    g._start_armor_quiz(_armor(g, heavy=True))
    play_quiz(g, 'c')


@scene('quiz_result_wrong', 'Quiz', 'Armour quiz: the wrong-answer flash.', expect='quiz')
def _(g):
    g._start_armor_quiz(_armor(g))
    answer(g, False)


@scene('quiz_chain_combat', 'Quiz', 'Attack a monster: maths CHAIN quiz with the timer running.',
       expect='quiz', key=True)
def _(g):
    g._start_combat(g._capture_monster)
    g.update(g.quiz_engine.timer_seconds * 0.35)


@scene('quiz_chain_x3', 'Quiz', 'Combat chain after three right answers (chain x3, rank badge).',
       expect='quiz')
def _(g):
    g._start_combat(g._capture_monster)
    play_quiz(g, 'ccc')


@scene('quiz_chain_correct_flash', 'Quiz', 'Combat chain: the right-answer flash.', expect='quiz')
def _(g):
    g._start_combat(g._capture_monster)
    answer(g, True)


@scene('quiz_escalator_prayer', 'Quiz', '\\, pick a prayer: theology ESCALATOR-CHAIN quiz.',
       expect='quiz', key=True)
def _(g):
    g._start_pray()
    press(g, pygame.K_1)


@scene('quiz_escalator_climbed', 'Quiz', 'Prayer quiz after two right answers (tier has escalated).',
       expect='quiz')
def _(g):
    g._start_pray()
    press(g, pygame.K_1)
    play_quiz(g, 'cc')


@scene('quiz_recall_lore', 'Quiz', 'N: Recall Lore, trivia escalator chain.', expect='quiz')
def _(g):
    press(g, pygame.K_n)


@scene('quiz_identify', 'Quiz', 'I, pick an item: philosophy identify question.', expect='quiz')
def _(g):
    press(g, pygame.K_i)
    press(g, pygame.K_RETURN)


@scene('quiz_cook', 'Quiz', 'C, pick an ingredient: cooking question.', expect='quiz')
def _(g):
    press(g, pygame.K_c)
    press(g, pygame.K_RETURN)


@scene('quiz_harvest', 'Quiz', 'H on a corpse: animal harvest question.', expect='quiz')
def _(g):
    from items import Corpse
    c = Corpse('giant rat', 'giant_rat', g.player.x, g.player.y)
    g.ground_items.append(c)
    press(g, pygame.K_h)


def _quiz_with_blurb(g):
    """Start the armour quiz; if the drawn question has no context blurb,
    answer it and look at the next (the real flow), until one does."""
    from quiz_engine import QuizState
    for subject_try in range(8):
        g._start_armor_quiz(_armor(g)) if subject_try == 0 else None
        qe = g.quiz_engine
        if qe.state == QuizState.ASKING and qe.current_context_blurb():
            return True
        if qe.state == QuizState.ASKING:
            answer(g, True)
            settle_quiz(g)
        else:
            return False
    return False


@scene('quiz_context_modal', 'Quiz', 'In a quiz, C: the topic context blurb (orientation).',
       expect='quiz_context', key=True)
def _(g):
    if not _quiz_with_blurb(g):
        # Recall Lore (trivia) and prayer (theology) are the other ladders.
        g.state = _S().STATE_PLAYER
        g._start_pray()
        press(g, pygame.K_1)
    press(g, pygame.K_c)


# -- Results after a quiz -------------------------------------------------------

@scene('result_recall_lore', 'Lore', 'N, answer the trivia chain: the Recall Lore card.', expect='hint')
def _(g):
    press(g, pygame.K_n)
    play_quiz(g, 'ccw')


@scene('result_hack_reality', 'Popups', 'xyzzy, Y, answer the AI chain: Hack Reality result.',
       expect='hack_reality')
def _(g):
    press(g, pygame.K_BACKQUOTE)
    type_text(g, 'xyzzy')
    press(g, pygame.K_RETURN)
    press(g, pygame.K_y, 'y')
    play_quiz(g, 'ccw')


# -- Endings ------------------------------------------------------------------------

def _die(g, reason):
    g.defeat_reason = reason
    g.player.hp = 0
    g._on_game_over()
    g.state = _S().STATE_DEAD


@scene('end_death', 'Endings', 'Die in combat: death screen.', expect='dead', key=True)
def _(g):
    _die(g, 'died')


@scene('end_starved', 'Endings', 'Starve: death screen (starved).', expect='dead')
def _(g):
    _die(g, 'starved')


@scene('end_fled', 'Endings', 'Abandon the quest: death screen (fled).', expect='dead')
def _(g):
    _die(g, 'fled')


@scene('end_review_missed', 'Endings', 'Death screen, R: review the questions you missed.',
       expect='review_missed')
def _(g):
    _die(g, 'died')
    press(g, pygame.K_r)


@scene('end_victory', 'Endings', 'Leave with the Philosopher\'s Stone: victory screen.', expect='victory')
def _(g):
    g._on_game_over(leave_bones=False)
    g.state = _S().STATE_VICTORY


@scene('end_victory_abyss', 'Endings', 'The secret Abyss ending: victory screen variant.', expect='victory')
def _(g):
    g._secret_victory = True
    g._on_game_over(leave_bones=False)
    g.state = _S().STATE_VICTORY


# ---------------------------------------------------------------------------
# Frame time (the performance gate)
# ---------------------------------------------------------------------------

# A long, two-line-at-1080p log message: the worst case for the message log,
# which used to re-wrap every entry every frame (FOUNDATION_REVIEW.md 2.2).
FULL_LOG_TEXT = ("You strike the cave troll with the Sword of Saint Michael for 23 damage; "
                 "it reels back, howling, and the torchlight shudders across the wet stone "
                 "of the Labyrinth of Echoes as its blood hisses on the floor.")


def fill_log(g, n: int = 60) -> None:
    """Fill the message log to its cap with long messages."""
    kinds = ('info', 'success', 'warning', 'danger', 'loot')
    for i in range(n):
        g.add_message(f"{FULL_LOG_TEXT} ({i})", kinds[i % len(kinds)])


def time_scene(sc: Scene, size, frames: int = 7, full_log: bool = True) -> dict:
    """Build the scene untraced on the real display surface, draw one warm-up
    frame, then time ``frames`` more, each INCLUDING ``pygame.display.flip()``
    (what the game loop does after drawing). Returns, in ms:

    * ``median`` / ``max``: steady-state frames (render + flip). The first
      (warm-up) frame is excluded: it pays one-off costs (font glyphs, the
      overlay surface, the log wrap). The rule that nothing is LOADED on a
      draw is guarded separately (test_ui_theme
      ``test_key_screens_draw_with_a_full_kit_and_the_quiz_never_loads_art``).
    * ``warm``: that first frame.
    * ``flip``: median of the flip alone. Under the SDL dummy driver this is
      the cost of SDL's software present path only (near zero); a real
      GPU / compositor present is not measurable headless.

    Must run inside ``harness(trace=False)``."""
    screen = make_screen(size, trace=False)
    reset_sandbox()
    reseed()
    times, flips = [], []
    if sc.kind == 'game':
        g = build_game(screen, size)
        sc.setup(g)
        if sc.expect_state and g.state != sc.expect_state:
            raise RuntimeError(f"setup reached state {g.state!r}, expected {sc.expect_state!r}")
        if full_log:
            fill_log(g)

        def frame():
            g.render()
    else:
        obj = sc.setup(screen)

        def frame():
            pygame.event.clear()
            _run_one_frame(lambda: obj.run(FakeClock()))
    flip = pygame.display.flip
    # The garbage collector is paused while frames are timed (and run once
    # before): a GC pass triggered by whatever the test process allocated
    # earlier is noise, not the screen's draw cost.
    import gc
    gc.collect()
    gc_was_on = gc.isenabled()
    gc.disable()
    try:
        for _ in range(frames + 1):
            t0 = time.perf_counter()
            frame()
            t1 = time.perf_counter()
            flip()
            t2 = time.perf_counter()
            times.append((t2 - t0) * 1000.0)
            flips.append((t2 - t1) * 1000.0)
    finally:
        if gc_was_on:
            gc.enable()
    warm, rest = times[0], sorted(times[1:])
    fl = sorted(flips[1:])
    return {'warm': warm, 'median': rest[len(rest) // 2], 'max': rest[-1],
            'flip': fl[len(fl) // 2]}


def calibration_ms(reps: int = 15) -> float:
    """Median ms of a fixed, frame-like pygame workload (fills, a
    full-surface alpha blit, rects, 40 lines of text) at 2560x1440. It slows
    down with the machine (another process hogging the CPU or memory bus,
    battery saver) the same way a screen does, so the frame-time gate
    scales its budgets by ``calibration_ms() / reference`` and a busy
    machine cannot fail it; a screen that got slower relative to this
    workload still does."""
    import fantasy_ui
    W, H = 2560, 1440
    dst = pygame.Surface((W, H))
    wash = pygame.Surface((W, H), pygame.SRCALPHA)
    wash.fill((0, 0, 0, 190))
    font = fantasy_ui.get_font('body', 20, unscaled=True)   # fixed work at any UI scale
    line = "You strike the cave troll with the Sword of Saint Michael for 23 damage."
    times = []
    for i in range(reps + 1):
        t0 = time.perf_counter()
        dst.fill((12, 14, 30))
        dst.blit(wash, (0, 0))
        for k in range(20):
            pygame.draw.rect(dst, (200, 160, 40), (40 + k * 60, 100, 300, 200), 2,
                             border_radius=4)
            dst.fill((20, 24, 50), (60 + k * 60, 120, 260, 160))
        for k in range(40):
            dst.blit(font.render(f"{line} {k}", True, (230, 220, 190)), (60, 300 + k * 26))
        times.append((time.perf_counter() - t0) * 1000.0)
    rest = sorted(times[1:])
    return rest[len(rest) // 2]


def time_scenes(scenes, sizes, frames: int = 7, verbose: bool = True) -> dict:
    """{(scene name, size): timing dict} for every scene at every size."""
    out = {}
    with harness(trace=False):
        for size in sizes:
            for sc in scenes:
                r = time_scene(sc, size, frames)
                out[(sc.name, size)] = r
                if verbose:
                    print(f"  {size_tag(size):>9}  {sc.name:<28} median {r['median']:6.2f} ms"
                          f"   max {r['max']:6.2f}   first {r['warm']:6.2f}"
                          f"   flip {r['flip']:5.2f}")
    return out


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------

@dataclass
class Shot:
    scene: Scene
    size: tuple
    ok: bool
    path: Path | None = None
    error: str = ''
    state: str = ''
    outside: list = field(default_factory=list)
    surface: object = None


def render_scene(sc: Scene, size, measure_contrast: bool = False) -> tuple[TracingSurface, str]:
    """Build the scene at `size` and draw one frame; returns (screen, state).
    ``measure_contrast``: record the contrast under every text blit (slower).
    Must run inside harness()."""
    screen = make_screen(size)
    screen.measure_contrast = measure_contrast
    reset_sandbox()
    reseed()
    GLYPH_ICONS.clear()
    state = ''
    if sc.kind == 'game':
        g = build_game(screen, size)
        sc.setup(g)
        state = g.state
        if sc.expect_state and g.state != sc.expect_state:
            raise RuntimeError(f"setup reached state {g.state!r}, expected {sc.expect_state!r}")
        screen.reset_trace()
        g.render()
    else:
        sc.setup(screen)
        state = sc.kind
    return screen, state


def is_blank(surf) -> bool:
    """True if the frame is (nearly) a single flat colour."""
    small = pygame.transform.scale(surf, (64, 36))
    cols = {small.get_at((x, y))[:3] for x in range(64) for y in range(36)}
    return len(cols) < 4


def capture(scenes, sizes, out_dir: Path = OUT_DIR, save=True, verbose=True) -> list[Shot]:
    shots: list[Shot] = []
    with harness():
        for size in sizes:
            d = out_dir / size_tag(size)
            if save:
                d.mkdir(parents=True, exist_ok=True)
            for sc in scenes:
                t0 = time.time()
                try:
                    surf, state = render_scene(sc, size)
                    shot = Shot(sc, size, True, state=state,
                                outside=surf.text_outside())
                    if save:
                        shot.path = d / f"{sc.name}.png"
                        pygame.image.save(surf, str(shot.path))
                    else:
                        shot.surface = surf.copy()
                except Exception as e:
                    shot = Shot(sc, size, False,
                                error=f"{type(e).__name__}: {e}")
                    if verbose:
                        traceback.print_exc()
                shots.append(shot)
                if verbose:
                    flag = 'ok ' if shot.ok else 'ERR'
                    extra = f"  ({len(shot.outside)} text outside)" if shot.outside else ''
                    print(f"  [{flag}] {size_tag(size):>9}  {sc.name:<28} "
                          f"{time.time() - t0:5.2f}s{extra}{'  ' + shot.error if not shot.ok else ''}")
    return shots


def contact_sheet(shots: list[Shot], size, path: Path, cols=5, thumb_w=380):
    pygame.font.init()
    tw = thumb_w
    th = int(tw * size[1] / size[0])
    label_h = 24
    pad = 10
    shots = [s for s in shots if s.size == size]
    rows = (len(shots) + cols - 1) // cols
    head = 40
    W = pad + cols * (tw + pad)
    H = head + pad + rows * (th + label_h + pad)
    sheet = pygame.Surface((W, H))
    sheet.fill((24, 22, 30))
    font = pygame.font.SysFont('consolas', 16)
    big = pygame.font.SysFont('consolas', 22, bold=True)
    sheet.blit(big.render(f"Philosopher's Quest UI capture  {size_tag(size)}  "
                          f"({sum(s.ok for s in shots)}/{len(shots)} screens)",
                          True, (235, 220, 170)), (pad, 10))
    for i, s in enumerate(shots):
        r, c = divmod(i, cols)
        x = pad + c * (tw + pad)
        y = head + pad + r * (th + label_h + pad)
        lab = s.scene.name + ('' if s.ok else '  [FAILED]')
        col = (220, 220, 220) if s.ok else (255, 110, 110)
        sheet.blit(font.render(lab, True, col), (x, y + 3))
        rect = pygame.Rect(x, y + label_h, tw, th)
        if s.ok and s.path and s.path.exists():
            img = pygame.image.load(str(s.path))
            sheet.blit(pygame.transform.smoothscale(img, (tw, th)), rect)
        else:
            pygame.draw.rect(sheet, (60, 20, 20), rect)
        pygame.draw.rect(sheet, (90, 85, 110), rect, 1)
    pygame.image.save(sheet, str(path))


NOT_CAPTURED = [
    ('Character creation', 'There is no separate character-creation screen: a hero is a typed name '
     '(plus secret-build names). Covered by title_name_typed / title_secret_build.'),
    ('Escalator-THRESHOLD quiz', 'The engine supports it but no game action starts one '
     '(every escalator caller uses escalator_chain). Not reachable in play.'),
    ('Level-up screen', 'The game has no level-up screen; stat gains arrive as log messages. '
     'Gate-boss boons (menu_boon) are the closest thing.'),
    ('Save / load dialogs', 'Saving is automatic; loading is "type your name" on the title '
     '(title_save_found) followed by popup_load_summary. Quit = popup_confirm_exit.'),
    ('Fullscreen effects takeovers', 'Divine Intercession / Unicorn takeovers are animations '
     'driven by effects_runtime timers mid-transition; a still of one frame is not a UI screen.'),
    ('QA floor-warp prompt', 'Only exists for the Titivillus QA build with PQ_QA_MODE=1.'),
]


def write_screens_md(shots: list[Shot], sizes, path: Path):
    by_scene: dict[str, dict] = {}
    order = []
    for s in shots:
        if s.scene.name not in by_scene:
            by_scene[s.scene.name] = {}
            order.append(s.scene)
        by_scene[s.scene.name][size_tag(s.size)] = s
    lines = ["# Philosopher's Quest UI screens", "",
             "Generated by `tools/ui/capture.py`. Every screen is drawn by the game's own "
             "render code from a fresh, seeded game. Re-run the tool to refresh.", "",
             f"Sizes: {', '.join(size_tag(z) for z in sizes)} "
             f"(default, the minimum the game allows, large, Brandon's 3440x1440).", "",
             "| Screen | Group | How it is reached | " +
             " | ".join(size_tag(z) for z in sizes) + " |",
             "|---|---|---|" + "---|" * len(sizes)]
    for sc in order:
        cells = []
        for z in sizes:
            s = by_scene[sc.name].get(size_tag(z))
            if s is None:
                cells.append('-')
            elif not s.ok:
                cells.append(f"FAILED: {s.error.replace('|', '/')}")
            elif s.outside:
                cells.append(f"yes ({len(s.outside)} text outside window)")
            else:
                cells.append('yes')
        reach = sc.reach + (f" *({sc.notes})*" if sc.notes else '')
        lines.append(f"| `{sc.name}` | {sc.group} | {reach.replace('|', '/')} | "
                     + " | ".join(cells) + " |")
    lines += ["", "## Not captured", ""]
    for name, why in NOT_CAPTURED:
        lines.append(f"- **{name}**: {why}")
    outs = [s for s in shots if s.ok and s.outside]
    if outs:
        lines += ["", "## Text drawn outside the window", ""]
        for s in outs:
            for r, t in s.outside[:6]:
                lines.append(f"- `{s.scene.name}` @ {size_tag(s.size)}: "
                             f"\"{t[:60]}\" at {tuple(r)}")
    path.write_text("\n".join(lines) + "\n", encoding='utf-8')


def _parse_size(text):
    w, h = text.lower().split('x')
    return int(w), int(h)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--sizes', nargs='*', help='e.g. 1600x900 1280x720, or 1280x720,1920x1080')
    ap.add_argument('--only', nargs='*', help='substrings of screen names')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--out', default=str(OUT_DIR))
    ap.add_argument('--time', action='store_true',
                    help='measure frame times (full message log) instead of capturing')
    args = ap.parse_args(argv)

    if os.environ.get('PYTHONHASHSEED') != '0':
        env = dict(os.environ, PYTHONHASHSEED='0')
        return subprocess.call([sys.executable, str(Path(__file__).resolve())]
                               + (argv if argv is not None else sys.argv[1:]), env=env)

    scenes = SCENES
    if args.only:
        scenes = [s for s in SCENES if any(o in s.name for o in args.only)]
    if args.list:
        for s in scenes:
            print(f"{s.name:<28} {s.group:<12} {s.reach}")
        return 0
    sizes = ([_parse_size(z) for s in args.sizes for z in s.split(',') if z.strip()]
             if args.sizes else all_sizes())
    if args.time:
        res = time_scenes(scenes, sizes)
        for z in sizes:
            vals = sorted(((r['median'], n) for (n, zz), r in res.items() if zz == z),
                          reverse=True)
            print(f"\n{size_tag(z)}: slowest {vals[0][1]} {vals[0][0]:.2f} ms; "
                  f"mean {sum(v for v, _ in vals) / len(vals):.2f} ms over {len(vals)} screens")
        return 0
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    shots = capture(scenes, sizes, out)
    for z in sizes:
        contact_sheet(shots, z, out / f"SHEET_{size_tag(z)}.png")
    if not args.only:
        write_screens_md(shots, sizes, out / 'SCREENS.md')
    bad = [s for s in shots if not s.ok]
    print(f"\n{len(shots) - len(bad)}/{len(shots)} captured in {time.time() - t0:.1f}s -> {out}")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
