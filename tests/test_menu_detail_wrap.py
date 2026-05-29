"""Tests for the multi-line `wrap_detail` opt-in on `draw_menu`.

Bug being fixed: icon-style menus (prayer, magic, identify, scrolls,
cook, etc.) silently truncate long detail text with "..." because the
icon-row branch of `draw_menu` calls `fit_text` instead of wrapping.
Players never see the rest of the prayer lore / item description.

The opt-in fix: callers pass `wrap_detail=True`. Inside `draw_menu`,
the icon-row branch wraps the detail with `wrap_text`, caches the
result on the entry dict, and grows the row height by 18 px per
extra line so the next row doesn't overlap.

This file covers:
1. `fit_text` truncates long input with "..." (the buggy default).
2. `wrap_text` returns multiple lines that all fit individually.
3. `draw_menu` exposes the `wrap_detail` parameter.
4. The prayer menu opts in (`wrap_detail=True` in its draw call).
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# A tiny font stub that returns predictable widths: 8 px per character.
# Lets the tests check wrap/fit behaviour without a real Pygame font.
class _StubFont:
    def __init__(self, char_w: int = 8, line_h: int = 18):
        self._cw = char_w
        self._lh = line_h

    def size(self, text: str) -> tuple[int, int]:
        return (len(text) * self._cw, self._lh)

    def get_height(self) -> int:
        return self._lh


# ---------------------------------------------------------------------------
# Helper behaviour: confirm the old truncation path vs the new wrap path
# ---------------------------------------------------------------------------

def test_fit_text_truncates_long_input_with_ellipsis():
    """`fit_text` is the OLD path. It should produce a "..." truncation
    for text wider than the budget — this is what the player was seeing
    in the prayer menu."""
    from fantasy_ui import fit_text
    font = _StubFont(char_w=8)
    long_text = "Intercession of the Mother of God; tradition invokes her in moments of mortal danger."
    # Budget of 240 px = 30 chars including the "..."
    out = fit_text(long_text, font, 240)
    assert out.endswith("..."), f"expected ellipsis truncation; got {out!r}"
    # And the result must fit in the budget
    assert font.size(out)[0] <= 240


def test_wrap_text_breaks_long_input_into_multiple_lines():
    """`wrap_text` is the NEW path used when `wrap_detail=True`. It
    splits long detail into multiple lines that each fit in the budget,
    so no information is lost."""
    from fantasy_ui import wrap_text
    font = _StubFont(char_w=8)
    long_text = "Intercession of the Mother of God; tradition invokes her in moments of mortal danger."
    lines = wrap_text(long_text, font, 240)
    assert len(lines) >= 2, (
        f"expected multi-line wrap of long text; got 1 line: {lines!r}"
    )
    # Every produced line must fit in the budget.
    for line in lines:
        assert font.size(line)[0] <= 240, (
            f"wrapped line {line!r} exceeds {240}px budget"
        )
    # Joining back must reproduce the original (modulo whitespace).
    assert " ".join(lines) == long_text


def test_wrap_text_passes_short_input_through_as_single_line():
    """Short detail shouldn't be split unnecessarily."""
    from fantasy_ui import wrap_text
    font = _StubFont(char_w=8)
    short = "Universal."
    lines = wrap_text(short, font, 240)
    assert lines == [short]


# ---------------------------------------------------------------------------
# `draw_menu` API surface — confirm the new kwarg exists and the prayer
# menu opts in. Source-level regression so the opt-in can't quietly
# disappear in a future edit.
# ---------------------------------------------------------------------------

def test_draw_menu_exposes_wrap_detail_parameter():
    """`draw_menu` must accept `wrap_detail` as a keyword argument."""
    from fantasy_ui import draw_menu
    sig = inspect.signature(draw_menu)
    assert "wrap_detail" in sig.parameters, (
        "draw_menu should expose `wrap_detail` so callers can opt into "
        "multi-line detail wrapping in icon-row menus"
    )
    # Default must remain False to preserve the current single-line
    # behaviour for menus that haven't opted in.
    assert sig.parameters["wrap_detail"].default is False


def test_draw_menu_icon_branch_uses_wrap_detail():
    """The icon-row measurement code must consult `wrap_detail` to
    grow the row and cache the wrap result. Without this, opting in
    would render multi-line detail that overlaps the next row."""
    from fantasy_ui import draw_menu
    src = inspect.getsource(draw_menu)
    assert "wrap_detail" in src, "wrap_detail must be referenced inside draw_menu"
    # Sanity: the icon-row branch calls wrap_text on the detail
    assert "wrap_text(entry['detail']" in src, (
        "icon-row branch should call wrap_text when wrap_detail is set"
    )
    # And caches the result on the entry so the render loop can reuse it
    assert "_wrapped_detail" in src, (
        "wrap result should be cached on the entry as `_wrapped_detail` "
        "so measurement and render agree on the row height"
    )


def test_prayer_menu_opts_into_wrap_detail():
    """`_draw_prayer_menu` must pass `wrap_detail=True` so the lore
    descriptions stop being chopped with '...'."""
    from game_render import RenderMixin
    src = inspect.getsource(RenderMixin._draw_prayer_menu)
    assert "wrap_detail=True" in src, (
        "_draw_prayer_menu must opt into wrap_detail so prayer lore "
        "isn't truncated mid-sentence"
    )


# ---------------------------------------------------------------------------
# Integration smoke test: simulate the measurement-loop behaviour with
# a stub font and confirm a long-detail icon row gets a taller height.
# ---------------------------------------------------------------------------

def test_measurement_grows_row_for_wrapped_detail():
    """Re-implement the row-growth formula from `draw_menu`'s
    measurement loop. Long detail at narrow width must yield >1 line
    and the row should grow by 18 px per extra line."""
    from fantasy_ui import wrap_text, _ICON_ROW_H
    font = _StubFont(char_w=8)
    bw = 820
    # Mirror the formula in draw_menu measurement: bw - 130
    icon_detail_wrap_w = bw - 130
    long_text = (
        "Intercession of the Mother of God; tradition invokes her in "
        "moments of mortal danger, when every other recourse has failed."
    )
    wrapped = wrap_text(long_text, font, icon_detail_wrap_w)
    base_h = _ICON_ROW_H
    grown_h = base_h + max(0, len(wrapped) - 1) * 18
    if len(wrapped) > 1:
        assert grown_h > base_h, (
            f"row should grow when detail wraps to {len(wrapped)} lines; "
            f"base={base_h}, grown={grown_h}"
        )
    # Sanity: every wrapped line fits the budget
    for line in wrapped:
        assert font.size(line)[0] <= icon_detail_wrap_w
