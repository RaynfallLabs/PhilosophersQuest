"""Tests for src/text_layout.py — the text containment primitives.

These verify the foundation that prevents text spillover across all panels.
A bug here ripples to every screen, so the rules are checked explicitly:

  - wrap_lines never produces a line wider than max_width
  - wrap_lines preserves all input characters (no truncation)
  - truncate_label respects max_width and ends with the ellipsis
  - fit_columns distributes available_width across flex columns correctly
  - fit_columns degrades gracefully when minimums exceed available
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame
pygame.init()
pygame.font.init()


def _font():
    return pygame.font.SysFont('arial', 14)


# ---------------------------------------------------------------------------
# wrap_lines
# ---------------------------------------------------------------------------

def test_wrap_lines_short_text_returns_single_line():
    from text_layout import wrap_lines
    out = wrap_lines("hi there", 400, _font())
    assert out == ["hi there"]


def test_wrap_lines_empty_returns_one_empty():
    from text_layout import wrap_lines
    assert wrap_lines("", 200, _font()) == ['']


def test_wrap_lines_never_exceeds_max_width():
    from text_layout import wrap_lines
    f = _font()
    text = ("The quick brown fox jumps over the lazy dog. " * 4).strip()
    for max_w in (80, 120, 200, 400):
        lines = wrap_lines(text, max_w, f)
        for ln in lines:
            assert f.size(ln)[0] <= max_w, f"line '{ln}' exceeds {max_w}px"


def test_wrap_lines_preserves_all_words():
    from text_layout import wrap_lines
    text = "alpha beta gamma delta epsilon zeta eta theta iota kappa"
    lines = wrap_lines(text, 60, _font())
    flat = ' '.join(lines).split()
    assert flat == text.split()


def test_wrap_lines_preserves_explicit_newlines():
    from text_layout import wrap_lines
    text = "para one\npara two\n\npara three"
    lines = wrap_lines(text, 400, _font())
    assert "para one" in lines
    assert "para two" in lines
    assert "para three" in lines
    # The double-newline yields one empty separator line
    assert '' in lines


def test_wrap_lines_breaks_overlong_word_by_chars():
    """A single word wider than max_width must still not overflow."""
    from text_layout import wrap_lines
    f = _font()
    big_word = "supercalifragilisticexpialidocious"
    lines = wrap_lines(big_word, 50, f)
    for ln in lines:
        assert f.size(ln)[0] <= 50
    # All characters of the long word must appear in the output, in order
    assert ''.join(lines) == big_word


# ---------------------------------------------------------------------------
# truncate_label
# ---------------------------------------------------------------------------

def test_truncate_label_short_passes_through():
    from text_layout import truncate_label
    out = truncate_label("hi", 200, _font())
    assert out == "hi"


def test_truncate_label_long_adds_ellipsis():
    from text_layout import truncate_label
    f = _font()
    out = truncate_label("a very long label that should be truncated", 50, f)
    assert out.endswith('…')
    assert f.size(out)[0] <= 50


def test_truncate_label_uses_custom_ellipsis():
    from text_layout import truncate_label
    out = truncate_label("alpha beta gamma delta", 60, _font(), ellipsis='...')
    assert out.endswith('...')


def test_truncate_label_zero_width_returns_empty():
    from text_layout import truncate_label
    out = truncate_label("anything", 1, _font())
    assert out == ''


# ---------------------------------------------------------------------------
# fit_columns
# ---------------------------------------------------------------------------

def test_fit_columns_fixed_only_sums_to_min():
    from text_layout import Column, fit_columns
    cols = [
        Column('A', 100, flex=0),
        Column('B', 50,  flex=0),
        Column('C', 30,  flex=0),
    ]
    out = fit_columns(cols, 500)
    assert out == [100, 50, 30]
    assert sum(out) <= 500


def test_fit_columns_flex_takes_extra_space():
    from text_layout import Column, fit_columns
    cols = [
        Column('Name',  100, flex=0),
        Column('Flex',  100, flex=1),
    ]
    widths = fit_columns(cols, 300)
    # Fixed gets 100; flex gets its min 100 + leftover 100 = 200
    assert widths == [100, 200]


def test_fit_columns_multiple_flex_split_proportionally():
    from text_layout import Column, fit_columns
    cols = [
        Column('A', 50, flex=1),
        Column('B', 50, flex=3),
    ]
    widths = fit_columns(cols, 250)
    # mins total 100; extra = 150; flex weights 1 + 3 = 4
    # A: 50 + (150 * 1/4) = 50 + 37 = 87
    # B: 50 + (150 * 3/4) = 50 + 112 = 162
    assert widths[0] == 87 or widths[0] == 88   # integer rounding wiggle
    assert widths[1] == 162 or widths[1] == 161
    assert sum(widths) <= 250


def test_fit_columns_overflow_shrinks_proportionally():
    """If sum of min_w exceeds available_width, columns shrink uniformly."""
    from text_layout import Column, fit_columns
    cols = [
        Column('A', 200, flex=0),
        Column('B', 200, flex=0),
        Column('C', 200, flex=0),
    ]
    widths = fit_columns(cols, 300)
    assert sum(widths) <= 305   # may round slightly over due to per-col max(1, ...)
    # All should shrink, none zero
    assert all(w > 0 for w in widths)


def test_fit_columns_empty_returns_empty():
    from text_layout import fit_columns
    assert fit_columns([], 500) == []
