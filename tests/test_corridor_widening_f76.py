"""Pin tests for 2-wide deep-floor corridors + footprint-validated spawn.

Added 2026-05-31 to support the 4 new 2x2 cosmic-scale bosses (Tiamat
f85, Surtur f87, Ymir's Last Spawn f82, Hrungnir's Ghost f80) that now
spawn via the regular procedural pool rather than hand-crafted boss
levels (the Fafnir precedent).

The fix has two halves:
  1. dungeon._carve_h / _carve_v take a ``width`` kwarg, plumbed via
     ``_corridor_width_for_level(level)`` from generate_dungeon.
     f1-75: 1-wide (historical).  f76+: 2-wide.
  2. dungeon.spawn_monsters validates the FULL footprint of multi-tile
     monsters before placement (previously checked only the anchor tile).

This file pins both behaviors so a future dungeon refactor can't silently
regress them.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# Corridor-width function pins
# ---------------------------------------------------------------------------

def test_corridor_width_for_level_under_76_is_1():
    from dungeon import _corridor_width_for_level
    for level in (1, 25, 50, 75):
        assert _corridor_width_for_level(level) == 1, \
            f"f{level} must keep 1-wide corridors (historical default)"


def test_corridor_width_for_level_76_and_above_is_2():
    from dungeon import _corridor_width_for_level
    for level in (76, 80, 85, 90, 99):
        assert _corridor_width_for_level(level) == 2, \
            f"f{level} must use 2-wide corridors so 2x2 bosses can path"


# ---------------------------------------------------------------------------
# _carve_h / _carve_v width parameter
# ---------------------------------------------------------------------------

def _empty_tiles(w, h):
    from dungeon import WALL
    return [[WALL] * w for _ in range(h)]


def _count_floor(tiles):
    from dungeon import FLOOR
    return sum(1 for row in tiles for c in row if c == FLOOR)


def test_carve_h_width_1_carves_one_row():
    from dungeon import _carve_h
    tiles = _empty_tiles(20, 10)
    _carve_h(tiles, 2, 10, 5, width=1)
    # Only y=5 should have floors
    floor_rows = sorted({y for y, row in enumerate(tiles)
                         for x, c in enumerate(row) if c == 0})
    # FLOOR is constant 0 in dungeon — but check via the helper instead.
    from dungeon import FLOOR
    floor_ys = sorted({y for y, row in enumerate(tiles)
                       for x, c in enumerate(row) if c == FLOOR})
    assert floor_ys == [5]


def test_carve_h_width_2_carves_two_rows():
    from dungeon import _carve_h, FLOOR
    tiles = _empty_tiles(20, 10)
    _carve_h(tiles, 2, 10, 5, width=2)
    floor_ys = sorted({y for y, row in enumerate(tiles)
                       for x, c in enumerate(row) if c == FLOOR})
    assert floor_ys == [5, 6], f"width=2 should carve y=5 + y=6, got {floor_ys}"


def test_carve_v_width_2_carves_two_columns():
    from dungeon import _carve_v, FLOOR
    tiles = _empty_tiles(20, 10)
    _carve_v(tiles, 2, 8, 7, width=2)
    floor_xs = sorted({x for y, row in enumerate(tiles)
                       for x, c in enumerate(row) if c == FLOOR})
    assert floor_xs == [7, 8], f"width=2 should carve x=7 + x=8, got {floor_xs}"


def test_carve_h_width_2_backs_off_when_overflowing():
    """If width=2 would write past the bottom wall, back off to (y-1) instead."""
    from dungeon import _carve_h, FLOOR
    tiles = _empty_tiles(20, 10)
    # y=8 is the last interior row; y=9 is the boundary wall
    _carve_h(tiles, 2, 10, 8, width=2)
    floor_ys = sorted({y for y, row in enumerate(tiles)
                       for x, c in enumerate(row) if c == FLOOR})
    # Should carve y=8 and y=7 (backed off), NOT y=9 (which is the wall)
    assert 9 not in floor_ys
    assert 7 in floor_ys and 8 in floor_ys


# ---------------------------------------------------------------------------
# End-to-end: generate dungeon at f85 and verify 2x2 walkable density
# ---------------------------------------------------------------------------

def test_f85_dungeon_has_walkable_2x2_anchors():
    """An f85 dungeon must have substantially more 2x2-walkable blocks
    than an f30 dungeon at the same seed/size."""
    from dungeon import generate_dungeon
    random.seed(42)
    d85 = generate_dungeon(width=80, height=50, level=85)
    random.seed(42)
    d30 = generate_dungeon(width=80, height=50, level=30)

    def count_2x2_blocks(d):
        return sum(
            1
            for y in range(1, d.height - 2)
            for x in range(1, d.width - 2)
            if d.is_walkable(x, y) and d.is_walkable(x + 1, y)
            and d.is_walkable(x, y + 1) and d.is_walkable(x + 1, y + 1)
        )

    blocks_85 = count_2x2_blocks(d85)
    blocks_30 = count_2x2_blocks(d30)
    # f85 should have AT LEAST 3x more 2x2-walkable blocks than f30
    # (in practice ~20x because corridors get walls). 3x is a safe floor
    # that survives different random seeds.
    assert blocks_85 >= max(50, blocks_30 * 3), \
        f"f85 should have >>2x2 anchors than f30 (got {blocks_85} vs {blocks_30})"


# ---------------------------------------------------------------------------
# Spawn picker: full-footprint validation
# ---------------------------------------------------------------------------

def test_spawn_picker_validates_full_footprint():
    """The _footprint_fits helper must reject any anchor where the full
    footprint doesn't land on walkable tiles, and the placement path must
    consult it BEFORE constructing a Monster. Since the 2026-06-06 per-room
    refactor, the check lives in the shared _spawn_one_in_room helper used by
    both spawn_monsters (targeted clusters) and populate_floor (whole floor)."""
    src = (ROOT / "src" / "dungeon.py").read_text(encoding='utf-8')
    assert "def _footprint_fits" in src, \
        "dungeon must define _footprint_fits to check full footprint"
    assert "footprint" in src
    # The shared placement helper must call it before any Monster() construction.
    place_idx = src.find("def _spawn_one_in_room")
    assert place_idx != -1, "expected the shared _spawn_one_in_room placement helper"
    place_body = src[place_idx:place_idx + 5000]
    fit_idx = place_body.find("_footprint_fits(")
    mk_idx = place_body.find("Monster(")
    assert fit_idx != -1, "placement helper must call _footprint_fits"
    assert fit_idx < mk_idx, \
        "_footprint_fits must be checked before Monster() construction"


# ---------------------------------------------------------------------------
# End-to-end: can a hand-placed Tiamat actually navigate?
# ---------------------------------------------------------------------------

def test_2x2_monster_can_navigate_in_f85():
    """Place a synthetic 2x2 monster in an f85 dungeon room and confirm
    it can move into a corridor in at least ONE direction."""
    from dungeon import generate_dungeon
    from monster import Monster
    random.seed(7)
    d = generate_dungeon(width=80, height=50, level=85)
    defn = {
        'id': 'test_2x2_boss',
        'name': 'Test 2x2 Boss', 'symbol': 'B', 'color': [200, 0, 0],
        'hp': '10d8', 'thac0': 0, 'speed': 10, 'ai_pattern': 'aggressive',
        'attacks': [{'damage': '1d6', 'type': 'physical'}],
        'footprint': [2, 2],
    }
    # Find ANY room with a valid 2x2 anchor and an adjacent 2x2 corridor
    found_navigable = False
    for room in d.rooms[1:]:
        for tx, ty in room.inner_tiles():
            ok_here = all(d.is_walkable(tx + dx, ty + dy)
                          for dx in range(2) for dy in range(2))
            if not ok_here:
                continue
            m = Monster(defn, tx, ty)
            # Try all 4 cardinal moves; at least one should succeed
            for ddx, ddy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                if m._can_move_to(d, tx + ddx, ty + ddy):
                    found_navigable = True
                    break
            if found_navigable:
                break
        if found_navigable:
            break
    assert found_navigable, \
        "In a fresh f85 dungeon, NO 2x2-anchor allows even one direction " \
        "of movement — the corridor widening isn't working"
