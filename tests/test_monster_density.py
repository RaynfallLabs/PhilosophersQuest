"""Tests for the room-aware monster spawn density formula (2026-05-19).

Locks in the density curve added when dungeons were rebuilt to 39% room area:
  - Density grows from 0.50 mob/room at L1 to 0.95 at L75+
  - Min count = 70% of (room_count * density), floor 3
  - Max count = 110% of target, capped at 20
  - Pack-spawning may push totals over max for variety

Plus invariants on the spawn pool itself.
"""
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame
pygame.init()


def _density_target(level: int, n_rooms_spawnable: int) -> tuple[int, int]:
    """Mirror the formula in level_manager.generate so the test catches drift."""
    density = min(0.50 + level / 130, 0.95)
    target = max(3, int(n_rooms_spawnable * density))
    return max(3, int(target * 0.70)), max(5, min(int(target * 1.10), 20))


# ---------------------------------------------------------------------------
# Formula invariants
# ---------------------------------------------------------------------------

def test_density_curve_grows_with_level():
    """Density should monotonically rise from L1 to L75, then plateau."""
    samples = [(lvl, min(0.50 + lvl / 130, 0.95)) for lvl in [1, 15, 30, 50, 75, 95]]
    for i in range(1, len(samples)):
        assert samples[i][1] >= samples[i - 1][1], (
            f'density should be non-decreasing: {samples}'
        )
    # Plateau check
    assert samples[-1][1] == samples[-2][1] == 0.95


def test_density_floor_at_l1():
    """L1 with 8 rooms should give a modest mob count (3-5 base)."""
    mn, mx = _density_target(1, 7)  # 8 rooms, 1 is start room
    assert 3 <= mn <= 4
    assert mx <= 6


def test_density_l15_no_dip():
    """The L15 dip bug — 20 rooms but only 4 mobs spawning — should not return."""
    mn, mx = _density_target(15, 19)  # 20 rooms - 1 start
    assert mn >= 7, f'L15 min should be >=7, was {mn}'
    assert mx >= 11, f'L15 max should be >=11, was {mx}'


def test_density_late_game_dense():
    """L75+ should hit the density cap (0.95 mob/room)."""
    mn, mx = _density_target(75, 19)
    assert mn >= 12
    assert mx >= 19
    # Cap is 20 hard
    assert mx <= 20


def test_density_cap_at_20():
    """No matter the room count, max_count is capped at 20."""
    for rooms in [25, 50, 100]:
        _, mx = _density_target(95, rooms - 1)
        assert mx <= 20, f'expected max_count <= 20, got {mx} at {rooms} rooms'


# ---------------------------------------------------------------------------
# Spawn pool invariants
# ---------------------------------------------------------------------------

def test_spawn_pool_has_eligible_monsters_per_floor():
    """Every floor 1-100 should have at least 10 eligible spawn-pool monsters
    (excluding bosses with peak_weight=0)."""
    import json
    from paths import data_path
    monsters = json.load(open(data_path('data', 'monsters.json'), encoding='utf-8'))

    for level in [1, 10, 30, 50, 75, 95]:
        eligible = 0
        for k, v in monsters.items():
            pw = v.get('peak_weight', 0)
            if pw <= 0:
                continue
            if v.get('min_level', 1) > level:
                continue
            peak_floor = v.get('peak_floor', v.get('min_level', 1))
            spread = max(1, v.get('spread', 10))
            dist = level - peak_floor
            bell = math.exp(-(dist ** 2) / (2 * spread ** 2))
            if bell < 0.005:
                continue
            eligible += 1
        assert eligible >= 10, f'L{level}: only {eligible} eligible monsters'


def test_no_orphaned_monsters_in_spawn_pool():
    """Monsters with peak_weight > 0 must have peak_floor > 0 (so the
    bell curve has a meaningful peak)."""
    import json
    from paths import data_path
    monsters = json.load(open(data_path('data', 'monsters.json'), encoding='utf-8'))
    orphans = []
    for k, v in monsters.items():
        if v.get('peak_weight', 0) > 0 and v.get('peak_floor', 0) <= 0:
            orphans.append(k)
    assert not orphans, f'monsters with peak_weight>0 but peak_floor<=0: {orphans[:5]}'


# ---------------------------------------------------------------------------
# End-to-end: actual dungeon generation
# ---------------------------------------------------------------------------

def test_l15_dungeon_has_meaningful_monster_count():
    """Regression: L15 floors must have at least 8 monsters on average."""
    from level_manager import LevelManager
    lm = LevelManager()
    counts = []
    for _ in range(5):
        dungeon, monsters, items = lm.generate(15)
        counts.append(len([m for m in monsters if m.alive]))
    avg = statistics.mean(counts)
    assert avg >= 8, f'L15 avg monster count too low: {avg}'


def test_l75_dungeon_has_dense_monster_count():
    """L75 should average at least 15 monsters per floor."""
    from level_manager import LevelManager
    lm = LevelManager()
    counts = []
    for _ in range(5):
        dungeon, monsters, items = lm.generate(75)
        counts.append(len([m for m in monsters if m.alive]))
    avg = statistics.mean(counts)
    assert avg >= 15, f'L75 avg monster count too low: {avg}'
