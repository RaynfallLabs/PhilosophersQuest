"""Deep sleepers stir (src/sleepers.py, Brandon 2026-10-26).

A zoo's, a graveyard's and a barracks' sleepers used to sleep until struck,
whatever the hero did beside them. Now a step or a gold pile taken in the
room may wake them, by odds that light feet, A Cat's Footfall, the Hand of
Glory, a Burdened pack and Aggravated change; finding the room warns that
its creatures sleep; and a zoo emptied with every keeper asleep is the
Seeker's Burglar.
"""
import json
import os
import random
import types
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import sleepers  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _hero(dex=10, boons=None, worn=(), burdened=False, aggravated=False):
    h = types.SimpleNamespace(DEX=dex, boons_taken=boons or {}, equipped_accessories=list(worn))
    h.is_burdened = lambda: burdened
    h.has_effect = lambda e: aggravated and e == 'aggravated'
    return h


def _sleeper(x, y):
    return types.SimpleNamespace(x=x, y=y, alive=True, status_effects={'sleeping': 10 ** 6})


class _AlwaysLow:
    def random(self):
        return 0.0


class _AlwaysHigh:
    def random(self):
        return 0.999


def test_reach_and_kind():
    s = [_sleeper(1, 0), _sleeper(3, 0), _sleeper(5, 0)]
    h = _hero()
    assert sleepers.stirred(h, 'step', 0, 0, s, 'zoo', _AlwaysLow()) == s[:1]   # step reach 2
    assert sleepers.stirred(h, 'take', 0, 0, s, 'zoo', _AlwaysLow()) == s[:2]   # take reach 3
    assert sleepers.stirred(h, 'take', 0, 0, s, 'zoo', _AlwaysHigh()) == []


def test_what_changes_the_odds():
    assert sleepers.factor(_hero(), 'step') == 1.0
    assert sleepers.factor(_hero(dex=20), 'take') == pytest.approx(0.7)
    assert sleepers.factor(_hero(dex=40), 'take') == sleepers.DEX_FLOOR
    assert sleepers.factor(_hero(burdened=True), 'take') == 2.0
    cat = _hero(boons={'fenrir_wolf': 'cats_footfall'})
    assert sleepers.factor(cat, 'step') == 0.0 and sleepers.factor(cat, 'take') == 1.0
    ring = _hero(worn=[types.SimpleNamespace(id='ring_of_the_assassin', passive_silent_walk=True)])
    assert sleepers.factor(ring, 'step') == 0.0 and sleepers.factor(ring, 'take') == 1.0
    hand = _hero(worn=[types.SimpleNamespace(id='hand_of_glory', passive_silent_walk=True)])
    assert sleepers.factor(hand, 'step') == 0.0 and sleepers.factor(hand, 'take') == 0.0


def test_aggravated_wakes_the_whole_room():
    s = [_sleeper(1, 0), _sleeper(9, 4)]
    assert sleepers.stirred(_hero(aggravated=True), 'step', 0, 0, s, 'barracks',
                            _AlwaysHigh()) == s


def test_only_deep_sleepers_and_only_these_rooms():
    light = types.SimpleNamespace(x=0, y=0, alive=True, status_effects={'sleeping': 20})
    assert not sleepers.is_deep_sleeper(light)
    assert sleepers.stirred(_hero(), 'take', 0, 0, [_sleeper(0, 0)], 'library', _AlwaysLow()) == []
    assert set(sleepers.RULES) == {'zoo', 'graveyard', 'barracks'}


def test_the_odds_match_the_simulation():
    """At DEX 10 one pile taken next to two keepers leaves both asleep about
    88% of the time (1 - 0.06)^2; the numbers Brandon was shown."""
    rng = random.Random(7)
    s = [_sleeper(1, 0), _sleeper(0, 1)]
    calm = sum(not sleepers.stirred(_hero(), 'take', 0, 0, s, 'zoo', rng) for _ in range(20000))
    assert 0.86 < calm / 20000 < 0.90


def test_finding_the_room_warns_that_its_creatures_sleep():
    src = (ROOT / 'src' / 'main.py').read_text(encoding='utf-8')
    block = src.split('_SPECIAL_ROOM_MSGS = {', 1)[1].split('}', 1)[0]
    for rtype in ('zoo', 'graveyard', 'barracks'):
        line = block.split(f"'{rtype}':", 1)[1].split("'danger')", 1)[0]
        assert 'asleep' in line or 'sleeping' in line or 'slept' in line, rtype
        assert 'wake' in line, rtype


# ---------------------------------------------------------------- in the game

@pytest.fixture
def game(tmp_path):
    import seeker_codes
    import seeker_profile
    saved = seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE
    seeker_codes._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}}
    seeker_profile._DIR_OVERRIDE = str(tmp_path / 'seekers')
    seeker_profile.set_active('Robyn')
    from main import Game
    import items
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name='Sleeper Test')
    yield g
    seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE = saved


def _zoo(g, keepers=2, piles=2):
    """Make the hero's room a zoo: keepers asleep, gold on the floor."""
    from main import DEEP_SLEEP
    from monster import Monster
    from items import GoldPile
    room = g.dungeon.rooms[0]
    centre = tuple(room.center)
    g.dungeon.special_rooms[centre] = 'zoo'
    defs = json.loads((ROOT / 'data' / 'monsters.json').read_text(encoding='utf-8'))
    tiles = [t for t in room.inner_tiles() if t != (g.player.x, g.player.y)]
    g.monsters = []
    for i in range(keepers):
        m = Monster(dict(defs['giant_rat'], id='giant_rat'), *tiles[i])
        m.status_effects['sleeping'] = DEEP_SLEEP
        m._keeper_of = centre
        g.monsters.append(m)
    g.dungeon._keepers_laid = {centre: keepers}
    g.ground_items = [i for i in g.ground_items if not isinstance(i, GoldPile)]
    piles_at = tiles[keepers:keepers + piles]
    for x, y in piles_at:
        g.ground_items.append(GoldPile(10, x, y))
    return room, piles_at


def test_gold_taken_can_wake_a_keeper(game, monkeypatch):
    room, piles = _zoo(game)
    monkeypatch.setattr(sleepers.random, 'random', lambda: 0.0)
    game.player.x, game.player.y = game.monsters[0].x, game.monsters[0].y + 0
    game._sleepers_stir('take')
    assert any(not sleepers.is_deep_sleeper(m) for m in game.monsters)
    assert tuple(room.center) in game.dungeon._disturbed_rooms


def test_emptying_a_zoo_unseen_is_the_burglar(game):
    room, piles = _zoo(game)
    game.player.amulet_slot = types.SimpleNamespace(id='hand_of_glory', passive_silent_walk=True)
    from items import GoldPile
    for x, y in piles:
        game.player.x, game.player.y = x, y
        pile = next(i for i in game.ground_items if isinstance(i, GoldPile) and (i.x, i.y) == (x, y))
        assert game._pickup_gold(pile)
    assert all(sleepers.is_deep_sleeper(m) for m in game.monsters)
    assert game._seeker.profile.is_unlocked('burglar')


def test_no_burglar_once_a_keeper_has_woken(game):
    room, piles = _zoo(game)
    game.monsters[0].status_effects.pop('sleeping')
    game.player.amulet_slot = types.SimpleNamespace(id='hand_of_glory', passive_silent_walk=True)
    from items import GoldPile
    for x, y in piles:
        game.player.x, game.player.y = x, y
        pile = next(i for i in game.ground_items if isinstance(i, GoldPile) and (i.x, i.y) == (x, y))
        game._pickup_gold(pile)
    assert not game._seeker.profile.is_unlocked('burglar')
