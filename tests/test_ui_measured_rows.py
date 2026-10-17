"""Phase 2 UI beautification — layout-correctness tests (2026-10-04).

Guards four Phase 2 deliverables:

  A. Measured font-height row offsets in the combat HUD and the quiz
     modal: rows must not overlap vertically at two representative window
     sizes (1280×720 + 1920×1080).

  B. Pre-computed quiz panel layout (`_quiz_layout`):
     - short content keeps base fonts, non-scrollable
     - medium content shrinks the question/choice fonts, non-scrollable
     - pathologically long content shrinks to the smallest font tier AND
       enables scrolling, scroll_offset starts at 0

  C. Tab strip overflow (`tab_strip_window`): a 3-tab strip fits entirely,
     a 10-tab strip constrained to a narrow width keeps the active tab
     inside the visible window and raises both arrow flags.

  D. The quiz answer cards are DRAWN where ``_quiz_layout`` puts them
     (``choice_rects``), scrolled or not. (Until 2026-10-15 they were drawn
     10 px above the layout's rects and the tests only looked at the layout.)

Headless — SDL dummy driver — these guard the layout math, not the pixels.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()
pygame.display.set_mode((16, 16))  # minimal video surface for Font/Surface

# Every test starts with an empty UI art kit and restores the previous one
# (the capture harness loads assets/ui/; GROUNDWORK_REVIEW 9).
pytestmark = pytest.mark.usefixtures('ui_theme_isolated')


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _reset_layout(w, h):
    """Reset layout globals to the given viewport."""
    import layout
    layout.update(w, h)


class _StubQuizEngine:
    """Minimal quiz_engine stand-in for _quiz_layout()."""

    def __init__(self, question_text, choices, mode=None, chain=0,
                 correct_count=0, required=1, timed=False,
                 confused_order=None, state=None, timer_seconds=30,
                 time_remaining=15, last_correct=False, last_answer=''):
        from quiz_engine import QuizMode, QuizState
        self.current_question = {
            'question': question_text,
            'choices': list(choices),
            'answer': choices[0] if choices else '',
        }
        self.mode = mode or QuizMode.THRESHOLD
        self.chain = chain
        self.correct_count = correct_count
        self.required = required
        self.timed = timed
        self.confused_order = confused_order
        self.state = state or QuizState.ASKING
        self.timer_seconds = timer_seconds
        self.time_remaining = time_remaining
        self.last_correct = last_correct
        self.last_answer = last_answer
        self.subject = 'philosophy'
        self.tier = 1
        self._quiz_scroll_offset = 0

    def current_context_blurb(self):
        return None


class _StubGameForQuiz:
    """Minimal RenderMixin stand-in with the attributes `_quiz_layout`
    reads. We bind the real method off RenderMixin so we exercise the
    production code path, not a fake."""

    def __init__(self):
        from fantasy_ui import get_font
        self.font_sm = get_font('body', 20)
        self.font_md = get_font('body', 26)
        self.font_lg = get_font('heading', 32)
        self.combat_target = None
        self.quiz_engine = None

    @staticmethod
    def _wrap_text(text, font, max_w):
        from text_layout import wrap_lines
        return wrap_lines(text, max_w, font)

    @property
    def _quiz_layout(self):
        import game_render
        return game_render.RenderMixin._quiz_layout.__get__(self, type(self))


# ---------------------------------------------------------------------------
# A1. Combat HUD measured row offsets
# ---------------------------------------------------------------------------

def _combat_render_stub():
    """RenderMixin subclass carrying just the fonts the combat strip uses,
    so the production slot / fit / draw code runs unmodified."""
    import game_render
    from fantasy_ui import get_font

    class _G(game_render.RenderMixin):
        @staticmethod
        def _wrap_text(text, font, max_w):
            from text_layout import wrap_lines
            return wrap_lines(text, max_w, font)

    g = _G()
    g.font_sm = get_font('body', 20)
    g.font_md = get_font('body', 26)
    g.font_lg = get_font('heading', 32)
    return g


def _assert_combat_slots_clean(slots, bx, bw):
    cells = [slots[k]['cell'] for k in ('target', 'strike')]
    # Cells sit side by side inside the panel, never overlapping.
    assert cells[0].x >= bx and cells[-1].right <= bx + bw
    for a, b in zip(cells, cells[1:]):
        assert a.right <= b.x, (a, b)
    for key in ('target', 'strike'):
        s = slots[key]
        rows = [s['cap'], s['main'], s['sub1'], s['sub2'], s['sub3']]
        for a, b in zip(rows, rows[1:]):
            assert a.bottom <= b.y, (key, a, b)
        for r in rows:
            assert s['cell'].contains(r), (key, r)
    # HP bar and HP numbers share one row without touching.
    t = slots['target']
    assert t['hp_bar'].right <= t['hp_text'].x
    assert t['sub1'].contains(t['hp_text'])
    # The player's own HP row: label, bar, numbers, none touching.
    assert t['you_label'].right <= t['you_bar'].x
    assert t['you_bar'].right <= t['you_text'].x
    assert t['sub3'].contains(t['you_text'])
    # Weapon name sits right of the STRIKE NOW caption, inside its row.
    s = slots['strike']
    assert s['cap'].contains(s['weapon'])


def test_combat_hud_slots_no_overlap_at_1280_720():
    _reset_layout(1280, 720)
    g = _combat_render_stub()
    _assert_combat_slots_clean(g._combat_hud_slots(100, 400, 1000), 100, 1000)


def test_combat_hud_slots_no_overlap_at_1920_1080():
    _reset_layout(1920, 1080)
    g = _combat_render_stub()
    _assert_combat_slots_clean(g._combat_hud_slots(100, 400, 1060), 100, 1060)


def test_combat_hud_height_matches_slot_rows():
    """`_quiz_layout` reserves `_combat_hud_height()`; the last slot row
    must end inside it."""
    g = _combat_render_stub()
    slots = g._combat_hud_slots(0, 0, 1000)
    assert slots['target']['sub3'].bottom <= g._combat_hud_height()


def test_fit_line_shrinks_before_truncating():
    """A long monster name steps down the font ladder and only gets an
    ellipsis when it overflows at the smallest size -- it never runs past
    its slot."""
    g = _combat_render_stub()
    sizes = (26, 22, 18, 15)
    font, text = g._fit_line("GIANT RAT", 400, sizes)
    assert text == "GIANT RAT" and font.get_height() == \
        __import__('fantasy_ui').get_font('body', 26).get_height()
    long_name = "ANCIENT CRYSTALLINE WYRM OF THE SUNLESS DEEP"
    # Sizes under the 16 px floor (DESIGN_RULES 3) are skipped: 15 is never
    # used, so the slot is one an 18 px line fits.
    font, text = g._fit_line(long_name, 470, sizes)
    assert font.size(text)[0] <= 470
    assert text == long_name, "should shrink to fit, not truncate"
    assert font.get_height() < g.font_md.get_height(), "must have stepped down"
    font, text = g._fit_line(long_name * 3, 330, sizes)
    assert font.size(text)[0] <= 330
    assert text.endswith('…')


def test_combat_hud_draws_worst_case_without_error():
    """Headless smoke test: the strip renders at chain 0, mid chain and a
    long-name / many-effects / huge-number worst case."""
    from types import SimpleNamespace
    _reset_layout(1280, 720)
    g = _combat_render_stub()
    g.screen = pygame.Surface((1280, 720))
    g.quiz_title = 'ATTACK'
    # Real player, weapon and monster: since call 13 the strip asks the
    # blow's own damage calculation (combat.strike_damage), which reads the
    # whole player.
    import json
    import items
    from monster import Monster
    from player import Player
    weapon = items.instantiate_weapon('longbow', 'adamantine')
    weapon.name = 'adamantine composite longbow of the endless hunt'
    weapon.base_damage, weapon.enchant_bonus = 40, 3
    weapon.damage_types = ['piercing', 'fire']
    weapon.chain_exponent = 1.6
    g.player = Player()
    g.player.weapon = g.player.ranged_weapon = weapon
    with open(_ROOT / 'data' / 'monsters.json', encoding='utf-8') as f:
        defs = json.load(f)
    kind = next(iter(defs))
    target = Monster(dict(defs[kind], id=kind), 1, 1)
    target.name = 'ancient crystalline wyrm of the sunless deep'
    target.hp, target.max_hp = 1284, 4500
    target.status_effects = {'poisoned': 3, 'slowed': 2, 'burning': 4,
                             'blinded': 1, 'stunned': 2, 'weakened': 5,
                             'confused': 2}
    g.combat_target = target
    rect = pygame.Rect(110, 400, 1060, g._combat_hud_height())
    for chain in (0, 7, 23, 40):
        g.quiz_engine = SimpleNamespace(chain=chain)
        g._draw_combat_hud(rect)


def test_quiz_layout_combat_strip_sits_between_choices_and_hints():
    """In combat the pinned tail is: scroll area, combat strip, hint row --
    stacked without overlap and inside the panel."""
    from quiz_engine import QuizMode
    _reset_layout(1280, 720)
    g = _combat_render_stub()
    g.combat_target = object()
    qe = _StubQuizEngine("17 x 6 = ?", ["96", "102", "112", "104"],
                         mode=QuizMode.CHAIN, chain=7, timed=True)
    qe.subject = 'math'
    g.quiz_engine = qe
    L = g._quiz_layout(qe)
    assert L['is_combat'] is True
    combat, status, scroll = L['combat_rect'], L['status_rect'], L['scroll_rect']
    assert scroll.bottom <= combat.y
    assert combat.bottom <= status.y
    assert status.bottom <= L['panel_rect'].bottom
    # Combat leads with a large tier in the plain body face (not Cinzel).
    from fantasy_ui import get_font
    assert L['question_font'] is get_font('body', 34, bold=True)
    # Fixed-height question band: one-line sum still reserves two lines.
    assert L['question_rect'].height >= 2 * L['q_line_h']


# ---------------------------------------------------------------------------
# A. Measured row offsets — quiz modal rows don't overlap
# ---------------------------------------------------------------------------

def _assert_quiz_rows_no_overlap(layout_dict):
    """Pairwise non-overlap for the three (visible) stacked rects:
    header, timer, status. The scrollable question/choices block sits
    between timer and status; its rects live inside scroll_rect which
    we also test overlaps nothing above / below."""
    header = layout_dict['panel_rect'].copy()
    header.height = layout_dict['header_h']
    timer = layout_dict['timer_rect']
    scroll = layout_dict['scroll_rect']
    status = layout_dict['status_rect']

    # Vertical ordering: header above timer above scroll above status.
    assert header.bottom <= timer.y, (header, timer)
    assert timer.bottom <= scroll.y + 1, (timer, scroll)
    assert scroll.bottom <= status.y + 1, (scroll, status)

    # Choice rects (two rows of two) sit after the question rect inside
    # the scroll region; the question rect must sit before the first
    # choice row.
    qrect = layout_dict['question_rect']
    choices = layout_dict['choice_rects']
    assert len(choices) == 4
    assert qrect.bottom <= choices[0].y
    # Row 1 (first two) sits above row 2 (last two).
    assert choices[0].bottom <= choices[2].y
    assert choices[1].bottom <= choices[3].y


def test_quiz_rows_no_overlap_at_1280_720():
    _reset_layout(1280, 720)
    g = _StubGameForQuiz()
    qe = _StubQuizEngine(
        "What is wisdom?",
        ["choice a", "choice b", "choice c", "choice d"],
    )
    g.quiz_engine = qe
    L = g._quiz_layout(qe)
    _assert_quiz_rows_no_overlap(L)


def test_quiz_rows_no_overlap_at_1920_1080():
    _reset_layout(1920, 1080)
    g = _StubGameForQuiz()
    qe = _StubQuizEngine(
        "What is wisdom?",
        ["choice a", "choice b", "choice c", "choice d"],
    )
    g.quiz_engine = qe
    L = g._quiz_layout(qe)
    _assert_quiz_rows_no_overlap(L)


def test_quiz_modal_fits_within_panel_bounds_at_1280_720():
    """Even with 4 max-length choices, the quiz modal stays inside the
    viewport (modulo the standard 20 px margin top/bottom)."""
    _reset_layout(1280, 720)
    g = _StubGameForQuiz()
    long_q = (
        "If a philosopher stands in the forest and no student is around "
        "to hear him question the nature of being, does his argument "
        "actually make a sound in the metaphysical sense?"
    )
    long_choices = ["x" * 60 for _ in range(4)]
    qe = _StubQuizEngine(long_q, long_choices)
    g.quiz_engine = qe
    L = g._quiz_layout(qe)
    import layout as layout_mod
    assert L['panel_rect'].height <= layout_mod.WINDOW_H - 40
    assert L['panel_rect'].x >= 0
    # Width stays inside the play-area budget (left of the right rail, as
    # always); the panel itself is centred on the WINDOW (SCALE_PLAN.md 3).
    # DESIGN_RULES 7: the quiz is min(1060 s, W - 80) wide, centred on the
    # window (the rails under it are hushed; VISUAL_REVIEW minor 11).
    assert L['panel_rect'].width <= layout_mod.WINDOW_W - 80
    assert L['panel_rect'].right <= layout_mod.WINDOW_W
    assert abs(L['panel_rect'].centerx - layout_mod.WINDOW_W / 2) <= 1


# ---------------------------------------------------------------------------
# B. Pre-computed quiz panel layout: shrink-then-scroll
# ---------------------------------------------------------------------------

def test_quiz_layout_fits_short_content_no_shrink():
    _reset_layout(1920, 1080)
    g = _StubGameForQuiz()
    qe = _StubQuizEngine("Short Q?", ["a", "b", "c", "d"])
    g.quiz_engine = qe
    L = g._quiz_layout(qe)
    assert L['font_tier'] == 0, "short content should keep base fonts"
    assert L['scrollable'] is False
    assert L['scroll_offset'] == 0
    assert L['question_font'] is g.font_md
    assert L['choice_font'] is g.font_sm


def test_quiz_layout_shrinks_medium_content():
    """Build content tall enough to exceed base fonts but still fit at
    the shrunk tier. We squeeze the viewport short so the shrink tier
    is triggered without needing scroll."""
    _reset_layout(1280, 400)
    g = _StubGameForQuiz()
    long_q = (
        "A moderately long philosophical question that at the base font "
        "size would push the panel beyond our short viewport, but once "
        "the question and choice fonts step down one tier the content "
        "fits inside the available 400 px of vertical space."
    )
    choices = [
        "Hobbes said life is nasty short and brutish for all mankind",
        "Rousseau said humankind is born free but is everywhere in chains",
        "Locke said government must protect life liberty and property",
        "Mill said the only justification for restraint is other-harm",
    ]
    qe = _StubQuizEngine(long_q, choices)
    g.quiz_engine = qe
    L = g._quiz_layout(qe)
    # Either tier 1 (one step shrink) or tier 2 (smallest) suffices here;
    # the critical assertion is that we did SHRINK and did NOT scroll.
    assert L['font_tier'] >= 1, "medium content should shrink at least one tier"
    assert L['question_font'] is not g.font_md
    # Scroll not forced when shrink fits
    if L['font_tier'] < 2:
        assert L['scrollable'] is False


def test_quiz_layout_scrolls_pathologically_long_content():
    """A question with a huge number of long paragraphs forces the
    smallest font tier and still overflows the viewport, enabling
    scrolling with scroll_offset=0 initially."""
    _reset_layout(1280, 400)
    g = _StubGameForQuiz()
    long_q = ("Why is wonder considered the beginning of philosophy? " * 60)
    choices = ["x" * 70 for _ in range(4)]
    qe = _StubQuizEngine(long_q, choices)
    g.quiz_engine = qe
    L = g._quiz_layout(qe)
    assert L['scrollable'] is True, "long content should enable scrolling"
    assert L['font_tier'] == 2, "scrolling should only kick in at the smallest tier"
    assert L['scroll_offset'] == 0
    assert L['scroll_max'] > 0


def test_quiz_scroll_offset_persists_on_quiz_engine():
    """`_quiz_scroll_offset` is stored on the QuizEngine and respected by
    the layout helper on the next call (same quiz session)."""
    _reset_layout(1280, 400)
    g = _StubGameForQuiz()
    long_q = ("Why? " * 400)
    choices = ["x" * 50 for _ in range(4)]
    qe = _StubQuizEngine(long_q, choices)
    g.quiz_engine = qe
    L1 = g._quiz_layout(qe)
    assert L1['scrollable'] is True
    # Simulate a PgDn press.
    qe._quiz_scroll_offset = 48
    L2 = g._quiz_layout(qe)
    assert L2['scroll_offset'] == min(48, L2['scroll_max'])


# ---------------------------------------------------------------------------
# C. Tab strip overflow
# ---------------------------------------------------------------------------

def test_tab_strip_fits_short_label_list():
    from text_layout import tab_strip_window
    widths = [60, 70, 65]
    win = tab_strip_window(widths, active=1, available_width=400)
    assert win['overflow'] is False
    assert win['start'] == 0
    assert win['end'] == 3
    assert win['show_left_arrow'] is False
    assert win['show_right_arrow'] is False


def test_tab_strip_scrolls_long_label_list():
    """10 tabs, strip width constrained — verify active tab (index 7) is
    included in the visible window and both arrows (one at least) are
    flagged where appropriate."""
    from text_layout import tab_strip_window
    widths = [80] * 10          # 10 tabs of 80 px each
    available = 300             # fits ~3-4 tabs
    active = 7
    win = tab_strip_window(widths, active=active, available_width=available)
    assert win['overflow'] is True
    assert win['start'] <= active < win['end'], (
        f"active tab {active} must be inside visible window "
        f"[{win['start']}, {win['end']})"
    )
    # When the active tab is deep in the list there should be hidden
    # tabs on the left; the right-arrow flag may or may not be set
    # depending on how the window centres, but at least ONE arrow must
    # be shown (otherwise overflow is a lie).
    assert win['show_left_arrow'] or win['show_right_arrow']


def test_tab_strip_first_tab_no_left_arrow():
    from text_layout import tab_strip_window
    widths = [80] * 10
    win = tab_strip_window(widths, active=0, available_width=300)
    assert win['overflow'] is True
    assert win['start'] == 0
    assert win['show_left_arrow'] is False
    assert win['show_right_arrow'] is True


def test_tab_strip_last_tab_no_right_arrow():
    from text_layout import tab_strip_window
    widths = [80] * 10
    win = tab_strip_window(widths, active=9, available_width=300)
    assert win['overflow'] is True
    assert win['end'] == 10
    assert win['show_right_arrow'] is False
    assert win['show_left_arrow'] is True


# ---------------------------------------------------------------------------
# D. The answer cards are drawn exactly at the layout's choice_rects
# ---------------------------------------------------------------------------

def _quiz_game(size):
    import layout
    from main import Game
    import game_states as S
    screen = pygame.display.set_mode(size)
    layout.update(*size)
    g = Game(screen, player_name='CardTest')
    g.on_resize(*size)
    g.state = S.STATE_QUIZ
    g.quiz_title = "EQUIPPING A TEST HELM  --  HISTORY"
    g.quiz_engine.start_quiz(mode='threshold', subject='history', tier=2,
                             callback=lambda _r: None, threshold=1, total_qs=1,
                             timed=False)
    return g


def _drawn_cards(monkeypatch, g):
    import fantasy_ui
    drawn = []
    real = fantasy_ui.draw_choice_button

    def spy(surf, rect, *a, **k):
        drawn.append(pygame.Rect(rect))
        return real(surf, rect, *a, **k)
    monkeypatch.setattr(fantasy_ui, 'draw_choice_button', spy)
    g.render()
    return drawn


def test_quiz_cards_are_drawn_at_the_layout_rects(monkeypatch):
    for size in ((1280, 720), (1920, 1080)):
        g = _quiz_game(size)
        drawn = _drawn_cards(monkeypatch, g)
        L = g._quiz_layout(g.quiz_engine)
        n = len(L['display_choices'])
        assert n >= 2
        assert drawn == L['choice_rects'][:n], (size, drawn, L['choice_rects'])
        # And the pixels agree: the card border is ON the layout rect's top
        # edge, not 10 px above it.
        top = L['choice_rects'][0]
        assert g.screen.get_at((top.centerx, top.y))[:3] != g.screen.get_at(
            (top.centerx, top.y - 10))[:3]
        # Nothing is left over at the bottom of the scroll area.
        last = L['choice_rects'][n - 1]
        assert last.bottom == L['scroll_rect'].bottom


def test_quiz_cards_scrolled_are_drawn_at_the_layout_rects_moved(monkeypatch):
    g = _quiz_game((1280, 720))
    qe = g.quiz_engine
    long_q = " ".join(["An extremely long question that will not fit."] * 30)
    long_c = " ".join(["A long answer that wraps over many lines."] * 6)
    qe.current_question = dict(qe.current_question, question=long_q,
                               choices=[long_c + " A", long_c + " B", long_c + " C",
                                        long_c + " D"],
                               answer=long_c + " A")
    qe.confused_order = None
    qe._quiz_scroll_offset = 0
    L0 = g._quiz_layout(qe)
    assert L0['scrollable'], "the fixture must force the scrolling layout"
    qe._quiz_scroll_offset = L0['scroll_max']        # scrolled to the bottom
    drawn = _drawn_cards(monkeypatch, g)
    L = g._quiz_layout(qe)
    off = L['scroll_offset']
    assert off > 0
    expected = [r.move(0, -off) for r in L['choice_rects']]
    visible = [r for r in expected
               if not (r.bottom < L['scroll_rect'].y or r.y > L['scroll_rect'].bottom)]
    assert drawn == visible



def test_quiz_with_more_than_four_choices_degrades_gracefully(monkeypatch):
    """GROUNDWORK_REVIEW 6: ``choice_rects`` had exactly four entries, so a
    (malformed) question with a fifth choice raised IndexError in the draw.
    The grid now grows downward: every choice gets its own card, the cards
    stay in two columns without overlapping, inside the scroll area."""
    for size in ((1280, 720), (1920, 1080)):
        for n in (5, 6, 9):
            g = _quiz_game(size)
            qe = g.quiz_engine
            choices = [f"Choice number {i + 1}" for i in range(n)]
            qe.current_question = dict(qe.current_question, choices=choices,
                                       answer=choices[0])
            qe.confused_order = None
            qe._quiz_scroll_offset = 0
            drawn = _drawn_cards(monkeypatch, g)
            L = g._quiz_layout(qe)
            assert len(L['choice_rects']) >= n
            if not L['scrollable']:
                assert drawn == L['choice_rects'][:n], (size, n)
                assert L['choice_rects'][n - 1].bottom <= L['scroll_rect'].bottom
            for i, a in enumerate(L['choice_rects'][:n]):
                assert L['panel_rect'].contains(a) or L['scrollable'], (size, n, a)
                for b in L['choice_rects'][i + 1:n]:
                    assert not a.colliderect(b), (size, n, a, b)
    # Fewer than four still lays out four slots (the old shape).
    g = _quiz_game((1280, 720))
    qe = g.quiz_engine
    qe.current_question = dict(qe.current_question, choices=['A', 'B', 'C'], answer='A')
    qe.confused_order = None
    assert len(g._quiz_layout(qe)['choice_rects']) == 4
    g.render()
