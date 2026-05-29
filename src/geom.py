"""Geometry helpers for multi-tile entities.

Every existing monster occupies a single (x, y) tile. Bosses with a
`footprint` field (currently only Fafnir) occupy a rectangle anchored
at (x, y) — top-left corner is the anchor per the Cogmind convention.

This module is the single source of truth for "is this point inside
this monster" / "what monster is at this tile" / "how close is this
point to this monster". Direct `m.x == nx and m.y == ny` comparisons
elsewhere in the codebase only work for 1×1 monsters; new code should
use these helpers.

All helpers are O(footprint_w × footprint_h) at worst — typically 1
for normal monsters and 4 for a 2×2 dragon.
"""
from __future__ import annotations

from typing import Iterator, Optional


def occupied_tiles(m) -> Iterator[tuple[int, int]]:
    """Yield every (x, y) tile this monster currently occupies.

    For a 1×1 monster this is just `(m.x, m.y)`. For a 2×2 monster
    anchored at (m.x, m.y) it yields four tiles forming the NW-anchored
    block."""
    fw, fh = getattr(m, 'footprint', (1, 1))
    for dy in range(fh):
        for dx in range(fw):
            yield (m.x + dx, m.y + dy)


def is_at_tile(m, x: int, y: int) -> bool:
    """True if (x, y) is one of the tiles this monster occupies. O(1)."""
    fw, fh = getattr(m, 'footprint', (1, 1))
    return m.x <= x < m.x + fw and m.y <= y < m.y + fh


def monster_at_tile(monsters, x: int, y: int):
    """Return the first alive monster occupying (x, y), or None.

    Replaces `next((m for m in monsters if m.alive and m.x == x and
    m.y == y), None)` everywhere — that pattern silently misses every
    tile of a multi-tile monster except the anchor."""
    for m in monsters:
        if m.alive and is_at_tile(m, x, y):
            return m
    return None


def chebyshev_distance(px: int, py: int, m) -> int:
    """Chebyshev (king-move) distance from (px, py) to the nearest
    tile of m. For a 1×1 monster this is `max(abs(m.x-px), abs(m.y-py))`.
    For a 2×2 monster it's the distance to whichever of the 4 tiles is
    closest."""
    fw, fh = getattr(m, 'footprint', (1, 1))
    if fw == 1 and fh == 1:
        return max(abs(m.x - px), abs(m.y - py))
    return min(max(abs(mx - px), abs(my - py))
               for mx, my in occupied_tiles(m))


def manhattan_distance(px: int, py: int, m) -> int:
    """Manhattan distance from (px, py) to the nearest tile of m.
    Used wherever the existing code wrote `abs(m.x-px) + abs(m.y-py)`."""
    fw, fh = getattr(m, 'footprint', (1, 1))
    if fw == 1 and fh == 1:
        return abs(m.x - px) + abs(m.y - py)
    return min(abs(mx - px) + abs(my - py)
               for mx, my in occupied_tiles(m))


def is_adjacent(px: int, py: int, m) -> bool:
    """True if (px, py) is Chebyshev-1 adjacent to ANY tile of m
    (and not standing on m itself)."""
    if is_at_tile(m, px, py):
        return False  # standing on the monster doesn't count as adjacent
    return chebyshev_distance(px, py, m) <= 1


def any_tile_in_set(m, tiles: set) -> bool:
    """True if ANY occupied tile of m is in `tiles` (e.g., FOV set).
    Used wherever the existing code wrote `(m.x, m.y) in visible`."""
    fw, fh = getattr(m, 'footprint', (1, 1))
    if fw == 1 and fh == 1:
        return (m.x, m.y) in tiles
    return any(t in tiles for t in occupied_tiles(m))


def all_occupied_tiles(monsters, exclude=None) -> set[tuple[int, int]]:
    """Build the set of every tile occupied by any alive monster in
    `monsters`, optionally skipping one monster (typically `self` when
    the caller is the monster choosing where to move).

    Replaces the very common pattern:
        occupied = {(m.x, m.y) for m in monsters if m.alive}
    which silently misses every tile of multi-tile monsters except
    their anchor."""
    out: set[tuple[int, int]] = set()
    for m in monsters:
        if not m.alive or m is exclude:
            continue
        for t in occupied_tiles(m):
            out.add(t)
    return out


def can_footprint_fit(dungeon, x: int, y: int, footprint: tuple[int, int],
                      occupied: Optional[set] = None,
                      ignore_monster=None) -> bool:
    """True if a monster with `footprint` anchored at (x, y) could
    legally stand there: every footprint tile is in-bounds, walkable,
    and not occupied by another monster (unless that monster is
    `ignore_monster` — used when the monster is moving and we ignore
    its own current tiles)."""
    fw, fh = footprint
    for dy in range(fh):
        for dx in range(fw):
            tx, ty = x + dx, y + dy
            if not dungeon.in_bounds(tx, ty):
                return False
            if not dungeon.is_walkable(tx, ty):
                return False
            if occupied and (tx, ty) in occupied:
                return False
    return True
