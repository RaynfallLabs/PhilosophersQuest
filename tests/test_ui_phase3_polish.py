"""Phase 3 UI beautification — polish tests (2026-10-04).

Guards three Phase 3 deliverables:

  A. Sidebar attributes 2-col x 3-row layout: synthesize a player with
     3-digit stat values and verify that within each cell the label and
     value never overlap, and that no cell crosses the vertical midpoint
     divider of the pane.

  B. "Depth" metric removed from the DERIVED block: ``Sidebar._derived``
     no longer emits the dupe. Confirms `Floor N` in ``_identity``
     remains the sole dungeon-level readout.

  C. ``MessageLog`` wrapping cleanups:
       1. oversized unbroken tokens get broken by character so no
          rendered line exceeds the pane width;
       2. line stride is derived from ``font.get_height()`` (not a
          hardcoded 26);
       3. a pane shorter than one line of text draws nothing and does
          NOT crash or accidentally return the whole log via
          ``messages[-0:]``.

Headless -- SDL dummy driver -- these guard the layout math, not pixels.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

import inspect
import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((16, 16))  # minimal video surface for Font/Surface


# ---------------------------------------------------------------------------
# A. Sidebar attributes 2-col x 3-row
# ---------------------------------------------------------------------------

class _StubPlayer3Digit:
    """Minimal Player stand-in with 3-digit attribute values plus the
    hooks `Sidebar._derived` consults. We only exercise `_attributes`
    + `_derived` in Phase 3 tests, so the surface area stays small."""

    STR = 100
    CON = 150
    DEX = 999
    INT = 100
    WIS = 100
    PER = 100
    known_spells: dict = {}
    status_effects: dict = {}
    inventory: list = []
    amulet_slot = None

    def get_ac(self):
        return 7

    def get_current_weight(self):
        return 42

    def get_carry_limit(self):
        return 300

    def get_sight_radius(self):
        return 8

    def get_quiz_timer(self, _subj):
        return 16


class _TrackingSurface:
    """Thin wrapper around a real pygame.Surface that records every
    `blit` call. `pygame.Surface.blit` is read-only in pygame-ce (the
    attribute lives on the C type, not the instance) so we can't just
    monkey-patch it. We hand helpers THIS wrapper for `blit` and
    forward every other method they need to the underlying Surface.

    MessageLog.draw calls `pygame.draw.rect(screen, ...)` and
    `pygame.draw.line(screen, ...)` directly; those cdef'd calls
    require a real Surface, so for the log tests we patch out
    `pygame.draw.rect`/`pygame.draw.line` via pytest's monkeypatch
    where needed.
    """

    def __init__(self, w=1600, h=900):
        self._surf = pygame.Surface((w, h))
        self.blits: list[tuple[int, int, int, int]] = []

    def blit(self, source, dest, *args, **kwargs):
        if isinstance(dest, pygame.Rect):
            x, y = dest.x, dest.y
        else:
            x, y = dest[0], dest[1]
        sw, sh = source.get_size()
        self.blits.append((x, y, sw, sh))

    def get_width(self):
        return self._surf.get_width()

    def get_height(self):
        return self._surf.get_height()

    # Fallback so any unexpected method just forwards to the real
    # Surface (keeps unexpected pygame.* calls from exploding).
    def __getattr__(self, name):
        return getattr(self._surf, name)


def _run_attributes(player, pane_x: int = 0, pane_w: int = 248,
                    monkeypatch=None):
    """Call `Sidebar._attributes` against a tracking surface and return
    (sidebar, start_y, end_y, label_blits, value_blits).

    `_header` is replaced with a no-op that just advances y, so the only
    blits in the recording buffer are the six (label, value) cell pairs
    produced by `_attributes` itself. That isolation keeps the test
    independent of any future header redesign.

    We separate label blits from value blits by call order: the helper
    always blits one label THEN one value per cell, so even-indexed
    blits are labels and odd-indexed are values.
    """
    import ui
    screen = _TrackingSurface(w=max(pane_w + 400, 800), h=900)

    sb = ui.Sidebar.__new__(ui.Sidebar)
    sb.screen = screen
    sb.left_x = pane_x
    sb.right_x = pane_x
    sb.x = pane_x
    sb.w = pane_w
    from fantasy_ui import get_font
    sb._fsm = get_font('body', 18)
    sb._fbold = get_font('body', 18, bold=True)
    sb._fhd = get_font('heading', 17)

    # Replace _header with a no-op so the only blits in the buffer are
    # from the 6 attribute cells. We bind directly on the instance so
    # we don't pollute the class for other tests.
    sb._header = lambda text, y: y + 26  # type: ignore[assignment]

    start_y = sb.PAD
    end_y = sb._attributes(player, start_y)

    attr_blits = screen.blits
    assert len(attr_blits) == 12, (
        f"expected 12 blits (6 cells x label+value); got {len(attr_blits)}"
    )
    labels = attr_blits[0::2]
    values = attr_blits[1::2]
    return sb, start_y, end_y, labels, values


def test_sidebar_attributes_2x3_layout_no_overlap_in_cell():
    """With 3-digit stats, label and value within a cell must not
    horizontally overlap."""
    sb, start_y, end_y, labels, values = _run_attributes(_StubPlayer3Digit())

    assert len(labels) == 6
    assert len(values) == 6

    for i, (lb, vb) in enumerate(zip(labels, values)):
        lx, ly, lw, _lh = lb
        vx, vy, vw, _vh = vb
        assert ly == vy, f"cell {i}: label y={ly} != value y={vy}"
        # Horizontal: label's right edge must stay strictly left of the
        # value's left edge. A gap of 1 px is acceptable; 0 or negative
        # means overlap.
        assert lx + lw <= vx, (
            f"cell {i}: label right={lx + lw} overlaps value left={vx}"
        )


def test_sidebar_attributes_cells_stay_in_their_column():
    """No cell may cross the vertical midpoint of the pane — col 1 stays
    strictly left of midpoint, col 2 strictly right of midpoint."""
    pane_x = 0
    pane_w = 248
    sb, _start_y, _end_y, labels, values = _run_attributes(
        _StubPlayer3Digit(), pane_x=pane_x, pane_w=pane_w,
    )
    midpoint = pane_x + pane_w // 2
    # Attribute order in the helper is interleaved:
    #   row 0 = (STR col 1, INT col 2)
    #   row 1 = (CON col 1, WIS col 2)
    #   row 2 = (DEX col 1, PER col 2)
    for i, (lb, vb) in enumerate(zip(labels, values)):
        col = i % 2
        lx, _ly, lw, _lh = lb
        vx, _vy, vw, _vh = vb
        if col == 0:
            # Col-1 cell: value's right edge must stay left of midpoint.
            assert vx + vw <= midpoint, (
                f"cell {i} (col 1): value right={vx + vw} crosses "
                f"midpoint={midpoint}"
            )
        else:
            # Col-2 cell: label's left edge must stay right of midpoint.
            assert lx >= midpoint, (
                f"cell {i} (col 2): label left={lx} crosses "
                f"midpoint={midpoint}"
            )


def test_sidebar_attributes_three_rows_tall():
    """2x3 means three rows of distinct y coords, not two."""
    sb, start_y, end_y, labels, _values = _run_attributes(_StubPlayer3Digit())
    row_ys = sorted({lb[1] for lb in labels})
    assert len(row_ys) == 3, (
        f"expected 3 distinct row y-coords for 2x3 layout; got {row_ys}"
    )
    # The y span of attributes should be ~3 rows * 24 px = 72 px.
    assert row_ys[-1] - row_ys[0] >= 2 * 20, row_ys


def test_sidebar_attributes_column_mapping_matches_spec():
    """Column 1 = STR / CON / DEX, column 2 = INT / WIS / PER (per the
    Phase 3 spec). We can't read the rendered glyphs from blits, but we
    can at least read the attribute list source to pin the order so a
    future refactor can't silently permute the mapping back to 3x2."""
    import ui
    src = inspect.getsource(ui.Sidebar._attributes)
    # Verify the interleaved pairing: STR,INT then CON,WIS then DEX,PER.
    assert src.index("'STR'") < src.index("'INT'") < src.index("'CON'")
    assert src.index("'CON'") < src.index("'WIS'") < src.index("'DEX'")
    assert src.index("'DEX'") < src.index("'PER'")


# ---------------------------------------------------------------------------
# B. "Depth" metric removed
# ---------------------------------------------------------------------------

def test_sidebar_derived_depth_metric_removed():
    """`_derived` must no longer include a `Depth {...}` f-string
    entry — Floor in `_identity` is the sole dungeon-level readout."""
    import ui
    src = inspect.getsource(ui.Sidebar._derived)
    # The old metric was `(f"Depth {dungeon_level}", FP.BODY_TEXT)`.
    # Guard against both f-string and plain-string reintroductions.
    assert 'f"Depth ' not in src, (
        "Sidebar._derived must not reintroduce the Depth metric f-string "
        "(found `f\"Depth `)."
    )
    assert "f'Depth " not in src, (
        "Sidebar._derived must not reintroduce the Depth metric "
        "(single-quoted f-string variant)."
    )


def test_sidebar_identity_still_prints_floor():
    """`_identity` keeps the `Floor N` readout — removing Depth would be
    a regression if Floor also disappeared."""
    import ui
    src = inspect.getsource(ui.Sidebar._identity)
    assert "Floor" in src, (
        "Sidebar._identity must retain the Floor N readout as the sole "
        "dungeon-level display after Depth was removed."
    )


# ---------------------------------------------------------------------------
# C. MessageLog wrapping — robust tokens + zero-row guard + font metrics
# ---------------------------------------------------------------------------

def test_log_wraps_oversized_token():
    """A 60-char no-space token in a narrow log pane must break by
    character so no rendered line exceeds the pane width."""
    from ui import MessageLog
    log = MessageLog()
    long_token = "A" * 60  # unbreakable at a space
    log.add(long_token)

    pane_w = 180  # narrower than the token at font size 20
    pane_h = 400
    text_w = pane_w - MessageLog.PAD_X * 2

    # Pre-wrap directly through the public helper.
    wrapped = MessageLog._wrap(long_token, log._font, text_w)
    assert len(wrapped) >= 2, (
        f"expected a 60-char token to break into multiple lines in a "
        f"{pane_w}px pane; got {wrapped!r}"
    )
    for line in wrapped:
        assert log._font.size(line)[0] <= text_w, (
            f"wrapped line {line!r} ({log._font.size(line)[0]}px) exceeds "
            f"text budget {text_w}px"
        )


def _draw_log_with_tracking(log, w: int, h: int):
    """Run `MessageLog.draw` against a tracking surface with the
    pygame primitive draw calls neutralised. Returns the blits list."""
    screen = _TrackingSurface(w=max(w, 100), h=max(h, 100))

    # Neutralise pygame primitive draws so our wrapper doesn't blow up
    # on the C-typed first-arg check. We only care about blit tracking.
    import pygame as _pg
    saved_rect = _pg.draw.rect
    saved_line = _pg.draw.line
    _pg.draw.rect = lambda *a, **k: None  # type: ignore[assignment]
    _pg.draw.line = lambda *a, **k: None  # type: ignore[assignment]
    try:
        log.draw(screen, 0, 0, w, h)
    finally:
        _pg.draw.rect = saved_rect  # type: ignore[assignment]
        _pg.draw.line = saved_line  # type: ignore[assignment]
    return screen.blits


def test_log_zero_row_guard_does_not_draw():
    """A pane shorter than one line of text must bail out — no text
    blits, no exception, and crucially no `messages[-0:]` slice that
    accidentally selects the entire backlog."""
    from ui import MessageLog
    log = MessageLog()
    log.add("one")
    log.add("two")
    log.add("three")

    # Height much smaller than one line_h.
    blits = _draw_log_with_tracking(log, w=400, h=4)
    assert blits == [], (
        f"expected no text blits on zero-row pane; got {blits}"
    )


def test_log_zero_row_guard_handles_zero_height():
    """A pane with height=0 must not raise and must blit nothing."""
    from ui import MessageLog
    log = MessageLog()
    log.add("hello")
    blits = _draw_log_with_tracking(log, w=400, h=0)
    assert blits == []


def test_log_line_height_from_font_metrics():
    """`line_height()` must respond to the font's metrics — not a
    hardcoded 26. Compute the expected stride from `font.get_height()`
    plus the documented leading constant."""
    from ui import MessageLog
    log = MessageLog()
    expected = log._font.get_height() + MessageLog.LEADING
    assert log.line_height() == expected, (
        f"line_height should derive from font.get_height() + LEADING; "
        f"got {log.line_height()}, expected {expected}"
    )
    # Negative control: a font with a bigger height produces a bigger
    # stride. Swap in a taller font and recompute.
    from fantasy_ui import get_font
    big_font = get_font('body', 32)
    log._font = big_font
    big_expected = big_font.get_height() + MessageLog.LEADING
    assert log.line_height() == big_expected, (
        f"line_height must track font changes; stride stayed at "
        f"{log.line_height()} after swapping to a 32-pt font (expected "
        f"{big_expected})."
    )


def test_log_draw_fits_in_normal_pane():
    """Sanity: at a normal pane size, the log DOES draw blits (so the
    zero-row guard isn't firing when it shouldn't)."""
    from ui import MessageLog
    log = MessageLog()
    log.add("hello world")
    blits = _draw_log_with_tracking(log, w=600, h=300)
    assert blits, "normal-sized pane should produce text blits"
