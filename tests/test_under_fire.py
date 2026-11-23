# ruff: noqa: F811  (make_game is a pytest fixture, imported)
"""Monsters that fight back (2026-11-22; DIFFICULTY_DIAGNOSIS_2026_11_22.md,
Brandon's "Yes, all three"):

1. a creature that cannot shoot back answers being shot (src/under_fire.py:
   a charger rushes; the Tactical Mind's Into Cover; a band's goblins sling;
   a captain under fire stops hanging back);
2. the leader's fall is a morale test for each follower, the biggest guard
   may take up the lead, a broken one turns at bay when caught (war_bands
   leader_falls, morale.run, morale.frightened_turn); a great blow is great;
3. morale by each kind's lore (monsters.json morale, morale_style,
   break_share).

Pure tests where the rule lives in a pure module, data tests for the kinds'
fields, and a staged Game for the band. Tests do not prove feel: that is
Brandon's play-test.
"""
import json
import os
import random
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kind_data  # noqa: E402
import morale  # noqa: E402
import packs  # noqa: E402
import tactics  # noqa: E402
import under_fire  # noqa: E402
import war_bands  # noqa: E402
from monster import Monster  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))


def _m(kind, x=5, y=5):
    return Monster({**MONS[kind], 'id': kind}, x, y)


class _Hero:
    def __init__(self, x=5, y=10):
        self.x, self.y = x, y
        self.hp = self.max_hp = 40
        self.status_effects = {}

    def has_effect(self, n):
        return False


class _Dice:
    """A stand-in for the random module: randint gives these numbers in turn."""

    def __init__(self, *rolls):
        self.rolls = list(rolls)

    def randint(self, a, b):
        return self.rolls.pop(0) if self.rolls else a

    def random(self):
        return 0.0


# ------------------------------------------------------------- under fire

def test_hurt_from_afar_is_being_shot_and_is_remembered():
    m, hero = _m('orc_warrior', 5, 5), _Hero(5, 10)
    assert not under_fire.note(m, hero)              # its first turn: nothing to compare
    m.hp -= 5
    assert under_fire.note(m, hero) and under_fire.shot_now(m) and under_fire.under_fire(m)
    mem = int(under_fire.rules()['memory'])
    for _ in range(mem - 1):
        assert not under_fire.note(m, hero)
        assert under_fire.under_fire(m) and not under_fire.shot_now(m)
    under_fire.note(m, hero)
    assert not under_fire.under_fire(m)


def test_a_blow_beside_him_or_a_pets_bite_is_not_being_shot():
    m, hero = _m('orc_warrior', 5, 5), _Hero(5, 6)
    under_fire.note(m, hero)
    m.hp -= 5
    assert not under_fire.note(m, hero)              # he is beside it: a sword
    far = _Hero(5, 12)
    m2 = _m('orc_warrior', 5, 5)
    under_fire.note(m2, far)
    m2.hp -= 5

    class Pet:
        alive, x, y = True, 6, 5
    assert not under_fire.note(m2, far, pets=[Pet()])  # a pet at it


def test_a_charger_shot_from_afar_rushes_two_strides_then_catches_its_breath():
    m, hero = _m('orc_warrior', 5, 5), _Hero(5, 12)
    assert under_fire.rusher(m) and 'rush' in under_fire.tell_keys(m)
    assert under_fire.steps(m) == 1 and not under_fire.start_rush(m, hero)   # not shot yet
    under_fire.note(m, hero)
    m.hp -= 5
    under_fire.note(m, hero)
    assert under_fire.start_rush(m, hero)
    turns = int(under_fire.rules()['rush_turns'])
    for _ in range(turns):
        assert under_fire.rushing(m) and under_fire.steps(m) == 2
        under_fire.spend_rush(m, hero)
    assert not under_fire.rushing(m) and under_fire.steps(m) == 1
    assert int(m._rush_rest) == int(under_fire.rules()['rush_rest'])
    m.hp -= 5
    under_fire.note(m, hero)
    assert not under_fire.start_rush(m, hero)        # still catching its breath
    said = [s for s, _u, _c in m.__dict__.get('_ai_lines') or ()]
    assert said == [kind_data.rules('under_fire')['rush_line'].replace('{The}', 'The Orc Warrior')]


def test_a_rush_ends_beside_the_hero_and_no_one_else_rushes():
    m, hero = _m('bugbear', 5, 5), _Hero(5, 12)
    under_fire.note(m, hero)
    m.hp -= 5
    under_fire.note(m, hero)
    assert under_fire.start_rush(m, hero)
    m.y = 11                                          # it has arrived
    under_fire.spend_rush(m, hero)
    assert not under_fire.rushing(m)
    rat = _m('giant_rat', 5, 5)                       # vermin: no charger
    under_fire.note(rat, hero)
    rat.hp -= 1
    under_fire.note(rat, hero)
    assert not under_fire.rusher(rat) and not under_fire.start_rush(rat, hero)
    boss = _m('orc_warrior', 5, 5)
    boss.is_mini_boss = True
    under_fire.note(boss, hero)
    boss.hp -= 5
    under_fire.note(boss, hero)
    assert not under_fire.start_rush(boss, hero)      # a named foe keeps its tuned fight


def test_the_chargers_are_real_kinds_and_rushers_by_lore():
    rushers = [k for k, v in MONS.items() if isinstance(v, dict) and v.get('rush')]
    for k in ('orc_warrior', 'bugbear', 'ogre', 'troll', 'cave_bear', 'minotaur_warrior'):
        assert k in rushers, k
    for k in ('goblin', 'giant_rat', 'jackal', 'bandit_archer', 'goblin_shaman'):
        assert k not in rushers, k
    for k in rushers:
        assert MONS[k]['ai_pattern'] == 'aggressive', k     # a hand-to-hand charger


# ------------------------------------------------------------- Into Cover (pure)

def _sp(mind):
    return tactics.spec(mind)


def test_shot_with_no_shot_of_its_own_a_thinking_kind_ducks_out_of_sight():
    v = tactics.View(mind='cunning', dist=5, under_fire=True, cover_tile=True, in_his_sight=True)
    opt, sc = tactics.decide(v, _sp('cunning'))
    assert opt == 'take_cover' and sc['take_cover'] > sc['attack']
    # With a lane it shoots back; with no cover it comes on; not shot, nothing.
    assert tactics.decide(tactics.View(mind='cunning', dist=5, under_fire=True, cover_tile=True,
                                       has_lane=True), _sp('cunning'))[0] != 'take_cover'
    assert tactics.decide(tactics.View(mind='cunning', dist=5, under_fire=True),
                          _sp('cunning'))[0] == 'attack'
    assert tactics.decide(tactics.View(mind='cunning', dist=5, cover_tile=True),
                          _sp('cunning'))[0] == 'attack'
    cap = int(tactics.data()['under_fire']['cover_moves'])
    assert tactics.decide(tactics.View(mind='cunning', dist=5, under_fire=True, cover_tile=True,
                                       covered=cap), _sp('cunning'))[0] == 'attack'


def test_round_the_corner_it_waits_then_strikes_first_as_he_comes():
    lurk = tactics.View(mind='soldier', dist=5, in_cover=True, in_his_sight=False)
    assert tactics.decide(lurk, _sp('soldier'))[0] == 'take_cover'
    close = tactics.View(mind='soldier', dist=2, in_cover=True, in_his_sight=True)
    opt, sc = tactics.decide(close, _sp('soldier'))
    assert opt == 'take_cover' and sc['take_cover'] > 1.5
    done = tactics.View(mind='soldier', dist=2, in_cover=True, cover_struck=True)
    assert tactics.decide(done, _sp('soldier'))[0] == 'attack'
    patient = int(tactics.data()['patience'])
    assert tactics.decide(tactics.View(mind='soldier', dist=5, in_cover=True, waited=patient),
                          _sp('soldier'))[0] == 'attack'


def test_a_captain_under_fire_stops_hanging_back():
    v = dict(mind='soldier', dist=4, role='leader', order='screen', screen_tile=True)
    assert tactics.decide(tactics.View(**v), _sp('soldier'))[0] == 'screen'
    assert tactics.decide(tactics.View(**v, under_fire=True), _sp('soldier'))[0] != 'screen'


def test_every_mind_has_a_cover_weight_and_the_lines_say_no_they():
    uf = tactics.data()['under_fire']
    for mind in tactics.MINDS:
        assert tactics.cover_weight(mind) > 0, mind
    for t in list(uf['lines'].values()) + [uf['bestiary']]:
        low = f' {t.lower()} '
        assert ' they ' not in low and ' them ' not in low and len(t) <= 70, t


# ------------------------------------------------------------- a band's slingers

class _Dun:
    def __init__(self, w=20, h=20):
        from dungeon import FLOOR, WALL, Dungeon, Room
        tiles = [[WALL] * w for _ in range(h)]
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                tiles[y][x] = FLOOR
        self.d = Dungeon(tiles, [Room(0, 0, w, h)], w, h, 3)


def test_a_bands_goblin_slings_stones_then_comes_on():
    d = _Dun().d
    hero = _Hero(5, 10)
    gob = _m('goblin', 5, 6)
    gob._band, gob._band_id, gob._band_role = 'b@1', 'goblin_scouts', 'guard'
    d.band = {'uid': 'b@1', 'order': 'screen'}
    assert packs.band_slinger(gob) and not packs.in_pack(gob)
    cap = int(packs.data()['band_sling']['stones'])
    for i in range(cap):
        assert packs.hunt_turn(gob, hero, d, [gob]) == 'attack', i
        assert gob.__dict__.get('_pack_blow', {}).get('ranged')
        gob.__dict__.pop('_pack_blow', None)
    assert packs.hunt_turn(gob, hero, d, [gob]) is None          # its stones thrown: it comes on
    gob2 = _m('goblin', 5, 6)
    gob2._band, gob2._band_id, gob2._band_role = 'b@1', 'goblin_scouts', 'guard'
    d.band['order'] = 'charge'
    assert packs.hunt_turn(gob2, hero, d, [gob2]) is None         # the charge is called
    d.band['order'] = 'screen'
    gob2.x, gob2.y = 5, 9
    assert packs.hunt_turn(gob2, hero, d, [gob2]) is None         # beside him: its knife


# ------------------------------------------------------------- morale by each kind's lore

def test_each_kinds_nerve_is_its_lore():
    nat = {k: morale.nature(_m(k)) for k in ('orc_warrior', 'bugbear', 'giant_rat', 'jackal',
                                             'goblin', 'hobgoblin', 'wolf', 'orc_berserker')}
    assert nat['orc_warrior'][1] >= 14 and nat['bugbear'][1] >= 15      # they hold
    assert nat['giant_rat'][1] <= 6 and nat['jackal'][1] <= 6             # they break
    assert nat['hobgoblin'][1] > nat['goblin'][1]                          # drilled
    assert nat['orc_berserker'][0] == 'never'
    assert nat['wolf'][0] == 'bolt' and nat['giant_rat'][0] == 'bolt'
    assert morale.break_share(_m('jackal')) == 0.5
    assert morale.break_share(_m('goblin')) == float(morale.rules()['break_share'])
    for k, v in MONS.items():
        if isinstance(v, dict) and 'morale' in v:
            assert 0 <= int(v['morale']) <= 20, k


def test_the_bestiary_says_each_kinds_nerve_in_one_line():
    assert morale.bestiary_line('bugbear').startswith('Steady')
    assert morale.bestiary_line('giant_rat').startswith('Shaky')
    assert 'friends' in morale.bestiary_line('goblin')
    assert morale.bestiary_line('skeleton') == ''                          # never breaks
    assert 'regroups' in morale.tell_keys(_m('goblin'))


def test_a_jackal_breaks_at_half_its_health():
    j, hero = _m('jackal'), _Hero(5, 9)
    j.hp = int(j.max_hp * 0.45)
    morale.turn(j, hero, [j], rng=_Dice(10, 10))       # 20 > 6: it breaks
    assert int(j._flee_timer) > 0
    o = _m('orc_warrior')
    o.hp = int(o.max_hp * 0.45)
    morale.turn(o, hero, [o], rng=_Dice(10, 10))
    assert int(o._flee_timer) == 0                       # an orc tests at a quarter


# ------------------------------------------------------------- at bay

def test_caught_and_struck_as_it_runs_it_turns_at_bay():
    d = _Dun().d
    hero = _Hero(5, 6)
    g = _m('goblin', 5, 5)
    g._flee_timer = 6
    g._mo_hp = g.hp
    g.hp -= 3                                            # his blow as it ran
    assert morale.run(g, hero, d, [g], set()) is True
    assert int(g._at_bay) > 0 and int(g._flee_timer) == 0


def test_a_frightened_creature_cornered_beside_him_strikes():
    from dungeon import FLOOR, WALL, Dungeon, Room
    tiles = [[WALL] * 5 for _ in range(5)]
    tiles[2][2] = tiles[2][3] = FLOOR                    # a dead end: it, then him
    d = Dungeon(tiles, [Room(0, 0, 5, 5)], 5, 5, 3)
    hero = _Hero(3, 2)
    g = _m('goblin', 2, 2)
    g.status_effects['feared'] = 5
    assert morale.frightened_turn(g, hero, d, [g], set()) is True
    assert int(g._at_bay) > 0
    tiles[2][1] = FLOOR                                  # a way out: it runs
    g2 = _m('goblin', 2, 2)
    g2.status_effects['feared'] = 5
    assert morale.frightened_turn(g2, hero, d, [g2], set()) is False
    assert (g2.x, g2.y) == (1, 2)


# ------------------------------------------------------------- the leader falls

def _scouts(n=3, kind='goblin'):
    lead = _m('hobgoblin', 5, 5)
    lead._band, lead._band_id, lead._band_role = 'u', 'goblin_scouts', 'leader'
    fol = []
    for i in range(n):
        f = _m(kind, 6 + i, 5)
        f._band, f._band_id, f._band_role, f._band_leader = 'u', 'goblin_scouts', 'guard', lead
        fol.append(f)
    return lead, fol


def test_the_leaders_fall_is_a_test_for_each_not_fear_for_all():
    lead, fol = _scouts()
    fol[0].max_hp = fol[0].hp = 30                       # the biggest guard
    hero = _Hero(5, 12)
    lead.alive = False
    # The big one fails his own test (no one takes the lead); then rolls of
    # 2+2 (hold), 10+10 (break), 2+2 (hold) for the rest at the penalty.
    out = war_bands.on_death([lead] + fol, lead, hero, rng=_Dice(10, 10, 2, 2, 10, 10, 2, 2))
    assert out['successor'] is None
    assert not any(f.has_effect('feared') for f in fol)
    broke = [f for f in fol if int(f._flee_timer or 0) > 0]
    held = [f for f in fol if int(f._flee_timer or 0) == 0]
    assert len(broke) == 1 and len(held) == 2, (broke, held)
    assert out['line'] == war_bands.leader_falls_spec('goblin_scouts')['lines']['hold'].replace(
        '{the}', 'the Hobgoblin')
    assert lead._band_role != 'leader'


def test_the_biggest_guard_may_take_up_the_lead():
    lead, fol = _scouts()
    big = fol[1]
    big.max_hp = big.hp = 40
    hero = _Hero(5, 12)
    lead.alive = False
    out = war_bands.on_death([lead] + fol, lead, hero, rng=_Dice(2, 2, 2, 2, 2, 2))
    assert out['successor'] is big and big._band_role == 'leader'
    assert war_bands.leader_of([lead] + fol, 'u') is big
    rest = [f for f in fol if f is not big]
    assert all(war_bands.holds_nerve(f) for f in rest)   # his band now
    assert 'rally' in war_bands.leader_falls_spec('goblin_scouts')['lines']


def test_when_every_one_breaks_the_band_routs():
    lead, fol = _scouts(2)
    hero = _Hero(5, 12)
    lead.alive = False
    out = war_bands.on_death([lead] + fol, lead, hero, rng=_Dice(*([10] * 12)))
    assert out['successor'] is None
    assert all(int(f._flee_timer or 0) > 0 for f in fol)
    assert out['line'] == war_bands.data()['bands']['goblin_scouts']['rout_line']


def test_each_bands_numbers_are_its_own():
    lf = war_bands.data()['leader_falls']
    for bid in lf['bands']:
        assert bid in war_bands.data()['bands'], bid
        assert war_bands.data()['bands'][bid]['morale'] == 'rout', bid
    assert war_bands.leader_falls_spec('footpads')['successor'] is False
    assert war_bands.leader_falls_spec('cult_circle')['penalty'] < war_bands.leader_falls_spec(
        'goblin_scouts')['penalty']
    for spec in [lf] + list(lf['bands'].values()):
        for t in (spec.get('lines') or {}).values():
            low = f' {t.lower()} '
            assert ' they ' not in low and ' them ' not in low and len(t) <= 70, t


def test_half_the_band_down_tests_their_nerve_only_with_no_leader():
    lead, fol = _scouts(3)
    # The leader lives: when half are down they hold for him.
    fol[0].alive = False
    fol[1].alive = False
    war_bands.on_death([lead] + fol, fol[1])
    assert not fol[2].__dict__.get('_morale_check') and not fol[2].has_effect('feared')
    # No leader leads them: each of the rest tests on his next turn.
    lead2, fol2 = _scouts(3)
    lead2.alive = False
    for f in fol2:
        f._band_leader = None
    lead2._band_role = 'fallen'
    fol2[0].alive = False
    fol2[1].alive = False
    war_bands.on_death([lead2] + fol2, fol2[1])
    assert fol2[2]._morale_check == 'half' and not fol2[2].has_effect('feared')
    assert int(fol2[2]._morale_penalty) == int(war_bands.data()['leader_falls']['half_down_penalty'])


def test_a_great_blow_must_be_great():
    lead, fol = _scouts(4)
    g = war_bands.data()['great_blow']
    assert not war_bands.is_great_blow(lead, int(g['chain']) - 1, lead.max_hp)
    assert not war_bands.is_great_blow(lead, int(g['chain']), 1)
    assert war_bands.is_great_blow(lead, int(g['chain']), int(lead.max_hp * float(g['share'])) + 1)


# ------------------------------------------------------------- a staged Game

import pygame  # noqa: E402

from test_bugbash_wb_e import blow, make_game, open_floor, place_monster  # noqa: E402,F401


def test_a_band_whose_leader_falls_does_not_all_simply_flee(make_game, monkeypatch):
    """A hobgoblin and three goblins beside the hero; the hobgoblin cut down.
    The goblins test their nerve: whatever the dice, none is simply
    frightened, and on the next turns those who held strike."""
    g, h = make_game()
    p = g.player
    p.hp = p.max_hp = 500
    open_floor(g, p.x, p.y, 4)
    lead = place_monster(g, 'hobgoblin', 1)
    gobs = [place_monster(g, 'goblin', -1), place_monster(g, 'goblin', 0, 1),
            place_monster(g, 'goblin', 0, -1)]
    uid = 'goblin_scouts@test'
    for m, role in [(lead, 'leader')] + [(o, 'guard') for o in gobs]:
        m._band, m._band_id, m._band_role = uid, 'goblin_scouts', role
        m.status_effects.pop('sleeping', None)
    for o in gobs:
        o._band_leader = lead
        o.hp = o.max_hp = 200                            # they live through the scene
    lead.hp = 1
    # One of the three breaks; the others hold (the dice are fixed: the
    # rest of the game's randomness is its own).
    calls = {'n': 0}

    def _breaks(m, penalty=0, rng=random):
        calls['n'] += 1
        return calls['n'] == 2
    monkeypatch.setattr(morale, 'breaks', _breaks)
    g._refresh_fov()
    h.said()
    blow(h, lead, 3)
    assert not lead.alive
    assert not any(o.has_effect('feared') for o in gobs)
    struck = 0
    for _ in range(4):
        hp0 = p.hp
        h.key(pygame.K_PERIOD, '.')                      # he waits a turn
        struck += p.hp < hp0
    assert struck >= 1
    standing = [o for o in gobs if int(o._flee_timer or 0) == 0 and o.alive]
    assert len(standing) >= 2
