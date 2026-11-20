"""Monster behaviour, third wave (AI-3): the defects the independent audit
found (_mm_2026_11_19/AI3/AUDIT.md, D1-D10 and the lead's ruling on
omniscience), each pinned by a seeded test that failed before its fix.

  D1  a swallowed hero is out of every reach but his holder's: no curse,
      dispel, darkness, aura, thrown pot or burst from outside, and a
      binding never shuts his blow on the holder from inside;
  D2  the leprechaun's bargain is asked after the world's turn, void if he
      died or got loose meanwhile, and paid once;
  D3  a chant is lost to sleep, paralysis, a stun, fear or charm;
  D4  heat and cold need open air, a stench a way for the smell, and a
      creature the hero cannot see is never named;
  D5  the bandit thug's crude pot stays inside the rubric's one-turn cap;
  D6  a territorial creature struck while it walks home turns and fights;
  D7  a broken coward does not dart in;
  D8  a surprise is the lurker's first blow only, and no lurker's surprise
      breaks the rubric's one-turn cap;
  D9  a kit carrier killed before its first turn makes no second loot roll;
  D10 the hints and docs say what the game does;
  and a caster counts only the resistances it can see or has seen.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))

import pygame  # noqa: E402

pygame.init()

import ai_lines  # noqa: E402
import auras  # noqa: E402
import caster_ai  # noqa: E402
import holds  # noqa: E402
import home_ground  # noqa: E402
import monster_kit  # noqa: E402
import skittish  # noqa: E402
from dungeon import WALL, FLOOR  # noqa: E402
from test_monster_behaviour_ai3 import (Hero, open_room, make, hurt, fail_saves,  # noqa: E402
                                        setup_function as _setup)

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))


def setup_function(f):
    _setup(f)


def _swallow(hero, cube, monkeypatch):
    fail_saves(monkeypatch)
    atk = next(a for a in cube.attacks if holds.spec_of(a))
    holds.after_blow(cube, hero, atk, 3, '')
    monkeypatch.undo()
    assert holds.swallowed(hero)


# ===========================================================================
# D1: inside the holder, nothing else reaches him
# ===========================================================================

def test_d1_no_curse_dispel_or_darkness_reaches_a_swallowed_hero(monkeypatch):
    d = open_room()
    hero = Hero(6, 5)
    cube = make('gelatinous_cube', 5, 5)
    cube._aware = True
    _swallow(hero, cube, monkeypatch)
    priest = make('cult_priest', 9, 5)
    priest._tracking = True
    assert caster_ai.choose(priest, caster_ai.Context(hero, d, [cube, priest])) is None
    hero.status_effects.update({'hasted': 9, 'light': 20})
    lich = make('lich', 9, 6)
    lich._tracking = True
    kob = make('kobold_sorcerer', 9, 4)
    kob._tracking = True
    for c in (lich, kob):
        ch = caster_ai.choose(c, caster_ai.Context(hero, d, [cube, c]))
        assert ch is None or ch['kind'] in ('ward', 'heal', 'escape'), ch
    # A chant drawn up before he was swallowed is let go, not laid on him.
    priest._casting = 'binding_litany'
    fail_saves(monkeypatch)
    caster_ai.turn(priest, hero, d, [cube, priest], set())
    assert 'immobilized' not in hero.status_effects


def test_d1_no_aura_reaches_a_swallowed_hero(monkeypatch):
    hero = Hero(6, 5, hp=300)
    cube = make('gelatinous_cube', 5, 5)
    cube._aware = True
    _swallow(hero, cube, monkeypatch)
    fire = make('fire_elemental', 7, 5)
    hp0 = hero.hp
    assert auras.pulse([cube, fire], hero, None, dungeon=open_room()) == []
    assert hero.hp == hp0


def test_d1_no_fire_pot_is_thrown_at_a_swallowed_hero(monkeypatch):
    hero = Hero(6, 5)
    cube = make('gelatinous_cube', 5, 5)
    cube._aware = True
    _swallow(hero, cube, monkeypatch)
    orc = make('orc_marauder', 9, 5)
    orc._tracking = True
    orc._kit = ('flask_of_fire_oil',)
    assert monster_kit.turn(orc, hero, open_room(), [cube, orc], set()) is None
    assert monster_kit.kit(orc) == ('flask_of_fire_oil',)       # not wasted either


# ===========================================================================
# D3: a chant lost to sleep, paralysis, a stun, fear or charm
# ===========================================================================

def test_d3_a_chant_is_lost_when_the_caster_is_put_to_sleep():
    for cond in ('sleeping', 'paralyzed', 'stunned', 'feared', 'charmed'):
        # (the dead take no charm: a living priest for that one)
        kind, sid = ('cult_priest', 'binding_litany') if cond == 'charmed' else ('lich', 'lich_hold')
        c = make(kind, 5, 5)
        c._tracking = True
        c._casting = sid
        c.status_effects[cond] = 6
        c.tick_effects()
        assert not c.__dict__.get('_casting'), cond
        assert any('chant' in t for t, _u, _c in ai_lines.take(c)), cond
    # Pinned (immobilized), it can still speak its spell.
    lich = make('lich', 5, 5)
    lich._casting = 'lich_hold'
    lich.status_effects['immobilized'] = 3
    lich.tick_effects()
    assert lich._casting == 'lich_hold'


# ===========================================================================
# D4: auras by their lore's reach, and no name for the unseen
# ===========================================================================

def _walled(w=12, h=9, wall_x=6):
    d = open_room(w, h)
    for y in range(h):
        d.tiles[y][wall_x] = WALL
    return d


def test_d4_heat_never_reaches_through_a_wall():
    d = _walled()
    hero = Hero(5, 4, hp=500)
    king = make('fire_giant_king', 7, 4)                       # radius 2, a wall between
    king.status_effects['sleeping'] = 50
    assert auras.pulse([king], hero, lambda _m: False, dungeon=d) == []
    assert hero.hp == 500
    d.tiles[4][6] = FLOOR                                      # open air: a sleeper burns too
    out = auras.pulse([king], hero, lambda _m: False, dungeon=d)
    assert hero.hp < 500 and out
    assert 'Fire Giant King' not in out[0][0] and 'somewhere close' in out[0][0]


def test_d4_a_stench_carries_round_a_corner_but_not_through_rock(monkeypatch):
    fail_saves(monkeypatch)
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    d = _walled()
    hero = Hero(5, 4)
    tree = make('upas_tree', 7, 4)                             # radius 2
    assert auras.pulse([tree], hero, None, dungeon=d) == []
    assert 'poisoned' not in hero.status_effects
    d.tiles[3][6] = FLOOR                                      # a gap a step aside
    out = auras.pulse([tree], hero, lambda _m: False, dungeon=d)
    assert hero.status_effects.get('poisoned', 0) > 0
    assert out and 'Upas' not in out[0][0]


def test_d4_a_seen_creature_is_named():
    hero = Hero(6, 5, hp=500)
    fire = make('fire_elemental', 5, 5)
    out = auras.pulse([fire], hero, lambda _m: True, dungeon=open_room())
    assert 'Fire Elemental' in out[0][0]


# ===========================================================================
# D5, D8: the rubric's one-turn cap
# ===========================================================================

def test_d5_the_thugs_crude_pot_is_inside_the_one_turn_cap():
    import monster_bands as mb
    for k, v in MONS.items():
        if not isinstance(v, dict):
            continue
        for e in v.get('kit') or ():
            if not monster_kit.throw_spec(e['item']):
                continue
            m = make(k)
            atk = monster_kit._throw_attack(e['item'], e.get('throw'))
            _ac, hp = mb.hero_at(int(v.get('peak_floor') or 1))
            assert mb.dice_mean(atk['damage']) <= 0.25 * hp, (k, atk['damage'], hp)
            assert m is not None
    thug = make('bandit_thug')
    thug._kit = ('flask_of_fire_oil',)
    assert monster_kit.leftovers(thug) == []                   # a crude pot breaks as he falls


def test_d8_no_lurkers_surprise_breaks_the_one_turn_cap():
    import monster_bands as mb
    for k, v in MONS.items():
        if not isinstance(v, dict) or v.get('ai_pattern') not in ('ambush', 'mimic'):
            continue
        if v.get('is_boss') or v.get('is_mini_boss') or v.get('is_seal_demon'):
            continue
        _ac, hp = mb.hero_at(int(v.get('peak_floor') or 1))
        best = max(mb.dice_mean(a['damage']) for a in v['attacks'])
        assert 1.75 * best <= 0.25 * hp, (k, best, hp)


def test_d8_the_surprise_is_spent_by_a_first_blow_that_misses(monkeypatch):
    hero = Hero(6, 5, hp=10000)
    m = make('piercer', 5, 5)
    m._aware = True
    m._mimic_surprise = True
    monkeypatch.setattr(random, 'randint', lambda a, b: a)    # a natural 1: a miss
    dmg, _msg = m.attack(hero)
    assert dmg == 0
    monkeypatch.setattr(random, 'randint', lambda a, b: b)
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    dmg, msg = m.attack(hero)
    assert 'from hiding' not in msg and dmg == 12             # 2d6 at its height, no surprise


# ===========================================================================
# D6: no free hits on a creature walking home
# ===========================================================================

def test_d6_a_struck_draugr_turns_and_fights():
    d = open_room(40, 12)
    m = make('draugr', 10, 5)
    m._home = (5, 5)
    m._aware = True
    hero = Hero(5 + 8 + 3, 5)
    assert home_ground.leash(m, hero, d, [m], set(), True) is False   # it lets him go
    m.take_damage(5)                                                  # an arrow from afar
    x0 = m.x
    assert home_ground.leash(m, hero, d, [m], set(), True) is True    # it turns on him
    assert m.x == x0
    for _ in range(4):                                                # and keeps on him a while
        assert home_ground.leash(m, hero, d, [m], set(), True) is True
    assert home_ground.leash(m, hero, d, [m], set(), True) is False   # then home again


# ===========================================================================
# D7: morale first
# ===========================================================================

def test_d7_a_broken_leprechaun_takes_no_darts():
    d = open_room()
    hero = Hero(10, 10)
    hero._facing_dx, hero._facing_dy = 1, 0                   # back turned
    m = make('leprechaun', 7, 10)
    m._aware = True
    m._flee_timer = 8
    hurt(m, 0.2)
    for _ in range(4):
        assert m.take_turn(hero, d, [m]) is False
    assert max(abs(m.x - hero.x), abs(m.y - hero.y)) >= 3


# ===========================================================================
# D9 and the ruling: no double loot; never omniscient
# ===========================================================================

def test_d9_a_kit_carrier_killed_in_its_sleep_makes_no_second_roll():
    random.seed(4)
    had = 0
    for _ in range(40):
        m = make('bandit_kingpin', 5, 5)
        m.treasure = dict(m.treasure, item_chance=0.55)
        monster_kit.kit_is_its_loot(m)                         # killed before its first turn
        if m.__dict__.get('_kit_had'):
            had += 1
            assert m.treasure['item_chance'] == 0.0
        else:
            assert m.treasure['item_chance'] == 0.55
    assert had > 0


def test_ruling_a_caster_learns_a_hidden_resistance_only_by_seeing_it(monkeypatch):
    """The hero drank fire resistance out of the mage's sight: its first fire
    bolt goes out, it sees the fizzle, and its next is frost."""
    hero = Hero(9, 5, hp=500)
    hero.status_effects = {'fire_resist': 30}
    m = make('battle_mage', 5, 5)
    cands = m._distance_attacks()
    first = caster_ai.pick_attack(m, hero, cands)
    assert first['name'] == 'Fire Bolt'
    monkeypatch.setattr(random, 'randint', lambda a, b: b)    # it lands
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    m._resolve_blow(first, hero)
    assert caster_ai.pick_attack(m, hero, cands)['name'] == 'Frost Bolt'


def test_ruling_its_band_learns_with_it(monkeypatch):
    hero = Hero(9, 5, hp=500)
    hero.status_effects = {'fire_resist': 30}
    a, b = make('battle_mage', 5, 5), make('battle_mage', 5, 6)
    a._band = b._band = 'band1'
    a._cached_all_monsters = [a, b]
    monkeypatch.setattr(random, 'randint', lambda x, y: y)
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    a._resolve_blow(next(x for x in a.attacks if x['name'] == 'Fire Bolt'), hero)
    assert caster_ai.pick_attack(b, hero, b._distance_attacks())['name'] == 'Frost Bolt'
    loner = make('battle_mage', 6, 6)
    assert caster_ai.pick_attack(loner, hero, loner._distance_attacks())['name'] == 'Fire Bolt'


def test_d10_darkness_is_not_cast_at_a_light_it_cannot_put_out():
    from types import SimpleNamespace
    import lights
    hero = Hero(8, 5)
    lamp = SimpleNamespace(id='heros_lamp', lit=True)
    real_held, real_lit = lights.held, lights.is_lit
    lights.held = lambda p: lamp
    lights.is_lit = lambda lt: True
    real_ever = lights.everlasting
    lights.everlasting = lambda lt: True
    try:
        m = make('kobold_sorcerer', 5, 5)
        m._tracking = True
        assert caster_ai.choose(m, caster_ai.Context(hero, open_room(), [m])) is None
    finally:
        lights.held, lights.is_lit, lights.everlasting = real_held, real_lit, real_ever


def test_d10_the_hints_and_docs_say_what_the_game_does():
    hints = json.load(open(os.path.join(ROOT, 'data', 'hints.json'), encoding='utf-8'))
    text = ' '.join(h for lst in hints.values() for h in lst)
    assert "The salamander's heat and the frost giant's cold" not in text
    assert 'A brigand carries' not in text
    assert not MONS['brigand'].get('kit') and MONS['bandit_captain'].get('kit')
    doc = open(os.path.join(ROOT, 'docs', 'systems', 'monsters.md'), encoding='utf-8').read()
    assert 'springs within 5 tiles' not in doc
    claude = open(os.path.join(ROOT, 'CLAUDE.md'), encoding='utf-8').read()
    assert 'unstrung (no missile, breath, gaze)' not in claude


# ===========================================================================
# The Game's side: D1 (the blow from inside, the burst), D2 (the bargain)
# ===========================================================================

def _scene(*placed):
    import test_monster_behaviour_ai3_game as G
    return G._scene(*placed)


def test_d1_a_bound_swallowed_hero_still_strikes_his_holder(monkeypatch):
    from game_states import STATE_QUIZ
    g = _scene(('gelatinous_cube', 1, 0))
    cube = g.monsters[0]
    _swallow(g.player, cube, monkeypatch)
    g.player.status_effects['immobilized'] = 2
    g._do_move(-1, 0)                                          # away from it: still its gut
    assert g.state == STATE_QUIZ and g.combat_target is cube


def test_d1_no_burst_outside_reaches_a_swallowed_hero(monkeypatch):
    g = _scene(('gelatinous_cube', 1, 0), ('fire_beetle', -1, 0))
    cube, beetle = g.monsters
    _swallow(g.player, cube, monkeypatch)
    hp0 = g.player.hp
    beetle.hp = 0
    beetle.alive = False
    g._on_monster_killed(beetle)
    assert g.player.hp == hp0


def test_d2_the_bargain_waits_for_the_world_and_is_void_if_he_died(monkeypatch):
    from game_states import STATE_PLAYER, STATE_ASK
    from items import GoldPile
    g = _scene(('leprechaun', 1, 0))
    m = g.monsters[0]
    m.treasure = {'gold': [40, 40], 'item_chance': 0.0, 'item_tier': 1}
    m._wants_bargain = True
    g._ways_turn_after(m)
    assert g.state == STATE_PLAYER                             # nothing is asked mid-turn
    g._ways_after_world()
    assert g.state == STATE_ASK
    yes = g._ask_data['options'][0][3]
    # He dies while the question is open (a trap, a burst).
    m.hp = 0
    m.alive = False
    g._on_monster_killed(m)
    piles = [it for it in g.ground_items if isinstance(it, GoldPile)]
    before = sum(it.amount for it in piles)
    yes()
    after = sum(it.amount for it in g.ground_items if isinstance(it, GoldPile))
    assert after == before                                     # no purse from a dead man
    assert any('chance is gone' in str(e[0]) for e in g.msg_log.entries[-4:])


def test_d2_the_purse_is_paid_once():
    from items import GoldPile
    g = _scene(('leprechaun', 1, 0))
    m = g.monsters[0]
    m.treasure = {'gold': [40, 40], 'item_chance': 0.0, 'item_tier': 1}
    m._wants_bargain = True
    g._ways_turn_after(m)
    g._ways_after_world()
    yes = g._ask_data['options'][0][3]

    def gold():
        return sum(it.amount for it in g.ground_items if isinstance(it, GoldPile))
    g0 = gold()
    yes()
    yes()
    assert gold() - g0 == 60


def test_d2_a_leprechaun_who_got_loose_offers_nothing():
    g = _scene(('leprechaun', 1, 0))
    m = g.monsters[0]
    m._wants_bargain = True
    g._ways_turn_after(m)
    m.x += 4                                                   # he slipped away
    g._ways_after_world()
    assert not m.__dict__.get('_wants_bargain') and g.state == 'player'
    assert skittish.bargain(m)
