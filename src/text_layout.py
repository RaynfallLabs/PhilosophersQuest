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


def text_block_height(lines: int, line_h: int, line_gap: int = 0) -> int:
    """Pixel height for `lines` lines of text with `line_h` line height
    and optional `line_gap` between lines."""
    if lines <= 0:
        return 0
    return lines * line_h + max(0, lines - 1) * line_gap
