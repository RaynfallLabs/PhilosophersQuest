"""Tests for multi-tile monsters — Fafnir as the first real 2×2 boss.

The mechanic is built on a single new `Monster.footprint = (w, h)`
field and the `geom.py` helper module. Every existing monster keeps
`footprint == (1, 1)` and behaves identically; Fafnir is the only
2×2 monster in the data, occupying 4 NW-anchored tiles.

Test coverage:
- Default footprint (1, 1) is preserved for every existing monster.
- Fafnir's data has `footprint: [2, 2]`.
- `geom.occupied_tiles`, `is_at_tile`, `monster_at_tile`,
  `chebyshev_distance`, `is_adjacent`, `any_tile_in_set`,
  `all_occupied_tiles` behave correctly for both 1×1 and 2×2.
- `Monster._adjacent_to` uses the footprint helpers.
- `Monster._can_move_to` validates the WHOLE footprint, not just
  the anchor.
- The L60 boss room can fit Fafnir at the spawn anchor.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# Data-layer tests
# ---------------------------------------------------------------------------

def _load_monsters_json() -> dict:
    return json.loads((ROOT / "data" / "monsters.json").read_text(encoding="utf-8"))


def test_fafnir_has_2x2_footprint():
    """The whole feature hinges on Fafnir's data carrying footprint=[2,2]."""
    monsters = _load_monsters_json()
    assert monsters["fafnir_dragon"].get("footprint") == [2, 2], (
        "fafnir_dragon must declare footprint=[2,2] in monsters.json"
    )


def test_only_fafnir_has_multi_tile_footprint():
    """Phase 1 ships one 2×2 monster. Other 2×2 monsters are
    one-line data changes in a follow-up commit; if more appear in
    this commit something has drifted."""
    monsters = _load_monsters_json()
    multi = [name for name, m in monsters.items()
             if m.get("footprint") and tuple(m["footprint"]) != (1, 1)]
    assert multi == ["fafnir_dragon"], (
        f"expected only fafnir_dragon as multi-tile, got: {multi}"
    )


# ---------------------------------------------------------------------------
# Monster class — footprint field + helpers
# ---------------------------------------------------------------------------

def _make_monster(footprint=None, x=10, y=10):
    """Build a minimal Monster instance for tests."""
    from monster import Monster
    defn = {
        "id": "test_monster",
        "name": "test monster",
        "symbol": "T",
        "color": [100, 100, 100],
        "hp": 10,
        "thac0": 20,
        "speed": 10,
        "attacks": [],
        "ai_pattern": "aggressive",
    }
    if footprint is not None:
        defn["footprint"] = list(footprint)
    return Monster(defn, x, y)


def test_default_footprint_is_1x1():
    m = _make_monster()
    assert m.footprint == (1, 1)


def test_explicit_2x2_footprint_loads():
    m = _make_monster(footprint=[2, 2])
    assert m.footprint == (2, 2)


def test_fafnir_instance_has_2x2_footprint():
    """End-to-end: loading Fafnir from JSON and constructing a Monster
    surfaces the (2, 2) footprint at runtime."""
    monsters = _load_monsters_json()
    from monster import Monster
    fafnir_defn = {"id": "fafnir_dragon", **monsters["fafnir_dragon"]}
    f = Monster(fafnir_defn, x=42, y=43)
    assert f.footprint == (2, 2)


# ---------------------------------------------------------------------------
# geom helpers
# ---------------------------------------------------------------------------

def test_occupied_tiles_1x1():
    from geom import occupied_tiles
    m = _make_monster(x=5, y=7)
    assert list(occupied_tiles(m)) == [(5, 7)]


def test_occupied_tiles_2x2():
    from geom import occupied_tiles
    m = _make_monster(footprint=[2, 2], x=5, y=7)
    # NW-anchored: (5,7), (6,7), (5,8), (6,8)
    assert set(occupied_tiles(m)) == {(5, 7), (6, 7), (5, 8), (6, 8)}


def test_is_at_tile_2x2_covers_all_four():
    from geom import is_at_tile
    m = _make_monster(footprint=[2, 2], x=5, y=7)
    for (x, y) in [(5, 7), (6, 7), (5, 8), (6, 8)]:
        assert is_at_tile(m, x, y), f"({x},{y}) should be in 2×2 footprint at (5,7)"
    # Tiles outside the footprint
    for (x, y) in [(4, 7), (7, 7), (5, 6), (5, 9), (6, 9)]:
        assert not is_at_tile(m, x, y), f"({x},{y}) should NOT be in footprint"


def test_monster_at_tile_finds_fafnir_from_any_of_four_tiles():
    """The CORE bugfix: walking into ANY of Fafnir's 4 tiles must
    return Fafnir (so combat starts). The pre-fix `next(... if m.x ==
    nx and m.y == ny ...)` only matched the anchor."""
    from geom import monster_at_tile
    f = _make_monster(footprint=[2, 2], x=10, y=10)
    monsters = [f]
    for (x, y) in [(10, 10), (11, 10), (10, 11), (11, 11)]:
        assert monster_at_tile(monsters, x, y) is f, (
            f"monster_at_tile must return Fafnir for ({x},{y}); "
            f"otherwise the player can walk through 3 of his 4 tiles"
        )
    # Tiles immediately outside the footprint return None
    for (x, y) in [(9, 10), (12, 10), (10, 9), (11, 12)]:
        assert monster_at_tile(monsters, x, y) is None


def test_chebyshev_distance_2x2_returns_nearest_tile():
    """Distance is to the NEAREST footprint tile, not to the anchor."""
    from geom import chebyshev_distance
    f = _make_monster(footprint=[2, 2], x=10, y=10)
    # Player at (13, 10): anchor (10,10) is Chebyshev-3 away,
    # but the (11, 10) tile is Chebyshev-2 away → answer is 2.
    assert chebyshev_distance(13, 10, f) == 2
    # Standing on a footprint tile → 0
    assert chebyshev_distance(11, 11, f) == 0
    # Diagonal from corner: NE of (11, 10) is (12, 9), distance 1
    assert chebyshev_distance(12, 9, f) == 1


def test_is_adjacent_2x2_any_of_eight_neighbours_of_any_tile():
    """The player counts as adjacent if they're Chebyshev-1 from ANY
    of the 4 tiles — so the 'adjacency ring' around a 2×2 monster has
    12 tiles, not 8."""
    from geom import is_adjacent
    f = _make_monster(footprint=[2, 2], x=10, y=10)
    # Standing on a footprint tile is NOT adjacent
    assert not is_adjacent(10, 10, f)
    assert not is_adjacent(11, 11, f)
    # The 12 ring tiles around the 2×2 footprint
    ring = [
        (9, 9), (10, 9), (11, 9), (12, 9),
        (9, 10), (12, 10),
        (9, 11), (12, 11),
        (9, 12), (10, 12), (11, 12), (12, 12),
    ]
    for (x, y) in ring:
        assert is_adjacent(x, y, f), f"({x},{y}) should be adjacent to 2×2 footprint"
    # Two tiles further out — NOT adjacent
    for (x, y) in [(8, 10), (13, 10), (10, 8), (11, 13)]:
        assert not is_adjacent(x, y, f)


def test_any_tile_in_set_2x2_partial_overlap():
    """Fafnir is visible if ANY of his 4 tiles is in the FOV set
    (Cogmind's rule). One tile visible → render the whole dragon."""
    from geom import any_tile_in_set
    f = _make_monster(footprint=[2, 2], x=10, y=10)
    assert any_tile_in_set(f, {(11, 11)})  # NE-most footprint tile only
    assert any_tile_in_set(f, {(10, 10)})  # anchor only
    assert any_tile_in_set(f, {(11, 11), (50, 50)})  # one of many
    assert not any_tile_in_set(f, {(9, 9), (12, 12)})  # neither in footprint


def test_all_occupied_tiles_includes_every_footprint_tile():
    """Replaces the buggy `{(m.x, m.y) for m in monsters}` pattern
    that silently misses 3 of Fafnir's 4 tiles."""
    from geom import all_occupied_tiles
    f = _make_monster(footprint=[2, 2], x=10, y=10)
    g = _make_monster(x=20, y=20)  # plain 1×1 alongside
    out = all_occupied_tiles([f, g])
    assert out == {(10, 10), (11, 10), (10, 11), (11, 11), (20, 20)}


def test_all_occupied_tiles_exclude_self():
    """Used when a monster decides where to move — it ignores its own
    tiles so it's not blocked by itself."""
    from geom import all_occupied_tiles
    f = _make_monster(footprint=[2, 2], x=10, y=10)
    g = _make_monster(x=20, y=20)
    out = all_occupied_tiles([f, g], exclude=f)
    assert out == {(20, 20)}


def test_all_occupied_tiles_skips_dead():
    from geom import all_occupied_tiles
    f = _make_monster(footprint=[2, 2], x=10, y=10)
    f.alive = False
    g = _make_monster(x=20, y=20)
    out = all_occupied_tiles([f, g])
    assert out == {(20, 20)}


# ---------------------------------------------------------------------------
# Monster._adjacent_to uses the footprint
# ---------------------------------------------------------------------------

class _StubPlayer:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def test_monster_adjacent_to_2x2_from_extra_tiles():
    """Fafnir at (10, 10) sees the player at (12, 10) as adjacent
    because the (11, 10) tile is Chebyshev-1 away. Pre-fix this
    returned False."""
    f = _make_monster(footprint=[2, 2], x=10, y=10)
    assert f._adjacent_to(_StubPlayer(12, 10))
    assert f._adjacent_to(_StubPlayer(11, 12))
    assert f._adjacent_to(_StubPlayer(9, 9))  # NW corner diagonal


def test_monster_adjacent_to_1x1_unchanged():
    """Sanity: 1×1 monsters still work the way they always did."""
    g = _make_monster(x=10, y=10)
    assert g._adjacent_to(_StubPlayer(11, 10))
    assert not g._adjacent_to(_StubPlayer(12, 10))


# ---------------------------------------------------------------------------
# Monster._can_move_to validates whole footprint
# ---------------------------------------------------------------------------

class _StubDungeon:
    """Minimal dungeon with a simple wall-map. Used to test footprint
    validation in _can_move_to."""

    def __init__(self, w=20, h=20, walls=None):
        self._w = w
        self._h = h
        self._walls = set(walls or [])
        self.phasing_walls = set()
        self.tiles = [[0] * w for _ in range(h)]

    def in_bounds(self, x, y):
        return 0 <= x < self._w and 0 <= y < self._h

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and (x, y) not in self._walls


def test_can_move_to_2x2_rejects_if_any_destination_tile_is_wall():
    """A 2×2 dragon trying to step into a position where one of its
    new tiles is a wall must be blocked."""
    f = _make_monster(footprint=[2, 2], x=10, y=10)
    # Wall at (12, 10) — the NE tile of the new footprint
    d = _StubDungeon(walls={(12, 10)})
    assert not f._can_move_to(d, 11, 10), (
        "monster cannot step east — its (12, 10) tile would land on a wall"
    )


def test_can_move_to_2x2_accepts_all_four_clear():
    f = _make_monster(footprint=[2, 2], x=10, y=10)
    d = _StubDungeon()  # no walls
    assert f._can_move_to(d, 11, 11)


def test_can_move_to_2x2_rejects_if_out_of_bounds():
    f = _make_monster(footprint=[2, 2], x=10, y=10)
    d = _StubDungeon(w=12, h=12)  # tiles 0..11
    # Moving east to (11, 10) would put a tile at (12, 10) which is OOB
    assert not f._can_move_to(d, 11, 10)


def test_can_move_to_1x1_unchanged():
    """1×1 monsters still validate just their one destination tile."""
    g = _make_monster(x=10, y=10)
    d = _StubDungeon(walls={(11, 10)})
    assert not g._can_move_to(d, 11, 10)
    assert g._can_move_to(d, 10, 11)


# ---------------------------------------------------------------------------
# L60 boss room geometry — Fafnir's spawn anchor + footprint must fit
# ---------------------------------------------------------------------------

def test_l60_boss_room_fits_fafnir_2x2_footprint():
    """The L60 boss room is hand-carved in boss_levels.py at center
    (42, 43) with half-dims (12, 5). The _spawn_boss helper places
    Fafnir at the room center and then nudges NW if needed. Verify
    the 4 footprint tiles end up on walkable floor."""
    from boss_levels import _level_60_lair
    dungeon, monsters, _items = _level_60_lair()
    fafnir = next(m for m in monsters if m.kind == 'fafnir_dragon')
    # All 4 footprint tiles must be in-bounds AND walkable AND
    # not occupied by anything blocking.
    for dy in range(fafnir.footprint[1]):
        for dx in range(fafnir.footprint[0]):
            tx, ty = fafnir.x + dx, fafnir.y + dy
            assert dungeon.in_bounds(tx, ty), (
                f"Fafnir footprint tile ({tx},{ty}) is out of bounds"
            )
            assert dungeon.is_walkable(tx, ty), (
                f"Fafnir footprint tile ({tx},{ty}) is not walkable — "
                f"the boss room or spawn anchor needs adjustment"
            )


def test_l60_player_can_attack_any_of_fafnirs_tiles():
    """End-to-end sanity: in the live L60 level, every one of Fafnir's
    4 tiles routes through `monster_at_tile` correctly and returns
    Fafnir — i.e. walking into the SE tile of the dragon's body is
    the same as walking into his head."""
    from boss_levels import _level_60_lair
    from geom import monster_at_tile
    _dungeon, monsters, _items = _level_60_lair()
    fafnir = next(m for m in monsters if m.kind == 'fafnir_dragon')
    for dy in range(fafnir.footprint[1]):
        for dx in range(fafnir.footprint[0]):
            tx, ty = fafnir.x + dx, fafnir.y + dy
            assert monster_at_tile(monsters, tx, ty) is fafnir
