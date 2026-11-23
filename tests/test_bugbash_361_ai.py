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


# ---------------------------------------------------------------------------
# AI02: a great blow on a band's leader shakes only the followers who see it,
# and is said only when one did falter
# ---------------------------------------------------------------------------

def _band(leader, followers, bid='goblin_scouts'):
    uid = f'{bid}@test'
    for m, role in [(leader, 'leader')] + [(o, 'guard') for o in followers]:
        m._band, m._band_id, m._band_role = uid, bid, role
    for o in followers:
        o._band_leader = leader


def test_a_great_blow_shakes_only_the_followers_who_see_it(monkeypatch):
    import war_bands
    dun = room()
    for y in range(1, 11):
        dun.tiles[y][8] = WALL                    # a wall between the camp and the far side
    lead = make('hobgoblin', 3, 5)
    lead.max_hp = lead.hp = 100
    near, asleep, beyond = make('goblin', 4, 5), make('goblin', 3, 6), make('goblin', 9, 5)
    asleep.status_effects['sleeping'] = 300
    _band(lead, [near, asleep, beyond])
    monkeypatch.setattr(war_bands.random, 'random', lambda: 0.0)   # every one who sees it falters
    line = war_bands.on_great_blow([lead, near, asleep, beyond], lead, 9, 50, dun)
    assert line
    assert near.has_effect('feared')
    assert not asleep.has_effect('feared') and not beyond.has_effect('feared')


def test_a_great_blow_that_frightens_no_one_is_not_said(monkeypatch):
    import war_bands
    dun = room()
    lead = make('hobgoblin', 3, 5)
    lead.max_hp = lead.hp = 100
    skel = make('goblin', 4, 5)
    skel.status_immune = ['feared']                # a follower that knows no fear
    _band(lead, [skel], 'necro_procession')
    monkeypatch.setattr(war_bands.random, 'random', lambda: 0.0)
    assert war_bands.on_great_blow([lead, skel], lead, 9, 50, dun) == ''
    assert not skel.has_effect('feared')


# ---------------------------------------------------------------------------
# AI04: the Tactical Mind's "he saw it decide" is the hero's own field of view
# ---------------------------------------------------------------------------

def test_the_mind_asks_the_heros_real_sight_when_the_game_has_looked():
    import tactical_mind
    dun = room()
    hero = Hero(2, 2)
    hero.get_sight_radius = lambda: 5
    gob = make('goblin', 6, 6)                     # the corner of a 5-tile sight: a square's, not a round one's
    was = tactical_mind.TURN.n
    try:
        tactical_mind.TURN.n = 40
        assert tactical_mind.hero_sees(gob, hero, dun)          # the old guess: in sight
        gob._hero_saw = (40, False)                              # the Game: out of his field of view
        assert not tactical_mind.hero_sees(gob, hero, dun)
        gob._hero_saw = (39, False)                              # last turn's look is no answer
        assert tactical_mind.hero_sees(gob, hero, dun)
    finally:
        tactical_mind.TURN.n = was


# ---------------------------------------------------------------------------
# AI05: a wound bleeding is no blow: not "shot", not "caught as it runs"
# ---------------------------------------------------------------------------

def test_a_bleed_ticking_is_not_being_shot():
    import under_fire
    hero = Hero(5, 10)
    orc = make('orc_warrior', 5, 5)
    orc.max_hp = orc.hp = 100
    under_fire.note(orc, hero)
    orc.status_effects['bleeding'] = 5
    orc.tick_effects()                             # the bleed takes its share
    assert orc.hp < 100
    assert not under_fire.note(orc, hero) and not under_fire.start_rush(orc, hero)
    orc.take_damage(4)                             # an arrow
    assert under_fire.note(orc, hero)


def test_a_runner_beside_him_bleeding_is_not_caught_and_struck():
    import morale
    dun, hero = room(), Hero(5, 5)
    gob = make('goblin', 5, 6)
    gob.max_hp = gob.hp = 60
    morale.start_flight(gob, hero, [gob])
    gob.status_effects['bleeding'] = 5
    gob.tick_effects()
    morale.run(gob, hero, dun, [gob], set())
    assert not int(gob.__dict__.get('_at_bay', 0) or 0)


# ---------------------------------------------------------------------------
# AI06: a blow beside it tells an eyeless creature where the hero is
# ---------------------------------------------------------------------------

def test_an_ooze_struck_by_a_hero_standing_still_strikes_back():
    dun, hero = room(), Hero(5, 5)
    jelly = make('ochre_jelly', 5, 6)
    jelly.max_hp = jelly.hp = 200
    senses.begin_turn(moved=True, guilty=False, floor=10)
    assert senses.notice(jelly, hero, dun, [jelly], set())       # it felt his step
    senses.begin_turn(moved=False, guilty=False, floor=10)
    assert not senses.notice(jelly, hero, dun, [jelly], set())   # he stands still: its tremor fails
    jelly.take_damage(5)                                          # he strikes it
    assert senses.notice(jelly, hero, dun, [jelly], set())
    assert jelly._sensed_by == 'touch'
    far = make('ochre_jelly', 5, 9)
    far.take_damage(5)                                            # an arrow from afar: no touch
    assert not senses.notice(far, hero, dun, [far], set())


# ---------------------------------------------------------------------------
# On a staged Game
# ---------------------------------------------------------------------------

import pygame  # noqa: E402

from test_bugbash_wb_e import make_game, open_floor, place_monster  # noqa: E402,F401


def test_a_mending_done_out_of_sight_is_not_told_later(make_game):
    """AI03: a caster's book mends a friend out of the hero's sight; the
    mending was not cleared, and the next turn he saw the caster the game
    said "chants and heals" of a turn it mended no one."""
    g, h = make_game()
    p = g.player
    p.hp = p.max_hp = 500
    open_floor(g, p.x, p.y, 3)
    priest = place_monster(g, 'goblin', 2)
    friend = place_monster(g, 'goblin', 3)
    for m in (priest, friend):
        m.status_effects.pop('sleeping', None)
        m.stationary = True                       # they keep where they are
    g.visible = set()                             # he sees nothing this turn
    priest._heal_target, priest._heal_amount = friend, 5   # as faction.heal leaves it
    g._sees_monster = lambda m: False
    g._do_monster_turns()
    assert priest._heal_target is None
    del g._sees_monster
    g._refresh_fov()
    h.said()
    h.wait()
    assert not any('heals' in s for s in h.said())


def test_the_game_tells_the_mind_what_the_hero_saw(make_game):
    """AI04: before each creature's turn the Game notes whether the hero saw
    it (tactical_mind.hero_sees reads it: his real field of view)."""
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 3)
    gob = place_monster(g, 'goblin', 2)
    gob.status_effects.pop('sleeping', None)
    g._refresh_fov()
    turn = g.turn_count
    g._do_monster_turns()
    assert gob._hero_saw == (turn, True)
