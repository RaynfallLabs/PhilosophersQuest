"""Bug bash 3.6.1, monster AI (2026-11-22): each test fails on the code
before its fix and passes after.

B10 (handed over from the abilities bug bash): a sleep laid by a spell (Mass
Sleep, Deep Slumber, the Bough of Somnus, a wand, a scroll, a flask, a gas)
woke to noise like a creature's own rest: the cast's own noise, a fight
beside it, a friend's shout. Deep Slumber and the Bough of Somnus say "A
blow wakes the one it lands on". In a staged game every goblin of three put
to sleep by Mass Sleep was awake within the cast's turn (one woke to the
spell's noise and shouted, and the shout woke the rest).
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import alarm  # noqa: E402
import senses  # noqa: E402
import sleepers  # noqa: E402
from dungeon import Dungeon, Room, WALL, FLOOR  # noqa: E402
from monster import Monster  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), '..')
_MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))


class Hero:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.hp = self.max_hp = 50
        self.status_effects = {}
        self.equipped_accessories = []
        self.boons_taken = {}
        self.STR = self.CON = self.INT = self.WIS = self.PER = self.DEX = 10

    def has_effect(self, name):
        return self.status_effects.get(name, 0) > 0

    def is_burdened(self):
        return False


def room():
    w, h = 12, 12
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, 11):
        for x in range(1, 11):
            tiles[y][x] = FLOOR
    return Dungeon(tiles, [Room(0, 0, 12, 12)], w, h, 5)


def make(kind='goblin', x=5, y=5):
    return Monster({**_MONS[kind], 'id': kind}, x, y)


class Zero:
    """An rng whose every roll wakes a sleeper that can be woken."""
    def random(self):
        return 0.0


def _fight_beside(dun, hero):
    senses.emit(dun, hero.x, hero.y, 'melee')
    senses.emit(dun, hero.x, hero.y, 'spell')


# ---------------------------------------------------------------------------
# B10: a spell's sleep ends on a blow, not on a noise
# ---------------------------------------------------------------------------

def test_a_spell_sleep_sleeps_through_the_fight_beside_it():
    dun, hero = room(), Hero(5, 5)
    gob = make('goblin', 6, 6)
    assert gob.add_effect('sleeping', 10) == 10
    assert sleepers.laid(gob)
    assert senses._wake_p(gob, 'melee', 1, 5, hero) == 0.0
    for _ in range(5):
        _fight_beside(dun, hero)
        assert senses.resolve_noises(dun, [gob], hero, rng=Zero()) == []
        gob.tick_effects()
    assert gob.has_effect('sleeping')


def test_its_own_rest_still_wakes_to_the_fight():
    dun, hero = room(), Hero(5, 5)
    gob = make('goblin', 6, 6)
    gob.status_effects['sleeping'] = 400          # a sleeping job (senses.assign_jobs)
    assert not sleepers.laid(gob)
    _fight_beside(dun, hero)
    assert senses.resolve_noises(dun, [gob], hero, rng=Zero()) == [gob]
    assert not gob.has_effect('sleeping')


def test_a_blow_wakes_a_spell_sleeper():
    gob = make('goblin', 6, 6)
    gob.max_hp = gob.hp = 100
    gob.add_effect('sleeping', 10)
    gob.take_damage(3)
    assert not gob.has_effect('sleeping')
    assert not sleepers.laid(gob)


def test_hold_lays_a_spell_sleep_too():
    gob = make('goblin', 6, 6)
    gob.hold('sleeping', 15)                      # the Seal of Solomon's pacifying
    assert sleepers.laid(gob)


def test_a_friends_shout_does_not_wake_a_spell_sleeper():
    dun, hero = room(), Hero(2, 2)
    gob = make('goblin', 6, 6)
    gob.add_effect('sleeping', 10)
    senses.rouse(gob, hero.x, hero.y)             # a band's or a pack's alarm
    assert gob.has_effect('sleeping')
    assert gob.__dict__.get('_goal') == (hero.x, hero.y)   # it goes there when it wakes
    nap = make('goblin', 7, 7)
    nap.status_effects['sleeping'] = 400
    senses.rouse(nap, hero.x, hero.y)
    assert not nap.has_effect('sleeping')


def test_a_lookouts_alarm_does_not_wake_a_spell_sleeper():
    dun, hero = room(), Hero(2, 2)
    gob = make('goblin', 6, 6)
    gob.add_effect('sleeping', 10)
    look = make('goblin', 7, 6)
    if alarm.spec(look) is None:
        look.__dict__['alarm'] = {'radius': 8, 'line': '{The} yells!'}
    alarm.shout(look, [look, gob], hero, dun, rng=Zero())
    assert gob.has_effect('sleeping')


def test_footsteps_and_gold_do_not_stir_a_spell_slept_zoo():
    hero = Hero(5, 5)
    beast = make('goblin', 5, 6)
    beast.status_effects['sleeping'] = sleepers.DEEP + 50   # a zoo's deep sleep
    beast.add_effect('sleeping', 10)                         # and a spell's on top
    hero.status_effects['aggravated'] = 5
    assert sleepers.stirred(hero, 'take', 5, 5, [beast], 'zoo', rng=Zero()) == []
    hero.status_effects.clear()
    assert sleepers.stirred(hero, 'take', 5, 5, [beast], 'zoo', rng=Zero()) == []


def test_the_spell_runs_out_and_its_own_rest_wakes_to_noise_again():
    dun, hero = room(), Hero(5, 5)
    gob = make('goblin', 6, 6)
    gob.status_effects['sleeping'] = 400          # asleep already
    gob.add_effect('sleeping', 3)                 # and a spell on top: 3 turns proof
    for _ in range(3):
        _fight_beside(dun, hero)
        assert senses.resolve_noises(dun, [gob], hero, rng=Zero()) == []
        gob.tick_effects()
    assert gob.has_effect('sleeping') and not sleepers.laid(gob)
    _fight_beside(dun, hero)
    assert senses.resolve_noises(dun, [gob], hero, rng=Zero()) == [gob]
