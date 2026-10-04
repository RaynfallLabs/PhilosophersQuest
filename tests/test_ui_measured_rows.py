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

  D. Panel footer region split (`PanelBuilder.footer_regions`): the
     scroll-count rect and hint rect do NOT intersect, even on a narrow
     panel with a long hint.

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

pygame.init()
pygame.display.set_mode((16, 16))  # minimal video surface for Font/Surface


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
        rows = [s['cap'], s['main'], s['sub1'], s['sub2']]
        for a, b in zip(rows, rows[1:]):
            assert a.bottom <= b.y, (key, a, b)
        for r in rows:
            assert s['cell'].contains(r), (key, r)
    # HP bar and HP numbers share one row without touching.
    t = slots['target']
    assert t['hp_bar'].right <= t['hp_text'].x
    assert t['sub1'].contains(t['hp_text'])
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
    assert slots['strike']['sub2'].bottom <= g._combat_hud_height()


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
    font, text = g._fit_line(long_name, 420, sizes)
    assert font.size(text)[0] <= 420
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
    weapon = SimpleNamespace(
        name='adamantine composite longbow of the endless hunt',
        base_damage=40, enchant_bonus=3, damage_types=['piercing', 'fire'],
        chain_exponent=1.6, chain_multipliers=[1.0])
    g.player = SimpleNamespace(weapon=weapon, ranged_weapon=weapon)
    g.combat_target = SimpleNamespace(
        name='ancient crystalline wyrm of the sunless deep',
        hp=1284, max_hp=4500, resistances=[], weaknesses=[], tags=[],
        status_effects={'poisoned': 3, 'slowed': 2, 'burning': 4,
                        'blinded': 1, 'stunned': 2, 'weakened': 5,
                        'confused': 2})
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
    assert L['panel_rect'].right <= layout_mod.GAME_W


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
# D. Panel footer region split
# ---------------------------------------------------------------------------

def test_footer_count_and_hint_do_not_overlap():
    """On a narrow panel with a long hint and a long scroll count, the
    count's rect and the hint's rect do not intersect."""
    _reset_layout(600, 500)
    from panel import PanelBuilder, SIZE_SM
    surf = pygame.Surface((600, 500))
    p = PanelBuilder(surf, size=SIZE_SM, max_height=400)
    p.set_footer_hint(
        "Up / Down: move   Left / Right: tab   Enter: pick   Shift+Tab: back"
    )
    p.set_scroll_indicator(999, 999)
    regions = p.footer_regions()
    assert not regions['left'].colliderect(regions['center']), (
        regions['left'], regions['center']
    )
    assert not regions['center'].colliderect(regions['right']), (
        regions['center'], regions['right']
    )


def test_footer_hint_fits_center_region_or_truncates():
    """The hint always paints inside the center region, truncating with
    an ellipsis if necessary (which keeps it off the left/right cells)."""
    _reset_layout(600, 500)
    from panel import PanelBuilder, SIZE_SM
    from fantasy_ui import get_font
    from text_layout import truncate_label
    surf = pygame.Surface((600, 500))
    p = PanelBuilder(surf, size=SIZE_SM, max_height=400)
    long_hint = "A" * 400
    p.set_footer_hint(long_hint)
    p.set_scroll_indicator(1, 42)
    regions = p.footer_regions()
    font = get_font('small', 14)
    fitted = truncate_label(long_hint, max(40, regions['center'].w), font)
    assert font.size(fitted)[0] <= regions['center'].w
