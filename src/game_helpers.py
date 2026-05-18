"""Pure helper functions extracted from main.Game.

All functions here are stateless (no `self`); they were `@staticmethod`s on
the `Game` class. They remain accessible from `Game` via thin static aliases
in `main.py` so existing `self._foo(...)` call sites work unchanged.
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


def migrate_buc_item(item) -> None:
    """Patch missing base-Item fields onto items from old saves."""
    if not hasattr(item, 'buc'):
        item.buc = 'cursed' if item.__dict__.get('cursed', False) else 'uncursed'
    if not hasattr(item, 'buc_known'):
        item.buc_known = False
    if not hasattr(item, 'identified'):
        item.identified = True  # old items without the field are assumed known
    if not hasattr(item, 'unidentified_name'):
        item.unidentified_name = getattr(item, 'name', '???')
    if not hasattr(item, 'id_level'):
        # Old saves: identified items are fully known (id_level=5); unknown stay at 0.
        item.id_level = 5 if getattr(item, 'identified', True) else 0
    if not hasattr(item, 'mastery_blessing'):
        item.mastery_blessing = None


def cycle_tab(current: int, direction: int, n_tabs: int, has_items: Callable[[int], bool]) -> int:
    """Advance *current* tab by *direction* (+1/-1), skipping empty tabs.

    *has_items* is called with a tab index and must return True if that tab has at
    least one item. Returns the new tab index (unchanged if every other tab is empty).
    """
    original = current
    for _ in range(n_tabs - 1):
        current = (current + direction) % n_tabs
        if has_items(current):
            return current
    return original  # all others empty — stay on original tab


def throw_crosses_tile(px: int, py: int, tx: int, ty: int, ax: int, ay: int) -> bool:
    """Does a thrown item's path from (px,py) to (tx,ty) pass through (ax,ay)?

    Bresenham line: returns True if the altar tile is on the path.
    """
    dx, dy = abs(tx - px), abs(ty - py)
    sx = 1 if tx > px else -1
    sy = 1 if ty > py else -1
    err = dx - dy
    cx, cy = px, py
    while True:
        if (cx, cy) == (ax, ay):
            return True
        if cx == tx and cy == ty:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            cx += sx
        if e2 < dx:
            err += dx
            cy += sy
    return False


def wand_tier_duration(base: int, tier: int) -> int:
    """Scale a wand's effect duration by its tier. T1=base, T5=base*2.5."""
    return max(2, int(base * (0.5 + tier * 0.5)))


def fix_name_case(name: str) -> str:
    """Title-case the name only if it's entirely lowercase (avoids breaking 'STR+1')."""
    if name == name.lower():
        return name.title()
    return name


def a_or_an(name: str) -> str:
    """Return 'a Name' or 'an Name' based on the first letter."""
    if not name:
        return name
    first = name.lstrip('{').lstrip()
    article = 'an' if first[0:1].lower() in 'aeiou' else 'a'
    return f"{article} {name}"


def fit_text(text: str, font: 'pygame.font.Font', max_w: int) -> str:
    """Truncate text with ellipsis if it exceeds max_w pixels.

    Re-exports text_layout.truncate_label so there's a single canonical
    implementation. The fantasy_ui.fit_text (older, uses '...' ellipsis)
    is left in place for menu chrome that depends on it.
    """
    from text_layout import truncate_label
    return truncate_label(text, max_w, font)


def wrap_text(text: str, font: 'pygame.font.Font', max_w: int) -> list[str]:
    """Break text into lines that fit within max_w pixels.

    Re-exports text_layout.wrap_lines. Single source of truth.
    """
    from text_layout import wrap_lines
    return wrap_lines(text, max_w, font)
