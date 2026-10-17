"""The gates every UI art step must pass (UI art foundation, 2026-10-15).

Every screen the capture tool knows (tools/ui/capture.py, 92 screens) is
drawn by the game's own render code, and:

  (a) FRAME TIME: every screen renders, with a full message log (60 long
      entries), within ``FRAME_BUDGET_MS`` for its window size. A frame is
      ``render()`` + ``pygame.display.flip()``, the median of several
      STEADY-STATE frames (the first, warm-up frame is excluded: it pays
      one-off costs; that nothing is loaded on a draw is guarded by
      test_ui_theme ``test_key_screens_draw_with_a_full_kit...``). Under the
      SDL dummy driver the flip measures ~0.00 ms: SDL's software present
      only. The real GPU / compositor present on Brandon's PC is NOT
      measurable headless, which is why the budgets keep headroom under the
      16.7 ms of a 60 FPS frame for the flip, input and game update.

      Measured 2026-10-16 on Brandon's PC (headless, full log, with a
      ComfyUI image job running alongside, i.e. a realistically busy box):
          size        mean      slowest                     budget  headroom
          1920x1080   4.7-6.1   7.2-10.0 ms                 12 ms   17-40 %
          2560x1440   8.3-9.9   10.2-13.3 ms                15 ms   11-32 %
          3440x1440   8.9-10.7  11.4-14.7 ms                16 ms    8-29 %
      (ranges over four runs; the slowest screens are the quiz context
      modal, pet feed / heal, shop and examine menus). 3440x1440 is
      Brandon's monitor and the heaviest size: its heaviest screens take
      12-14 ms to DRAW, so 60 FPS there leaves only ~3-4 ms for the flip and
      game update. The 16 ms budget is a regression gate, not a 60 FPS
      promise. Before the foundation work: 1920x1080 mean 17.1 / slowest
      24.2 ms; 3440x1440 mean 31.8 / slowest 42.6 ms.
      Kept from flaking three ways: the GC is paused while frames are timed
      (a collection is not draw cost); a screen over budget is re-measured
      twice more with 15 frames and its BEST median counts (a busy moment
      cannot fail it; a real regression is slow every time); and budgets
      scale up by ``capture.calibration_ms() / CALIBRATION_REF_MS`` when the
      machine as a whole is slower than when the budgets were set (battery
      saver, thermal throttling). Each run writes its numbers, headroom and
      calibration to _genart/ui/frame_times_gate.json.
  (b) TEXT CONTRAST: the pixels actually behind each piece of text, sampled
      at the moment the text is drawn: quiz question + answer text >= 7:1,
      other text >= 4.5:1 (large text, 28 px line box and up: 3:1, the WCAG
      large-text rule).
  (c) LAYOUT at the minimum window the game allows (1280x720; main() holds
      the window there unless the display itself is smaller):
        * no text outside the window;
        * no text running over the edge of a panel it overlaps;
        * on a modal screen (drawn over a full-window overlay), no text in
          NO panel at all (text pushed wholly below / beside its panel).
      "Panels" are what ``draw_dark_panel`` / ``draw_panel`` draw, plus
      every OUTLINED ``pygame.draw.rect`` box at least
      ``capture.BOX_MIN_W`` x ``BOX_MIN_H`` (the hand-drawn prayer / boon /
      intercession boxes, ``_ui_subpanel``, decision-menu panes and rows,
      answer cards).
      STILL UNCOVERED: text composed onto an intermediate surface before
      being blitted (the tracer only sees text surfaces blitted to the
      screen); boxes drawn as FILLED rects only, polygons or images (no
      outline to recognise); the title screen's free-floating text (no
      overlay: nothing to be "in"); study mode's in-panel layout (one
      window-sized panel, so only its edges are checked); text inside a
      panel but over a sibling element (e.g. a hint over a list row) is
      only seen when that element is an outlined box.
  (d) the no-art fallback is in tests/test_ui_theme.py (FALLBACK GATE).

Only text on the TOP layer is judged: on a modal screen, text drawn after
the last full-window overlay (what the player reads), not the dimmed HUD
under it. Drop shadows (FP.INK) and pure symbols ('*', arrows) are skipped.

KNOWN_* lists the problems that were already there before the art work
(main @ 7a8a6854; each value was re-measured there, see the entries). The
foundation step was not allowed to change how they look; each is a real
bug to fix in its own step. An exemption covers its text only at no worse
than the contrast recorded for it. Entries that no longer occur fail
``test_every_exemption_is_still_needed``: delete them. Nothing may be ADDED
to make an art step pass; an entry may only be added when a NEW check finds
a problem that is provably already there at that commit.
"""
import json
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import importlib.util  # noqa: E402
import sys  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from pathlib import Path  # noqa: E402

import pygame  # noqa: E402
import pytest  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

from fantasy_ui import FP, KT  # noqa: E402

pygame.init()


def _load_capture():
    if 'pq_ui_capture' in sys.modules:
        return sys.modules['pq_ui_capture']
    spec = importlib.util.spec_from_file_location(
        'pq_ui_capture', _ROOT / 'tools' / 'ui' / 'capture.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['pq_ui_capture'] = mod
    spec.loader.exec_module(mod)
    return mod


capture = _load_capture()

# Every test starts with an empty UI art kit and restores the previous one
# (the capture harness loads assets/ui/; GROUNDWORK_REVIEW 9).
# The whole module is slow (every screen captured at five sizes, the frame
# budget timed): it runs in CI and on request (`pytest --run-slow`).
pytestmark = [pytest.mark.usefixtures('ui_theme_isolated'), pytest.mark.slow]

MIN_SIZE = (1280, 720)
FRAME_BUDGET_MS = {(1280, 720): 10.0, (1920, 1080): 12.0, (2560, 1440): 15.0, (3440, 1440): 16.0}
# capture.calibration_ms() on Brandon's PC when the budgets were set (2026-10-16:
# 2.30-2.96 ms over 24 runs, median 2.4).
CALIBRATION_REF_MS = 2.4
FRAME_SIZES = list(FRAME_BUDGET_MS)
QUIZ_CONTRAST = 7.0
BODY_CONTRAST = 4.5
LARGE_CONTRAST = 3.0
LARGE_LINE_H = 28

# (screen-name prefix, text prefix) -> (why it is low, the contrast it had).
# EMPTY since the Midnight Codex kit pass (2026-10-16): every pre-existing
# problem listed here (welcome F2 hint and load notice, study-mode hints and
# verdicts, the throw menu's POTION tag, the death-screen titles) was fixed
# and its entry deleted. Nothing may be added to make an art step pass.
KNOWN_LOW_CONTRAST = {}
CONTRAST_SLACK = 0.02
# (Deleted 2026-10-16 as never used: ('end_', 'Slain on dungeon level'), 3.05:1 at
# 7a8a6854 and now. Its line box is 28 px+, so the 3:1 large-text floor applies.)

# (screen-name prefix, text prefix) -> why it crosses its panel's edge.
# EMPTY since the kit pass (the title banner's Q tail, the study-mode hints,
# the fast picker's footer overrun were fixed).
KNOWN_OUTSIDE_PANEL = {}

# (screen-name prefix, text prefix) -> why it sits in no panel on a modal
# screen. EMPTY since the kit pass (the character sheet's key hint now sits
# inside the sheet's frame, not over the message log).
KNOWN_NO_PANEL = {}

# Free text on a modal screen BY DESIGN (not a bug). EMPTY since the visual
# review (2026-10-16): the ending headlines used to float on the coloured
# wash (rune-circle rays crossed them); they sit on their own plaque now.
DESIGNED_FREE_TEXT = {}
# The title screen has no modal layer: its glow / vignette are full-window
# blits, not overlays, and its text floats free by design. Its two modal
# popups ARE checked.
NO_PANEL_CHECKED_TITLES = ('title_alltime_scores', 'title_god_prompt')


def _match(table, scene, text):
    """The KNOWN key covering (scene, text), or None."""
    for key in table:
        s, t = key
        if scene.startswith(s) and text.startswith(t):
            return key
    return None


@dataclass
class Rec:
    name: str
    group: str
    top: list            # [(rect, text, info)]
    outside_window: list
    outside_panels: list
    in_no_panel: list
    n_panels: int
    size: tuple = MIN_SIZE
    panels: tuple = ()          # top-layer panel rects
    overlays: int = 0
    text_h_min: int = 0         # smallest text line box on the whole screen
    all_text: tuple = ()        # every text blit: (rect, text, info), all layers
    glyph_icons: tuple = ()     # menu icons drawn as a letter glyph (no art)


def _record(sc, surf, size=MIN_SIZE):
    blits, infos, panels = surf.top_layer()
    heights = [r.h for r, t in surf.text_blits if any(c.isalnum() for c in t)]
    return Rec(sc.name, sc.group,
               [(r, t, i) for (r, t), i in zip(blits, infos)],
               surf.text_outside(), surf.text_outside_panels(),
               surf.text_in_no_panel(), len(panels), size,
               tuple(pygame.Rect(p) for p, _ in panels), surf.overlays,
               min(heights) if heights else 0,
               tuple((r, t, i) for (r, t), i in zip(surf.text_blits, surf.text_info)),
               tuple(capture.GLYPH_ICONS))


def _render_all(size):
    recs = {}
    with capture.harness():
        for sc in capture.SCENES:
            surf, _state = capture.render_scene(sc, size, measure_contrast=True)
            recs[sc.name] = _record(sc, surf, size)
    return recs


@pytest.fixture(scope='module')
def min_records():
    return _render_all(MIN_SIZE)


# The UI scales with the window (_genart/ui/SCALE_PLAN.md): the contrast and
# layout gates also run at 1920x1080 (scale 1.25) and 3440x1440 (Brandon's
# monitor, scale 1.5), with the centring and text-size checks in (e).
SCALED_SIZES = [(1920, 1080), (3440, 1440)]
# Bug bash 4, calls 15 and 19: 1280x720 is the supported floor; below it the
# COMPACT layout (UI scale under 1.0, text floored at 16 px) must not break a
# screen at 1093x614 (a 1366x768 laptop at 125 %), and a portrait monitor
# (1080x1920) gets the stacked title screen. Every layout, contrast, size,
# clip, ellipsis, centring and title-wheel gate runs at both.
SMALL_SIZES = [(1093, 614), (1080, 1920)]


@pytest.fixture(scope='module')
def scaled_records():
    return {size: _render_all(size) for size in SCALED_SIZES}


@pytest.fixture(scope='module')
def small_records():
    return {size: _render_all(size) for size in SMALL_SIZES}


# =============================================================================
# (b) contrast
# =============================================================================

def _is_quiz_body(scene, info):
    return (scene.startswith('quiz_') and scene != 'quiz_context_modal'
            and info['color'] in (FP.VELLUM, FP.PARCHMENT_LIGHT,
                                  KT.TEXT_QUIZ, KT.OK_TEXT, KT.BAD_TEXT))


def _log_pane(size=MIN_SIZE):
    import layout
    layout.update(*size)
    return pygame.Rect(layout.MAP_X, layout.GAME_H, layout.MAP_W, layout.MSG_H)


def test_contrast_tracer_sees_low_contrast():
    """Guard the guard: grey text on a grey box must be reported as low."""
    surf = capture.TracingSurface((200, 60))
    surf.measure_contrast = True
    surf.fill((90, 90, 90))
    with capture.harness():
        font = pygame.font.Font(None, 30)
        surf.blit(font.render('Faint', True, (110, 110, 110)), (10, 10))
        surf.blit(font.render('Clear', True, (255, 255, 255)), (100, 10))
    lo, hi = (i['contrast'] for i in surf.text_info)
    assert lo < 1.5 and hi > 3.0


def _contrast_failures(min_records, used=None, size=MIN_SIZE):
    # The message log is judged like every other text (VISUAL_REVIEW must-fix
    # 1): its age fade is a colour blend floored at 4.5:1, so even its oldest
    # line passes. ``log_lines`` counts what was measured there.
    log_pane = _log_pane(size)
    failures, measured_quiz = [], {'__log__': 0}
    for name, rec in min_records.items():
        for r, text, info in rec.top:
            c = info['contrast']
            if c is None or info['color'] == FP.INK or not any(ch.isalnum() for ch in text):
                continue
            if rec.group == 'Play' and log_pane.colliderect(r):
                measured_quiz['__log__'] += 1
            if _is_quiz_body(name, info):
                need = QUIZ_CONTRAST
                measured_quiz.setdefault(name, []).append(c)
            elif r.h >= LARGE_LINE_H:
                need = LARGE_CONTRAST
            else:
                need = BODY_CONTRAST
            if c >= need:
                continue
            key = _match(KNOWN_LOW_CONTRAST, name, text)
            if key is not None:
                if used is not None:
                    used.add(key)
                floor = KNOWN_LOW_CONTRAST[key][1]
                if c >= floor - CONTRAST_SLACK:
                    continue
                failures.append(f"{name}: {c:.2f}:1, WORSE than its exemption's "
                                f"{floor:.2f}:1  {text[:50]!r}")
                continue
            failures.append(f"{name}: {c:.2f}:1 < {need}:1  {info['color']} {text[:50]!r}")
    return failures, measured_quiz


def test_text_contrast_on_every_screen(min_records):
    failures, measured_quiz = _contrast_failures(min_records)
    assert not failures, "Text below its contrast floor:\n" + "\n".join(failures)
    assert measured_quiz.pop('__log__') >= 30, "the message log's lines were not measured"
    quiz =[n for n in min_records if n.startswith('quiz_') and n != 'quiz_context_modal']
    missing = [n for n in quiz if n not in measured_quiz]
    assert not missing, f"no quiz question/answer text was measured on: {missing}"


def test_study_score_is_readable_and_clear_of_the_border(min_records):
    """GROUNDWORK_REVIEW 2: the header's frame repaint put both gold border
    lines through the study "Score: N/M" text (8.76:1 -> 1.62:1). It now
    sits on the header plaque, which the art kit insets inside the frame's
    16 px band (the panel starts at 24): clear of the frame and the band."""
    import fantasy_ui
    for name in ('study_question', 'study_result_correct', 'study_result_wrong'):
        rec = min_records[name]
        hits = [(r, i) for r, t, i in rec.top
                if t.startswith('Score:') and i['color'] != FP.INK]
        assert hits, f"{name}: no score drawn"
        for r, info in hits:
            assert info['contrast'] >= BODY_CONTRAST, (name, info['contrast'])
            # The study page is sized to its content and centred (VISUAL_REVIEW
            # 2026-10-16): the score sits on the plaque of the page it is on.
            with capture.harness():
                plaques = [fantasy_ui.header_rect(p, 48) for p in rec.panels
                           if p.w > 400 and p.h > 200]
            assert plaques and all(pl.y >= p.y + 16 for pl, p in
                                   zip(plaques, [p for p in rec.panels
                                                 if p.w > 400 and p.h > 200]))
            assert any(pl.contains(info['ink']) for pl in plaques), (name, info['ink'], plaques)


# =============================================================================
# (c) layout at the minimum window
# =============================================================================

def test_no_text_outside_the_window_at_minimum_size(min_records):
    bad = [f"{n}: {t[:40]!r} at {tuple(r)}" for n, rec in min_records.items()
           for r, t in rec.outside_window]
    assert not bad, "\n".join(bad)


def test_no_text_over_its_panel_edge_at_minimum_size(min_records):
    bad = [f"{n}: {t[:40]!r} ink {tuple(r)} panel {tuple(p)}"
           for n, rec in min_records.items() for r, t, p in rec.outside_panels
           if _match(KNOWN_OUTSIDE_PANEL, n, t) is None]
    assert not bad, "Text crossing the edge of its panel:\n" + "\n".join(bad)


def _no_panel_checked(rec):
    return rec.group != 'Title' or rec.name in NO_PANEL_CHECKED_TITLES


def test_no_text_in_no_panel_on_modal_screens(min_records):
    bad = [f"{n}: {t[:40]!r} ink {tuple(r)}"
           for n, rec in min_records.items() if _no_panel_checked(rec)
           for r, t in rec.in_no_panel
           if _match(KNOWN_NO_PANEL, n, t) is None and _match(DESIGNED_FREE_TEXT, n, t) is None]
    assert not bad, "Text outside every panel on a modal screen:\n" + "\n".join(bad)


def test_every_exemption_is_still_needed(min_records):
    """A KNOWN entry that matches nothing is stale: delete it."""
    used = set()
    _contrast_failures(min_records, used)
    for n, rec in min_records.items():
        for _r, t, _p in rec.outside_panels:
            k = _match(KNOWN_OUTSIDE_PANEL, n, t)
            if k:
                used.add(('outside',) + k)
        for _r, t in rec.in_no_panel:
            k = _match(KNOWN_NO_PANEL, n, t)
            if k:
                used.add(('nopanel',) + k)
    stale = ([k for k in KNOWN_LOW_CONTRAST if k not in used]
             + [k for k in KNOWN_OUTSIDE_PANEL if ('outside',) + k not in used]
             + [k for k in KNOWN_NO_PANEL if ('nopanel',) + k not in used])
    assert not stale, f"exemptions that no longer occur (delete them): {stale}"


def test_panels_are_seen_by_the_layout_check(min_records):
    """Guard the guard: the panel checks only mean something if the
    harness records the panels the screens draw, and reports text that
    crosses one or misses every one."""
    for name in ('menu_equip', 'quiz_threshold_equip', 'popup_confirm_exit',
                 'lore_item', 'menu_wand', 'end_death', 'title_alltime_scores',
                 'menu_prayer', 'menu_boon', 'popup_intercession'):
        assert min_records[name].n_panels >= 1, name
    surf = capture.TracingSurface((300, 200))
    with capture.harness():
        import fantasy_ui
        fantasy_ui.draw_dark_panel(surf, (20, 20, 200, 100))
        font = pygame.font.Font(None, 30)
        surf.blit(font.render('Inside', True, (255, 255, 255)), (40, 40))
        surf.blit(font.render('Overrun text', True, (255, 255, 255)), (150, 60))
    out = surf.text_outside_panels()
    assert [t for _r, t, _p in out] == ['Overrun text']

    # A hand-drawn outlined box is a panel; text wholly below it on a modal
    # screen is reported (the footer-hint failure), text inside is not.
    surf = capture.TracingSurface((400, 300))
    with capture.harness():
        import fantasy_ui
        fantasy_ui.draw_overlay(surf, 190)
        pygame.draw.rect(surf, (16, 12, 6), (40, 40, 300, 150), border_radius=8)
        pygame.draw.rect(surf, (200, 160, 40), (40, 40, 300, 150), 3, border_radius=8)
        font = pygame.font.Font(None, 30)
        surf.blit(font.render('In the box', True, (255, 255, 255)), (60, 60))
        surf.blit(font.render('Lost hint', True, (255, 255, 255)), (60, 240))
        surf.blit(font.render('Edge', True, (255, 255, 255)), (320, 100))
    assert [t for _r, t in surf.text_in_no_panel()] == ['Lost hint']
    assert [t for _r, t, _p in surf.text_outside_panels()] == ['Edge']


# =============================================================================
# (a) frame time
# =============================================================================

def test_every_screen_renders_within_the_frame_budget():
    scale = max(1.0, capture.calibration_ms() / CALIBRATION_REF_MS)
    res = capture.time_scenes(capture.SCENES, FRAME_SIZES, frames=9, verbose=False)

    def budget(size):
        return FRAME_BUDGET_MS[size] * scale

    def over(r):
        return {k: v for k, v in r.items() if v['median'] > budget(k[1])}
    slow = over(res)
    for _attempt in range(2):     # re-measure, longer; the BEST median counts
        if not slow:
            break
        scale = max(scale, capture.calibration_ms() / CALIBRATION_REF_MS)
        with capture.harness(trace=False):
            for (name, size) in slow:
                sc = next(s for s in capture.SCENES if s.name == name)
                again = capture.time_scene(sc, size, frames=15)
                if again['median'] < res[(name, size)]['median']:
                    res[(name, size)] = again
        slow = over({k: res[k] for k in slow})
    out = _ROOT / '_genart' / 'ui'
    try:
        out.mkdir(parents=True, exist_ok=True)
        summary = {'calibration_scale': round(scale, 3)}
        for z in FRAME_SIZES:
            vals = [(v['median'], n) for (n, zz), v in res.items() if zz == z]
            worst = max(vals)
            summary[capture.size_tag(z)] = {
                'budget_ms': round(budget(z), 2), 'slowest_ms': round(worst[0], 2),
                'slowest': worst[1], 'mean_ms': round(sum(v for v, _ in vals) / len(vals), 2),
                'headroom_pct': round(100 * (1 - worst[0] / budget(z)), 1),
                'flip_ms': round(max(v['flip'] for (n, zz), v in res.items() if zz == z), 3)}
        (out / 'frame_times_gate.json').write_text(json.dumps(
            {'summary': summary,
             'screens': {f"{capture.size_tag(z)} {n}": round(v['median'], 2)
                         for (n, z), v in sorted(res.items())}}, indent=1), encoding='utf-8')
    except OSError:
        pass
    assert not slow, "Screens over the frame budget (x%.2f machine scale):\n%s" % (
        scale, "\n".join(f"{capture.size_tag(z)} {n}: {v['median']:.1f} ms "
                         f"(budget {budget(z):.1f} ms)"
                         for (n, z), v in sorted(slow.items())))


# =============================================================================
# (b, c) at the scaled sizes
# =============================================================================

@pytest.mark.parametrize('size', SCALED_SIZES + SMALL_SIZES, ids=lambda z: f"{z[0]}x{z[1]}")
def test_text_contrast_at_scaled_sizes(scaled_records, small_records, size):
    recs = {**scaled_records, **small_records}[size]
    failures, measured_quiz = _contrast_failures(recs, size=size)
    assert not failures, f"Text below its contrast floor at {size}:\n" + "\n".join(failures)
    quiz = [n for n in recs
            if n.startswith('quiz_') and n != 'quiz_context_modal']
    assert not [n for n in quiz if n not in measured_quiz]


@pytest.mark.parametrize('size', SCALED_SIZES + SMALL_SIZES, ids=lambda z: f"{z[0]}x{z[1]}")
def test_layout_at_scaled_sizes(scaled_records, small_records, size):
    recs = {**scaled_records, **small_records}[size]
    bad = [f"outside window: {n}: {t[:40]!r} at {tuple(r)}"
           for n, rec in recs.items() for r, t in rec.outside_window]
    bad += [f"over panel edge: {n}: {t[:40]!r} ink {tuple(r)} panel {tuple(p)}"
            for n, rec in recs.items() for r, t, p in rec.outside_panels
            if _match(KNOWN_OUTSIDE_PANEL, n, t) is None]
    bad += [f"in no panel: {n}: {t[:40]!r} ink {tuple(r)}"
            for n, rec in recs.items() if _no_panel_checked(rec)
            for r, t in rec.in_no_panel
            if _match(KNOWN_NO_PANEL, n, t) is None and _match(DESIGNED_FREE_TEXT, n, t) is None]
    assert not bad, f"Layout problems at {size}:\n" + "\n".join(bad)


# =============================================================================
# (e) UI scale: centring and text size (SCALE_PLAN.md 3 and 7)
# =============================================================================

# Bottom-anchored modals: none since the visual review (2026-10-16). The
# quick pickers (wand, spell, eat, quaff, throw, powers, pet care) used to
# sit low over a lightly dimmed map (SCALE_PLAN.md 3, exception 1); a half
# log line peeked under them and the log beside them stayed bright. They
# centre like every other menu now. Kept as a tuple for the check below.
BOTTOM_ANCHORED = ()
# Centred horizontally only: the character sheet is full height with its key
# hint under it (exception 2); an ending's grade panel sits under the title
# set on the wash above it.
HORIZONTAL_ONLY = ('menu_charsheet', 'end_')


def _modal_records(recs):
    """Screens with a modal layer: a full-window overlay with panels on top."""
    for name, rec in recs.items():
        if rec.group in ('Play', 'Study') or not rec.overlays or not rec.panels:
            continue
        if rec.group == 'Title' and name not in NO_PANEL_CHECKED_TITLES:
            continue
        yield name, rec


def _centring_errors(recs):
    import ui_scale
    bad = []
    for name, rec in _modal_records(recs):
        W, H = rec.size
        box = rec.panels[0].unionall(list(rec.panels[1:]))
        if abs(box.centerx - W / 2) > 2:
            bad.append(f"{name} @ {W}x{H}: centre x {box.centerx} != {W // 2}  {tuple(box)}")
        if BOTTOM_ANCHORED and name.startswith(BOTTOM_ANCHORED):
            gap = int(30 * ui_scale.scale_for(W, H) + 0.5)
            if abs(H - box.bottom - gap) > 1:
                bad.append(f"{name} @ {W}x{H}: bottom gap {H - box.bottom} != {gap}")
        elif not name.startswith(HORIZONTAL_ONLY):
            if abs(box.centery - H / 2) > 2:
                bad.append(f"{name} @ {W}x{H}: centre y {box.centery} != {H // 2}  {tuple(box)}")
    return bad


def test_every_modal_is_centred_on_the_window(min_records, scaled_records, small_records):
    """Every modal and menu centres on the WINDOW (not on the play area left
    of the right rail) at 1280x720, 1920x1080 and 3440x1440; the panel
    rects come from the capture harness's own record of what was drawn."""
    bad = _centring_errors(min_records)
    for size in SCALED_SIZES:
        bad += _centring_errors(scaled_records[size])
    for size in SMALL_SIZES:
        bad += _centring_errors(small_records[size])
    assert not bad, "Off-centre modals:\n" + "\n".join(bad)
    checked = sum(1 for _ in _modal_records(min_records))
    assert checked >= 50, f"only {checked} modal screens were checked"


def test_text_is_never_smaller_than_at_the_minimum_window(min_records, scaled_records):
    """Brandon: 'never smaller than today at 1280x720'. On every screen the
    smallest line of text at a bigger window is at least as tall as the
    smallest at 1280x720 -- and at 3440x1440 the text has grown."""
    bad = []
    for size in SCALED_SIZES:
        for name, rec in scaled_records[size].items():
            base = min_records[name].text_h_min
            if rec.text_h_min < base:
                bad.append(f"{name} @ {size}: smallest text {rec.text_h_min} px < {base} px")
    assert not bad, "\n".join(bad)
    grown = [n for n, rec in scaled_records[(3440, 1440)].items()
             if rec.text_h_min > min_records[n].text_h_min]
    assert len(grown) >= len(min_records) * 0.9, "text did not grow at 3440x1440"


# =============================================================================
# (f) The Midnight Codex visual review (_genart/ui/VISUAL_REVIEW.md, 2026-10-16):
#     one gate per class of problem a test can see, at 1280x720, 1920x1080
#     and 3440x1440.
# =============================================================================

def _all_records(min_records, scaled_records, small_records=None):
    yield MIN_SIZE, min_records
    for size in SCALED_SIZES:
        yield size, scaled_records[size]
    for size in (SMALL_SIZES if small_records else ()):
        yield size, small_records[size]


def _readable(text):
    return any(ch.isalnum() for ch in text)


def _floor_px(size, base=16):
    """The text floor at ``size``: 16 px at UI scale 1, growing with the
    scale; in COMPACT (scale under 1) it stays 16 px (ui_scale.TEXT_FLOOR)."""
    import ui_scale
    return max(base, int(base * ui_scale.scale_for(*size) + 0.5))


# Text that is not for reading at a glance, by design: the developer-only
# debug overlay (PQ_QA_MODE). Every other screen keeps the 16 px floor.
SMALL_TEXT_SCREENS = ('play_debug_overlay',)


def test_no_text_below_the_16px_floor(min_records, scaled_records, small_records):
    """DESIGN_RULES 3: hints, footers and labels are 16 px at UI scale 1 at
    the least (the review found 11-13 px on the kit table, quirks, the
    score tables and the character-sheet slot labels). Every text blit on
    every screen, all layers, at its window's UI scale."""
    bad = []
    measured = 0
    for size, recs in _all_records(min_records, scaled_records, small_records):
        floor = _floor_px(size)
        for name, rec in recs.items():
            if name.startswith(SMALL_TEXT_SCREENS):
                continue
            for _r, text, info in rec.all_text:
                pt = info.get('pt')
                if pt is None or not _readable(text):
                    continue
                measured += 1
                if pt < floor:
                    bad.append(f"{name} @ {size[0]}x{size[1]}: {pt} px < {floor} px  {text[:40]!r}")
    assert measured > 5000, f"only {measured} text blits carried a font size"
    assert not bad, f"{len(bad)} text blits under the floor:\n" + "\n".join(sorted(set(bad))[:120])


def test_no_ascii_dashes_or_web_addresses_on_screen(min_records, scaled_records, small_records):
    """Raw strings in a kit world (review minor 8): an ASCII double hyphen
    is set as a typographic dash ("Prayer -- Lord" becomes "Prayer — Lord"),
    and no research link ever reaches the screen (study results showed
    "Source: https://en.wikipedia.org/...")."""
    import re
    bad = []
    for size, recs in _all_records(min_records, scaled_records, small_records):
        for name, rec in recs.items():
            for _r, text, _info in rec.all_text:
                if re.search(r'(?<!-)--(?!-)', text) or re.search(
                        r'https?://|www\.|wikipedia', text, re.I):
                    bad.append(f"{name} @ {size[0]}x{size[1]}: {text[:70]!r}")
    assert not bad, "\n".join(sorted(set(bad)))


def test_no_text_is_cut_by_its_clip(min_records, scaled_records, small_records):
    """Clipped text hides meaning (review must-fix 3: "5d6 fire damag",
    "Total answered: 9 (4"). A line drawn into a clip that cuts its glyphs
    sideways must wrap or be re-laid out instead."""
    bad = []
    for size, recs in _all_records(min_records, scaled_records, small_records):
        for name, rec in recs.items():
            for _r, text, info in rec.all_text:
                ink, clip = info['ink'], info['clip']
                vis = ink.clip(clip)
                if vis.w <= 0 or vis.h <= 0 or not _readable(text):
                    continue                    # wholly clipped: not drawn at all
                if vis.w < ink.w - 2:
                    bad.append(f"{name} @ {size[0]}x{size[1]}: {text[:60]!r} "
                               f"ink {tuple(ink)} clip {tuple(clip)}")
    assert not bad, "Text cut by its clip:\n" + "\n".join(sorted(set(bad)))


# Ellipses that hide nothing a child needs (each says why). Everything else
# must wrap or be re-laid out (review must-fix 4, minor 4).
ALLOWED_ELLIPSIS = {
    # Narration that trails off on purpose; nothing is cut.
    ('quiz_recall_lore', 'You close your eyes and search your memory'):
        'narration: the hero searching memory, not truncated text',
    ('result_recall_lore', 'You close your eyes and search your memory'):
        'narration: the same line on the result card',
    ('result_hack_reality', 'You speak the First Word'):
        'narration: reality shudders, not truncated text',
}


def test_no_ellipsis_hides_meaning(min_records, scaled_records, small_records):
    bad = []
    used = set()
    for size, recs in _all_records(min_records, scaled_records, small_records):
        for name, rec in recs.items():
            for _r, text, _info in rec.all_text:
                t = text.rstrip()
                if not (t.endswith('…') or t.endswith('...')):
                    continue
                key = _match(ALLOWED_ELLIPSIS, name, text)
                if key is not None:
                    used.add(key)
                    continue
                bad.append(f"{name} @ {size[0]}x{size[1]}: {text[:70]!r}")
    assert not bad, "Ellipsized text:\n" + "\n".join(sorted(set(bad)))
    stale = [k for k in ALLOWED_ELLIPSIS if k not in used]
    assert not stale, f"ellipsis allowances that no longer occur (delete them): {stale}"


def test_every_menu_icon_is_item_art(min_records, scaled_records, small_records):
    """Item art is the item (Brandon's rule): no menu row may draw a letter
    glyph because no sprite resolved."""
    bad = [f"{name} @ {size[0]}x{size[1]}: {sorted(set(rec.glyph_icons))}"
           for size, recs in _all_records(min_records, scaled_records, small_records)
           for name, rec in recs.items() if rec.glyph_icons]
    assert not bad, "\n".join(bad)


def test_every_item_in_the_data_resolves_to_art():
    """Every item the data defines (the shop's stock, the pack, loot) has a
    sprite through the one resolver the map and the menus share."""
    from items import load_items
    from renderer import _resolve_item_sprite_path
    missing = []
    for cls in ('potion', 'scroll', 'accessory', 'food', 'wand', 'spellbook',
                'ingredient', 'ammo', 'weapon', 'armor', 'shield', 'artifact'):
        for it in load_items(cls):
            if not _resolve_item_sprite_path(it.id):
                missing.append(f"{cls}: {it.id}")
    assert not missing, "\n".join(missing)


def _pixels(sc_name, size):
    with capture.harness():
        sc = next(s for s in capture.SCENES if s.name == sc_name)
        surf, _ = capture.render_scene(sc, size)
        return pygame.image.tobytes(surf, 'RGB')


@pytest.mark.parametrize('scene,plain', [('play_death_chase', 'play_main'),
                                         ('title_save_found', 'title_name_typed')])
def test_capture_reaches_its_screen(scene, plain):
    """Review minor 12: these two captures were pixel-identical to the plain
    screen, so the Death vignette and the saved-journey cue went unseen."""
    assert _pixels(scene, MIN_SIZE) != _pixels(plain, MIN_SIZE)


@pytest.mark.parametrize('size', [MIN_SIZE] + SCALED_SIZES + SMALL_SIZES,
                         ids=lambda z: f"{z[0]}x{z[1]}")
def test_title_wheel_captions_never_collide(size):
    """Review must-fix 6: at 1280x720 the subject captions collided and the
    orbit lines ran through them. Every tile and caption plaque is clear of
    every other, of the title banner, of the name box and of Top Runs."""
    import ui_scale
    with capture.harness():
        screen = capture.make_screen(size)
        from welcome_screen import WelcomeScreen
        import layout
        w = WelcomeScreen(screen, layout.VERSION)
        _cx, _cy, _r, items = w._wheel()
        rects = [it[3] for it in items] + [it[5] for it in items]
        for i, a in enumerate(rects):
            for b in rects[i + 1:]:
                assert not a.colliderect(b), (size, tuple(a), tuple(b))
        box, _sy, _keys = w._bottom_layout()
        top = int((w._BANNER_Y + w._BANNER_H) * ui_scale.get() + 0.5)
        assert all(r.top >= top and r.bottom <= box.y for r in rects), size
        lb_w, _lb_h = w._leaderboard_size()
        assert lb_w, "the high-score fixture should give a Top Runs panel"
        lb, *_ = w._leaderboard_rect(len(w._lb_entries))
        assert lb.left >= 0 and lb.right <= size[0] - 20, (size, tuple(lb))
        assert not any(lb.colliderect(r) for r in rects), (size, tuple(lb))


# =============================================================================
# (f) no list row under a footer divider (VISUAL_REVIEW_2 must-fix 1)
# =============================================================================

ALL_SIZES = [MIN_SIZE, (1920, 1080), (2560, 1440), (3440, 1440)] + SMALL_SIZES


def _rows_and_dividers(names, size):
    """{scene: (row rects, divider bands)} for ``names`` at ``size``. A row is
    every ``_ui_row`` the screen draws (list rows of every picker and menu);
    a divider band is the full box a ``draw_divider`` covers, its centre
    ornament's reach above and below the line included."""
    import game_render
    import fantasy_ui
    out = {}
    rows, divs = [], []
    R = game_render.RenderMixin
    real_row, real_div = R._ui_row, game_render.draw_divider

    def row(self, rect, *a, **k):
        rows.append(pygame.Rect(rect))
        return real_row(self, rect, *a, **k)

    def div(surf, x, y, w, *a, **k):
        r = fantasy_ui.divider_reach()
        divs.append(pygame.Rect(x, y - r, w, 2 * r))
        return real_div(surf, x, y, w, *a, **k)

    R._ui_row, game_render.draw_divider = row, div
    try:
        with capture.harness():
            for sc in capture.SCENES:
                if sc.name not in names:
                    continue
                rows.clear()
                divs.clear()
                capture.render_scene(sc, size)
                out[sc.name] = (list(rows), list(divs))
    finally:
        R._ui_row, game_render.draw_divider = real_row, real_div
    return out


PICKER_SCENES = ('menu_quaff', 'menu_throw', 'menu_powers', 'menu_spell', 'menu_wand',
                 'menu_eat', 'menu_pet_feed', 'menu_pet_heal', 'menu_pet_specials')


@pytest.mark.parametrize('size', ALL_SIZES, ids=lambda z: f"{z[0]}x{z[1]}")
def test_no_list_row_touches_a_divider(size):
    """On every menu and picker, no list row overlaps a divider or its centre
    ornament, and on the quick pickers every last row leaves the same gap
    (at least the ``md`` step) above the footer divider's ornament. The
    ornament used to sit on the last row of seven pickers, touching
    "(2 turns)." on pet specials."""
    import ui_scale
    names = {s.name for s in capture.SCENES
             if s.name.startswith(('menu_', 'shop', 'lore_'))}
    got = _rows_and_dividers(names, size)
    bad = []
    for name, (rows, divs) in sorted(got.items()):
        for r in rows:
            for d in divs:
                if r.colliderect(d):
                    bad.append(f"{name}: row {tuple(r)} overlaps divider {tuple(d)}")
    assert not bad, "\n".join(bad)
    # The md step at THIS size's scale (the harness puts the scale back after
    # drawing, so ui_scale.get() is not the scale the screens were drawn at).
    md = int(12 * ui_scale.scale_for(*size) + 0.5)
    gaps = {}
    for name in PICKER_SCENES:
        rows, divs = got[name]
        assert rows and divs, name
        footer = max(divs, key=lambda d: d.y)
        last = max(r.bottom for r in rows)
        gaps[name] = footer.top - last
    assert all(g >= md for g in gaps.values()), (size, gaps)
    assert len(set(gaps.values())) == 1, (size, gaps)
