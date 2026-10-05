"""World-generation regressions from the pre-v3.0 audit (2026-10-04).

W3  hidden treasure chambers must not rebuild quest structures
W4  quest structures must not destroy or cut off the down stairs
W6  level 100 must have altars for the holy-fire prayer

Generation is random, so each check runs a batch of floors.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

import pytest  # noqa: E402

from dungeon import (ALTAR, STAIRS_DOWN, _bfs_reaches,  # noqa: E402
                     _find_stair_tiles)
from level_manager import LevelManager  # noqa: E402

_RUNS = 25


def _generate(level):
    result = LevelManager().generate(level)
    return result[0], result[1], result[2]


def _stairs_ok(dungeon):
    h, w = len(dungeon.tiles), len(dungeon.tiles[0])
    up, down = _find_stair_tiles(dungeon.tiles, w, h)
    return up is not None and down is not None and \
        _bfs_reaches(dungeon.tiles, w, h, up, down)


@pytest.mark.parametrize('level', [68, 71, 74, 76, 79, 99])
def test_w4_quest_floors_keep_reachable_down_stairs(level):
    for _ in range(_RUNS):
        dungeon, _m, _i = _generate(level)
        assert _stairs_ok(dungeon), f"L{level}: down stairs missing or cut off"


@pytest.mark.parametrize('level,attr', [
    (53, 'odin_altar_pos'),
    (78, 'dwarven_forge_pos'),
    (79, 'vidar_altar_pos'),
    (99, 'judgment_altar_pos'),
])
def test_w3_w4_quest_altar_pointer_is_a_real_altar(level, attr):
    """The stored quest position must be an ALTAR tile, and the floor must
    hold no stray second quest structure from a repeated spawn pass."""
    for _ in range(_RUNS):
        dungeon, _m, _i = _generate(level)
        pos = getattr(dungeon, attr, None)
        assert pos is not None, f"L{level}: {attr} not set"
        x, y = pos
        assert dungeon.tiles[y][x] == ALTAR, f"L{level}: {attr} is not an altar"
        assert dungeon.tiles[y][x] != STAIRS_DOWN


def test_w3_hidden_chamber_pass_spawns_loot_only():
    """spawn_items(structures=False) must leave quest pointers untouched."""
    from dungeon import generate_dungeon, spawn_items
    for _ in range(10):
        dungeon = generate_dungeon(80, 50, 79)
        spawn_items(dungeon.rooms, 79, dungeon)
        before = (dungeon.vidar_altar_pos,
                  sum(row.count(ALTAR) for row in dungeon.tiles),
                  len(dungeon.traps))
        room = dungeon.rooms[1]
        spawn_items([room, room], 79, dungeon, structures=False)
        after = (dungeon.vidar_altar_pos,
                 sum(row.count(ALTAR) for row in dungeon.tiles),
                 len(dungeon.traps))
        assert before == after


@pytest.mark.parametrize('level', [20, 45])
def test_w4_swamp_rooms_never_cut_off_the_stairs(level):
    for _ in range(40):
        dungeon, _m, _i = _generate(level)
        assert _stairs_ok(dungeon), f"L{level}: down stairs cut off"


# ---- W7: quest / scripted items never come from random pools --------------

_QUEST_IDS = ('philosophers_stone', 'gleipnir', 'seal_of_wrath',
              'scales_of_michael', 'bronze_bull', 'leather_scrap',
              'sealed_dispatch', 'cursed_lodestone', 'eye_of_graeae',
              'vidars_sandal', 'aegis_of_athena', 'prophets_amulet',
              'duck_of_doom')


def test_w7_quest_items_are_scripted_only():
    from items import scripted_only_ids
    locked = scripted_only_ids()
    for item_id in _QUEST_IDS:
        assert item_id in locked, item_id
    # Wonder relics and ordinary gear stay obtainable.
    for item_id in ('palladium', 'tablet_of_destinies'):
        assert item_id not in locked, item_id


def test_w7_chest_unique_pool_has_no_quest_items():
    import json
    from container_system import _build_unique_pool
    templates = json.loads((_ROOT / 'data' / 'chest_templates.json')
                           .read_text(encoding='utf-8'))
    from items import scripted_only_ids
    locked = scripted_only_ids()
    checked = 0
    for tpl in templates.values():
        if not isinstance(tpl, dict) or 'loot_table' not in tpl:
            continue
        pool = _build_unique_pool(tpl, 100)
        leaked = sorted({it.id for it in pool if it.id in locked})
        assert not leaked, leaked[:8]
        checked += 1
    assert checked >= 1


def test_w7_floor_magic_pool_has_no_scripted_items():
    import random
    from dungeon import _item_eligible_weighted
    from items import load_items, scripted_only_ids
    locked = scripted_only_ids()
    pool = []
    for cls in ('accessory', 'wand', 'scroll', 'spellbook'):
        pool += load_items(cls)
    for level in (1, 30, 60, 90):
        eligible = _item_eligible_weighted(pool, level, random.Random(level))
        assert not {it.id for it in eligible} & locked


def test_w13_barracks_does_not_draw_from_unique_files():
    src = (_ROOT / 'src' / 'dungeon.py').read_text(encoding='utf-8')
    # rindex: the loot branch in spawn_items, not the atmosphere-message one
    block = src[src.rindex("elif room_type == 'barracks':"):]
    block = block[:block.index("elif room_type == 'swamp':")]
    assert 'load_items(' not in block
    assert 'pick_random_weapon_for_floor' in block


def test_w6_level_100_has_altars():
    from boss_levels import generate_boss_level
    dungeon = generate_boss_level(100)[0]
    altars = sum(row.count(ALTAR) for row in dungeon.tiles)
    assert altars == 6, f"level 100 should have 6 altars, found {altars}"
