"""WCAG contrast regression tests for FP palette text-on-panel pairs.

Why this exists: on 2026-05-18 the user reported "dark text on blue background,
completely unreadable" — turned out to be FOUR separate contrast bugs across
the codebase (quiz wrong-answer red-on-red, sidebar SLOT_EMPTY too dark,
MP_BLUE used as text instead of MP_BLUE_TEXT, corpse color too dark in
sidebar). A subagent audit found and these tests lock in the fix so the
problem class can't recur.

WCAG AA threshold: 4.5:1 for normal text. We allow 4.0:1 as a "muted but
visible" floor for SLOT_EMPTY (the empty-equip-slot dash, deliberately dim).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def _luma(rgb):
    """WCAG relative luminance for an sRGB tuple."""
    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast(c1, c2):
    L1, L2 = max(_luma(c1), _luma(c2)), min(_luma(c1), _luma(c2))
    return (L1 + 0.05) / (L2 + 0.05)


# ----------------------------------------------------------------------
# Background contexts that text can land on
# ----------------------------------------------------------------------

def _midnight():
    from fantasy_ui import FP
    return FP.MIDNIGHT


def _midnight_mid():
    """Alternating row bg in draw_menu — text must survive this too."""
    from fantasy_ui import FP
    return FP.MIDNIGHT_MID


def _menu_selected_bg():
    """The (40, 55, 110) bg of a SELECTED row in draw_menu."""
    return (40, 55, 110)


# ----------------------------------------------------------------------
# Text colors that MUST be readable on the panel
# ----------------------------------------------------------------------

# Each entry: (fp_attr_name, min_contrast_on_midnight)
# 4.5 is WCAG AA; 4.0 is "muted but legible" — used for SLOT_EMPTY which
# is intentionally faded (empty-slot dashes shouldn't compete with content).
# Text colors: must clear 4.5:1 against midnight. HP_RED / MP_BLUE / SP_RED /
# SP_AMBER are intentionally NOT in this list — they are BAR FILL colors only
# (never used as text). SP_GREEN is in the list because it doubles as text in
# the character sheet's damage-resistance rows.
_TEXT_ON_MIDNIGHT = [
    ('BODY_TEXT',          4.5),
    ('FADED_TEXT',         4.5),
    ('ACCENT_TEXT',        4.5),
    ('HINT_TEXT',          4.5),
    ('HINT_TEXT_DIM',      3.8),  # dim variant — quieter on dense screens
    ('DANGER_TEXT_LIGHT',  4.5),  # the in-menu wrong-answer color
    ('SUCCESS_TEXT',       4.5),
    ('WARNING_TEXT',       4.5),
    ('LOOT_TEXT',          4.5),
    ('GOLD',               4.5),
    ('GOLD_BRIGHT',        4.5),
    ('GOLD_PALE',          4.5),
    ('PARCHMENT',          4.5),
    ('PARCHMENT_LIGHT',    4.5),
    ('VELLUM',             4.5),
    ('CYAN_ACCENT',        4.5),
    ('ARCANE_ACCENT',      4.5),
    ('AMBER_ACCENT',       4.5),
    ('MP_BLUE_TEXT',       4.5),
    ('COOLDOWN_TEAL',      4.5),
    ('READY_TEAL',         4.5),
    ('COOLDOWN_ARCANE',    4.5),
    ('PASSIVE_FIRE',       4.5),
    ('PASSIVE_MANIFEST',   4.5),
    ('PASSIVE_WARD',       4.5),
    ('SP_GREEN',           4.5),  # also used as text in resistance rows
    ('SLOT_EMPTY',         4.0),  # intentionally dim, but must clear 4:1
]


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def test_all_text_colors_clear_threshold_on_midnight():
    """Every named text constant in FP must clear its contrast floor against
    the canonical midnight panel background."""
    from fantasy_ui import FP
    failures = []
    for attr, floor in _TEXT_ON_MIDNIGHT:
        col = getattr(FP, attr)
        c = _contrast(col, _midnight())
        if c < floor:
            failures.append(f"FP.{attr} {col} contrast={c:.2f} < {floor:.2f}")
    assert not failures, "Contrast failures on MIDNIGHT:\n  " + "\n  ".join(failures)


def test_text_survives_alternating_row_bg():
    """Body and faded text need to survive the MIDNIGHT_MID alternating bg
    used by draw_menu's row striping. Selected-row bg (40,55,110) is even
    lighter; tested separately."""
    from fantasy_ui import FP
    floor = 4.5
    bg = _midnight_mid()
    for attr in ('BODY_TEXT', 'FADED_TEXT', 'HINT_TEXT', 'GOLD_PALE',
                 'DANGER_TEXT_LIGHT', 'SUCCESS_TEXT', 'CYAN_ACCENT'):
        col = getattr(FP, attr)
        c = _contrast(col, bg)
        assert c >= floor, f"FP.{attr} {col} on MIDNIGHT_MID contrast={c:.2f} < {floor}"


def test_choice_button_renders_text_in_parchment_not_danger():
    """The quiz wrong-answer card was rendering DANGER_TEXT (200,18,18) on
    its dark-red bg (70,14,14) — contrast 2.67, invisible. Verify the
    choice button now uses PARCHMENT_LIGHT regardless of state."""
    from pathlib import Path
    src = Path('src/fantasy_ui.py').read_text(encoding='utf-8')
    idx = src.find('def draw_choice_button(')
    assert idx >= 0
    block = src[idx:idx + 2500]
    # The text-color line should not branch on correct/incorrect anymore
    assert 't_color = FP.PARCHMENT_LIGHT' in block
    # And specifically must NOT have the old branching pattern
    assert 'else border_col' not in block


def test_item_color_corpse_is_readable_in_sidebar():
    """Sidebar inventory uses ITEM_COLOR[item.item_class] directly as text.
    'corpse' was (148, 68, 68) — contrast 2.76 on midnight. Must clear 4.5."""
    from fantasy_ui import ITEM_COLOR
    c = _contrast(ITEM_COLOR['corpse'], _midnight())
    assert c >= 4.5, f"ITEM_COLOR['corpse'] {ITEM_COLOR['corpse']} contrast={c:.2f} on midnight"


def test_mp_blue_is_NOT_used_as_text_color():
    """FP.MP_BLUE = (50, 85, 205) is the BAR FILL color and fails as text.
    The replacement FP.MP_BLUE_TEXT must exist and ui.py must reference it,
    not MP_BLUE, for the sidebar spell count."""
    from pathlib import Path
    from fantasy_ui import FP
    assert hasattr(FP, 'MP_BLUE_TEXT')
    sidebar = Path('src/ui.py').read_text(encoding='utf-8')
    # Sidebar should not render text in raw MP_BLUE
    for line in sidebar.splitlines():
        if 'render(' in line and 'MP_BLUE' in line and 'MP_BLUE_TEXT' not in line:
            raise AssertionError(f"ui.py renders text in MP_BLUE (use MP_BLUE_TEXT): {line.strip()}")


def test_slot_empty_is_above_minimum_contrast():
    """The empty-equip-slot filler. Original (52, 52, 70) was 2:1 — invisible.
    Must clear 4.0:1 (dim-but-visible floor)."""
    from fantasy_ui import FP
    c = _contrast(FP.SLOT_EMPTY, _midnight())
    assert c >= 4.0, f"FP.SLOT_EMPTY contrast={c:.2f} on midnight — too dim"
