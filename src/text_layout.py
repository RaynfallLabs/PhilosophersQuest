"""Text containment helpers — the source of truth for fitting text to panels.

The audit at tools/audit/deliverables/beauty_screen_catalog.md flagged
inconsistent text containment across screens — some screens truncate
content with ellipsis (loses information), others overflow the panel
boundary at smaller resolutions. This module gives the renderer ONE
correct way to do each thing.

Three functions cover the cases:

  - wrap_lines(text, max_width, font)
        Word-wraps `text` so each resulting line's rendered width is <=
        `max_width`. Use for CONTENT (prose, hint text, descriptions).
        Returns a list of strings. Never truncates: long words break to
        their own line at full width.

  - fit_columns(rows, available_width, columns, font)
        Resize a row of column widths to fit `available_width`. Columns
        flagged 'flex' get the leftover space proportionally. Use for
        TABLES (Kit panel, character sheet, equip menu).

  - truncate_label(s, max_width, font, ellipsis='...')
        Truncate a LABEL (single-line, non-essential string) with
        ellipsis so it fits in `max_width`. Use only for labels —
        tab strips, button text, column headers. Never for content.

All three are pure functions of (text/rows, width, font); no rendering
side-effects, easy to unit-test without pygame init.
"""
from __future__ import annotations

from typing import NamedTuple


def wrap_lines(text: str, max_width: int, font) -> list[str]:
    """Break `text` into lines that each render at <= `max_width` pixels.

    Word-aware: splits on whitespace, packs as many words as fit, then
    breaks. Preserves \\n in the input as forced line breaks. Long words
    that don't fit on their own line get broken character-by-character
    so they still don't overflow.

    Returns at least one entry; empty input returns [''].
    """
    if not text:
        return ['']
    out: list[str] = []
    for paragraph in text.split('\n'):
        if not paragraph:
            out.append('')
            continue
        words = paragraph.split(' ')
        line = ''
        for w in words:
            candidate = w if not line else f"{line} {w}"
            if font.size(candidate)[0] <= max_width:
                line = candidate
                continue
            # Candidate too wide — flush current line if any, then handle w
            if line:
                out.append(line)
                line = ''
            # Word itself may be wider than max_width — break by characters
            if font.size(w)[0] > max_width:
                buf = ''
                for ch in w:
                    if font.size(buf + ch)[0] <= max_width:
                        buf += ch
                    else:
                        if buf:
                            out.append(buf)
                        buf = ch
                line = buf
            else:
                line = w
        if line:
            out.append(line)
    return out


def truncate_label(s: str, max_width: int, font, ellipsis: str = '…') -> str:
    """Truncate `s` with `ellipsis` so it fits in `max_width` pixels.

    For LABELS only (tab names, column headers, button text). Never use
    for body content — wrap_lines does that without losing information.

    If the string already fits, returns it unchanged. If even the ellipsis
    won't fit, returns the empty string.
    """
    if font.size(s)[0] <= max_width:
        return s
    ell_w = font.size(ellipsis)[0]
    if ell_w >= max_width:
        return ''
    target = max_width - ell_w
    # Binary search for the longest prefix that fits
    lo, hi = 0, len(s)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if font.size(s[:mid])[0] <= target:
            lo = mid
        else:
            hi = mid - 1
    return s[:lo].rstrip() + ellipsis


# ----------------------------------------------------------------------
# Column fitting
# ----------------------------------------------------------------------

class Column(NamedTuple):
    """One column in a table layout.

    Attributes:
      label:    column header text (for fit-checking the header itself)
      min_w:    minimum width in pixels (table won't shrink below this)
      flex:     0 = fixed width (use min_w), 1+ = flexible weight share
      align:    'left' or 'right'
    """
    label: str
    min_w: int
    flex: int = 0
    align: str = 'left'


def fit_columns(columns: list[Column], available_width: int) -> list[int]:
    """Return list of pixel widths matching `columns`, summing to at most
    `available_width`.

    Fixed columns (flex=0) get exactly `min_w`. Remaining space is divided
    among flex columns proportionally to their `flex` weight. If the sum
    of `min_w` already exceeds available, all columns shrink uniformly
    (the caller may want to drop columns instead).
    """
    n = len(columns)
    if n == 0:
        return []

    fixed_total = sum(c.min_w for c in columns if c.flex == 0)
    flex_min_total = sum(c.min_w for c in columns if c.flex > 0)
    flex_weight_total = sum(c.flex for c in columns if c.flex > 0)

    if fixed_total + flex_min_total > available_width:
        # Everything must shrink — distribute available proportionally to min_w
        total_min = fixed_total + flex_min_total
        if total_min == 0:
            return [0] * n
        return [max(1, int(c.min_w * available_width / total_min)) for c in columns]

    extra = available_width - fixed_total - flex_min_total
    widths: list[int] = []
    if flex_weight_total > 0:
        for c in columns:
            if c.flex == 0:
                widths.append(c.min_w)
            else:
                widths.append(c.min_w + (extra * c.flex) // flex_weight_total)
    else:
        # No flex columns — just use min widths
        widths = [c.min_w for c in columns]
    return widths


# ----------------------------------------------------------------------
# Tab strip overflow (Phase 2 beautification, 2026-10-04)
# ----------------------------------------------------------------------


def tab_strip_window(widths: list[int], active: int, available_width: int,
                     gap: int = 6, arrow_w: int = 18) -> dict:
    """Pick the scroll window for a tab strip whose cumulative width may
    exceed its container.

    Pure math — no pygame — so the renderer and tests can share it.

    Args:
        widths: pre-measured width (px) of each tab's rendered box.
        active: index of the active tab; the window must contain it.
        available_width: total pixels the strip may consume.
        gap: px gap between adjacent tabs.
        arrow_w: px reserved for a ``◀`` or ``▶`` affordance when the
                 window scrolls past either edge.

    Returns a dict with:
        overflow (bool): True when the full strip is wider than available.
        start (int):   first visible tab index.
        end (int):     one past the last visible index (slice bound).
        show_left_arrow (bool): a ``◀`` arrow should be drawn.
        show_right_arrow (bool): a ``▶`` arrow should be drawn.

    When ``overflow`` is False, ``start=0`` and ``end=len(widths)`` and
    both arrows are hidden. When overflow is True, the window is chosen so
    the active tab is included and (when it fits) roughly centred.
    """
    n = len(widths)
    if n == 0:
        return {'overflow': False, 'start': 0, 'end': 0,
                'show_left_arrow': False, 'show_right_arrow': False}

    total_w = sum(widths) + gap * max(0, n - 1)
    if total_w <= available_width:
        return {'overflow': False, 'start': 0, 'end': n,
                'show_left_arrow': False, 'show_right_arrow': False}

    at = max(0, min(active, n - 1))
    inner_w = max(1, available_width - 2 * arrow_w - gap * 2)

    def _end_from(s: int) -> int:
        """Return one-past-last index that still fits starting at s."""
        used = 0
        for i in range(s, n):
            used += widths[i]
            if i > s:
                used += gap
            if used > inner_w:
                return i
        return n

    # Smallest valid start = walk backward from `at` while the window
    # that begins one tab earlier still contains the active tab.
    start = at
    while start > 0 and _end_from(start - 1) > at:
        start -= 1

    # Prefer centring: nudge start forward while the active tab stays
    # visible and we have more tabs before it than after.
    while start < at and _end_from(start + 1) > at:
        shown_before = at - start
        shown_after = _end_from(start) - at - 1
        if shown_before <= shown_after:
            break
        start += 1

    end = _end_from(start)
    show_left = start > 0
    show_right = end < n
    return {
        'overflow': True,
        'start': start,
        'end': end,
        'show_left_arrow': show_left,
        'show_right_arrow': show_right,
    }
