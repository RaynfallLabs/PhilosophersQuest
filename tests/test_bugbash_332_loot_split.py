"""Armour 6/7 (bug bash 3.3.2): common gear is found 45 / 45 / 10.

Brandon's ruling (plan revision 2, point 6): armour has seven more slots
than a weapon, so a find of common gear is a weapon, an armour piece or a
shield 45 / 45 / 10 (it was 60 / 20 / 15 in floor rooms, 30 / 10 / 10 in
drops, a third each in chests), and an armour piece is any of the eight
slots evenly (the shirt was never found on a floor). The armour model
(tools/balance/armor_model.py) proved the design on this split.
"""
import collections
import inspect
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import pygame  # noqa: E402

pygame.init()

import gear  # noqa: E402
import items  # noqa: E402


def test_the_game_finds_gear_on_the_split_the_model_proved():
    import armor_model
    model = armor_model.PROPOSAL['split']
    game = gear.loot_split()
    assert game == {'weapon': model['weapon'], 'armor': model['armour'], 'shield': model['shield']}
    assert game == {'weapon': 0.45, 'armor': 0.45, 'shield': 0.10}


def test_a_find_is_a_weapon_an_armour_piece_or_a_shield_by_the_split():
    rng = random.Random(3)
    n = 4000
    got = collections.Counter(type(items.pick_random_gear_for_floor(rng.randint(1, 100), rng)).__name__
                              for _ in range(n))
    assert abs(got['Weapon'] / n - 0.45) < 0.03
    assert abs(got['Armor'] / n - 0.45) < 0.03
    assert abs(got['Shield'] / n - 0.10) < 0.02


def test_an_armour_find_is_any_of_the_eight_slots_evenly():
    rng = random.Random(5)
    n = 4000
    slots = collections.Counter(items.pick_random_armor_for_floor(rng.randint(1, 100), rng).slot
                                for _ in range(n))
    assert set(slots) == set(items.ARMOR_SLOTS) and 'shirt' in slots
    for s, c in slots.items():
        assert abs(c / n - 1 / len(items.ARMOR_SLOTS)) < 0.03, (s, c)


def test_a_chests_gear_follows_the_split():
    import container_system
    rng = random.Random(9)
    n = 3000
    got = collections.Counter(
        type(container_system._pull_common_from_category('gear', [], 40, rng)).__name__
        for _ in range(n))
    assert abs(got['Armor'] / n - 0.45) < 0.03 and abs(got['Shield'] / n - 0.10) < 0.02


def test_floor_rooms_and_monster_drops_roll_the_split():
    import dungeon
    import game_combat
    assert 'pick_random_gear_for_floor(level, rng)' in inspect.getsource(dungeon.spawn_items)
    assert 'pick_random_gear_for_floor(effective_floor, _rng)' in inspect.getsource(game_combat)
    assert '_ARMOR_SLOTS_FOR_DROP' not in inspect.getsource(dungeon)
