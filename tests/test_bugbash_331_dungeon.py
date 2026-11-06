"""Bug bash 3.3.1, dungeon generation: what lies where.

C10a: on floors 1 and 2 no named unique is old enough to be found (each
carries its own min_level, from its lore), so the loot pool's fallback
handed the floor-unique roll every unique there is: Stormbringer
(min_level 88) could lie on floor 1. The gate is the item's own data, never
a multiplier on the floor (LORE, NOT FLOOR).
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pytest  # noqa: E402

import dungeon  # noqa: E402
import items  # noqa: E402


def _uniques():
    out = []
    for c in ('weapon', 'armor', 'shield'):
        out += [i for i in items.load_items(c) if getattr(i, 'is_unique', False)]
    return out


@pytest.mark.parametrize('level', [1, 2, 3, 10, 40, 99])
def test_the_floor_unique_pool_holds_nothing_too_deep_for_the_floor(level):
    items.bind_unique_registry(set())
    pool = dungeon._item_eligible_weighted(_uniques(), level, random.Random(level))
    assert all(int(i.min_level) <= level for i in pool), \
        sorted({(i.min_level, i.id) for i in pool if i.min_level > level})[:5]


@pytest.mark.parametrize('cls', ['accessory', 'wand', 'scroll', 'spellbook', 'potion', 'ammo'])
def test_no_loot_pool_falls_back_to_deeper_things(cls):
    items.bind_unique_registry(set())
    base = items.load_items(cls)
    for level in (1, 2, 5):
        pool = dungeon._item_eligible_weighted(base, level, random.Random(level))
        assert all(int(getattr(i, 'min_level', 1) or 1) <= level for i in pool), (cls, level)


def test_early_floors_never_lay_a_late_unique():
    items.bind_unique_registry(set())
    from level_manager import LevelManager
    late = []
    random.seed(331)
    for n in range(60):
        lv = 1 + n % 2
        lm = LevelManager()
        _d, _m, ground = lm.generate(lv)
        late += [(lv, g.id) for g in ground
                 if getattr(g, 'is_unique', False) and int(getattr(g, 'min_level', 1) or 1) > lv]
    assert late == []
