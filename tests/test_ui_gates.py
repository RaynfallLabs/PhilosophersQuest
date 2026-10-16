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

from fantasy_ui import FP  # noqa: E402

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
pytestmark = pytest.mark.usefixtures('ui_theme_isolated')

MIN_SIZE = (1280, 720)
FRAME_BUDGET_MS = {(1920, 1080): 12.0, (2560, 1440): 15.0, (3440, 1440): 16.0}
# capture.calibration_ms() on Brandon's PC when the budgets were set (2026-10-16:
# 2.30-2.96 ms over 24 runs, median 2.4).
CALIBRATION_REF_MS = 2.4
FRAME_SIZES = list(FRAME_BUDGET_MS)
QUIZ_CONTRAST = 7.0
BODY_CONTRAST = 4.5
LARGE_CONTRAST = 3.0
LARGE_LINE_H = 28

# (screen-name prefix, text prefix) -> (why it is low, the contrast it has at
# 7a8a6854). Pre-existing; re-measured at that commit on 2026-10-16 (the same
# value today). A drop below the recorded value is a failure.
KNOWN_LOW_CONTRAST = {
    ('title_', '[ F2 ]  View All-Time'):
        ('welcome leaderboard: the F2 hint is drawn over the panel\'s bottom border at 1280x720',
         2.52),
    ('title_load_notice', "Your saved journey didn't"):
        ('welcome: the load-failure notice lands inside the parchment name box '
         '(FOUNDATION_REVIEW 3.4)', 1.45),
    ('study_', 'Up/Down to select'):
        ('study mode: the footer hint is drawn over the panel\'s bottom border at 720 px tall',
         1.03),
    ('study_', 'Press 1-4 to answer'):
        ('study mode: footer hint over the bottom border', 1.03),
    ('study_', 'Press ENTER or SPACE'):
        ('study mode: footer hint over the bottom border', 1.03),
    ('study_result_correct', 'CORRECT!'):
        ('study mode: verdict drawn over the panel\'s top border at 720 px tall', 1.39),
    ('study_result_wrong', 'INCORRECT'):
        ('study mode: verdict in DANGER_TEXT red, over the top border', 2.11),
    ('menu_throw', 'POTION'):
        ('fast picker: ARCANE_BRIGHT category tag, 4.0:1 on the selected row', 3.98),
    ('end_', 'YOU HAVE DIED'):
        ('death screen: DANGER_TEXT title on the blood-red wash (1.7:1)', 1.74),
    ('end_', 'YOU HAVE STARVED'):
        ('death screen: DANGER_TEXT title on the blood-red wash', 1.74),
    ('end_', 'YOU FLED THE DUNGEON'):
        ('death screen: DANGER_TEXT title on the blood-red wash', 1.74),
}
CONTRAST_SLACK = 0.02
# (Deleted 2026-10-16 as never used: ('end_', 'Slain on dungeon level'), 3.05:1 at
# 7a8a6854 and now. Its line box is 28 px+, so the 3:1 large-text floor applies.)

# (screen-name prefix, text prefix) -> why it crosses its panel's edge.
KNOWN_OUTSIDE_PANEL = {
    ('title_', 'QUEST'):
        'welcome title banner: the tail of the big Q runs ~8 px past the banner\'s bottom border',
    ('title_load_notice', "Your saved journey didn't"): 'see KNOWN_LOW_CONTRAST',
    ('study_', 'Up/Down to select'): 'see KNOWN_LOW_CONTRAST',
    ('study_', 'Press 1-4 to answer'): 'see KNOWN_LOW_CONTRAST',
    ('study_', 'Press ENTER or SPACE'): 'see KNOWN_LOW_CONTRAST',
    ('menu_spell', 'Up/Down: move'):
        'fast picker: the footer hint is not truncated and overruns a 1280 px panel '
        '(FOUNDATION_REVIEW 3.5)',
}

# (screen-name prefix, text prefix) -> why it sits in no panel on a modal
# screen. Found when the no-panel check was added (2026-10-16); identical at
# 7a8a6854, so pre-existing.
KNOWN_NO_PANEL = {
    ('menu_charsheet', 'Arrows: move focus'):
        'character sheet: the footer key hint is drawn below the panels, over the dimmed '
        'message log, at 1280x720',
}

# Free text on a modal screen BY DESIGN (not a bug): the ending headlines
# are set on the coloured wash above the grade panel.
DESIGNED_FREE_TEXT = {
    ('end_death', 'YOU HAVE DIED'), ('end_death', 'Slain on dungeon level'),
    ('end_starved', 'YOU HAVE STARVED'), ('end_starved', 'Hunger claimed you'),
    ('end_fled', 'YOU FLED THE DUNGEON'), ('end_fled', 'Your quest ends in'),
    ('end_victory', 'VICTORY!'), ('end_victory', "You retrieved the Philosopher"),
    ('end_victory_abyss', 'DEATH IS DEAD'), ('end_victory_abyss', 'The Abyss has closed'),
}
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


def _record(sc, surf):
    blits, infos, panels = surf.top_layer()
    return Rec(sc.name, sc.group,
               [(r, t, i) for (r, t), i in zip(blits, infos)],
               surf.text_outside(), surf.text_outside_panels(),
               surf.text_in_no_panel(), len(panels))


@pytest.fixture(scope='module')
def min_records():
    recs = {}
    with capture.harness():
        for sc in capture.SCENES:
            surf, _state = capture.render_scene(sc, MIN_SIZE, measure_contrast=True)
            recs[sc.name] = _record(sc, surf)
    return recs


# =============================================================================
# (b) contrast
# =============================================================================

def _is_quiz_body(scene, info):
    return (scene.startswith('quiz_') and scene != 'quiz_context_modal'
            and info['color'] in (FP.VELLUM, FP.PARCHMENT_LIGHT))


def _log_pane():
    import layout
    layout.update(*MIN_SIZE)
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


def _contrast_failures(min_records, used=None):
    log_pane = _log_pane()
    failures, measured_quiz = [], {}
    for name, rec in min_records.items():
        for r, text, info in rec.top:
            c = info['contrast']
            if c is None or info['color'] == FP.INK or not any(ch.isalnum() for ch in text):
                continue
            if rec.group == 'Play' and log_pane.colliderect(r):
                continue   # the message log fades old lines by design; see the report
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
    quiz = [n for n in min_records if n.startswith('quiz_') and n != 'quiz_context_modal']
    missing = [n for n in quiz if n not in measured_quiz]
    assert not missing, f"no quiz question/answer text was measured on: {missing}"


def test_study_score_is_readable_and_clear_of_the_border(min_records):
    """GROUNDWORK_REVIEW 2: the header's frame repaint put both gold border
    lines through the study "Score: N/M" text (8.76:1 -> 1.62:1). It now
    sits inside the header strip, under the top border."""
    for name in ('study_question', 'study_result_correct', 'study_result_wrong'):
        rec = min_records[name]
        hits = [(r, i) for r, t, i in rec.top
                if t.startswith('Score:') and i['color'] != FP.INK]
        assert hits, f"{name}: no score drawn"
        for r, info in hits:
            assert info['contrast'] >= BODY_CONTRAST, (name, info['contrast'])
            # Inside the panel's inner border (24 + 6) and the 44 px header.
            assert info['ink'].top > 24 + 6 and info['ink'].bottom <= 24 + 44, (name, info['ink'])


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
