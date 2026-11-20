"""Monster behaviour, first wave (AI-1): the defects the audit found
(_mm_2026_11_19/AI1/AUDIT.md), each pinned by a seeded test that failed
before its fix.

D1 a yielded foe struck while held; D2 a lone pack-dependent bandit could
not yield and his flight froze; D3 a chant broken by anything, always said
to be "your blow"; D4 a bleed or a burn ticking ended a hiding and sprang a
relurked lurker; D5 a captain who yields kept his band's nerve; D6 only the
melee kinds ever broke; D7 pets kept biting a foe who begged; D8 filling a
soaked lantern lit it; D9 the text claimed more than the code does; D10 the
simulator's ai_rot ablation was not clean. And slice M's kinds on the
engine: the mandrake's death cry, the ponaturi in the light, the bulls'
shove, the relentless myrmekes and taniwha.
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

import ai_lines  # noqa: E402
import gone_again  # noqa: E402
import morale  # noqa: E402
import relurk  # noqa: E402
import senses  # noqa: E402
import summoning  # noqa: E402
from dungeon import Dungeon, Room, WALL, FLOOR  # noqa: E402
from monster import Monster  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))


class Hero:
    def __init__(self, x=10, y=10, hp=200):
        self.x, self.y = x, y
        self.hp = self.max_hp = hp
        self.status_effects = {}
        self.equipped_accessories = []
        self.boons_taken = {}
        self.STR = self.CON = self.DEX = self.INT = self.WIS = self.PER = 10
        self.shield = None
        self.weapon = None
        self.armor_slots = []

    def has_effect(self, name):
        return self.status_effects.get(name, 0) > 0

    def is_burdened(self):
        return False

    def get_ac(self):
        return 10

    def get_sight_radius(self):
        return 8

    def take_damage(self, amount, damage_type='physical'):
        self.hp = max(0, self.hp - max(0, int(amount)))
        return max(0, int(amount))

    def save_bonus_for(self, _stat):
        return 0


class Dice:
    def __init__(self, face):
        self.face = face

    def randint(self, a, b):
        return max(a, min(b, self.face))

    def random(self):
        return 0.0


def open_room(w=24, h=24):
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            tiles[y][x] = FLOOR
    return Dungeon(tiles, [Room(0, 0, w, h)], w, h, 5)


def dead_end():
    tiles = [[WALL] * 8 for _ in range(5)]
    for x in range(1, 7):
        tiles[2][x] = FLOOR
    return Dungeon(tiles, [Room(0, 0, 8, 5)], 8, 5, 3)


def make(kind, x=5, y=5):
    return Monster({**MONS[kind], 'id': kind}, x, y)


def hurt(m, share):
    m.hp = max(1, int(m.max_hp * share))
    return m


def setup_function(_):
    random.seed(11)
    senses.begin_turn(moved=True, guilty=False, floor=5)
    summoning.CONTEXT = None


# ---------------------------------------------------------------- D1
def test_d1_a_yielded_foe_never_strikes_even_when_held():
    for held in ('stuck_in_pit', 'impaled', 'immobilized'):
        b = make('bandit_thug', 5, 5)
        morale.give_up(b)
        b.status_effects[held] = 5
        hero = Hero(6, 5)
        for _ in range(4):
            assert b.take_turn(hero, open_room(), [b]) is False, held
        assert (b.x, b.y) == (5, 5)                      # held: it stays put


# ---------------------------------------------------------------- D2
def test_d2_a_lone_bandit_breaks_runs_and_yields_when_caught():
    b = make('bandit_thug', 1, 2)
    hero = Hero(2, 2)
    dun = dead_end()
    b.take_turn(hero, dun, [b])                          # alone: he turns cowardly
    assert b.ai_pattern == 'cowardly' and morale.ruled(b)
    hurt(b, 0.2)
    morale.turn(b, hero, [b], rng=Dice(10))
    assert b._flee_timer > 0
    assert morale.run(b, hero, dun, [b], set()) is False
    assert b.__dict__.get('_yielded')                     # cornered, no friend: he begs


def test_d2_a_forced_flight_counts_down():
    b = make('bandit_thug', 10, 10)
    b.ai_pattern = 'cowardly'
    b._flee_timer = 8
    for _ in range(8):
        morale.turn(b, Hero(3, 3), [b], rng=Dice(1))
    assert b._flee_timer == 0


# ---------------------------------------------------------------- D3
def _chanting():
    s = make('skeleton_necromancer', 5, 5)
    s._chanting = True
    return s


def test_d3_the_line_names_who_broke_the_chant():
    s = _chanting()
    s.take_damage(3)
    assert any('Your blow breaks' in t for t, _u, _c in ai_lines.take(s))
    s = _chanting()
    summoning.CONTEXT = 'throes'
    try:
        s.take_damage(3)
    finally:
        summoning.CONTEXT = None
    assert any('The blast breaks' in t for t, _u, _c in ai_lines.take(s))

    class G:
        pass
    g = G()
    g._damage_by = 'pet'
    pet = type('P', (), {'alive': True, 'x': 6, 'y': 5, 'name': 'Ember'})()
    g.pets = [pet]
    import game_behaviour
    summoning.set_source_reader(lambda: (lambda m: game_behaviour.BehaviourMixin._ai_blow_source(g, m)))
    try:
        s = _chanting()
        s.take_damage(3)
        assert any('Your Ember breaks' in t for t, _u, _c in ai_lines.take(s))
        g._damage_by = 'monster'
        s = _chanting()
        s.take_damage(3)
        assert any('is struck, and his chant breaks off' in t for t, _u, _c in ai_lines.take(s))
    finally:
        summoning.set_source_reader(None)


def test_d3_a_bleed_ticking_breaks_no_chant():
    s = _chanting()
    s.status_effects['bleeding'] = 3
    s.tick_effects()
    assert s.__dict__.get('_chanting')


# ---------------------------------------------------------------- D4
def test_d4_a_bleed_or_a_burn_ticking_ends_no_hiding():
    for dot in ('bleeding', 'burning'):
        imp = make('imp', 12, 10)
        hero = Hero(3, 10)
        tiles = [[FLOOR] * 24 for _ in range(24)]
        for y in range(24):
            tiles[y][8] = WALL
        dun = Dungeon(tiles, [Room(0, 0, 24, 24)], 24, 24, 5)
        gone_again.begin_hiding(imp, hero)
        imp.status_effects[dot] = 5
        imp.tick_effects()
        assert not imp.__dict__.get('_struck'), dot
        assert gone_again.hiding_turn(imp, hero, dun) is False, dot
        assert imp._hit_run_state == 'hiding', dot


def test_d4_a_relurked_spider_is_not_sprung_by_its_own_bleeding():
    s = make('giant_spider')
    s.ai_pattern = 'aggressive'
    s._aware = True
    s.hp = int(s.max_hp * 0.5)
    s._lost_turns = 3
    assert relurk.consider(s)
    s.status_effects['bleeding'] = 5
    s.tick_effects()
    assert s.ai_pattern == 'ambush' and not s._aware


# ---------------------------------------------------------------- D5
def test_d5_a_captain_who_yields_leads_no_one():
    import war_bands
    lead = make('mercenary_veteran')
    f = hurt(make('bandit_thug'), 0.1)
    f._band_leader = lead
    assert war_bands.holds_nerve(f) and morale.held_by_others(f, Hero())
    morale.give_up(lead)
    assert not war_bands.holds_nerve(f)
    assert not morale.held_by_others(f, Hero())


# ---------------------------------------------------------------- D6
def test_d6_archers_hit_and_run_summoners_and_healers_have_a_nerve():
    for kind in ('bandit_archer', 'imp', 'skeleton_necromancer', 'orc_priest', 'young_red_dragon'):
        m = make(kind)
        assert morale.ruled(m), kind
    for kind in ('yellow_mold', 'floating_eye'):
        assert not morale.ruled(make(kind)), kind


def test_d6_a_broken_archer_runs_instead_of_shooting():
    a = hurt(make('bandit_archer', 10, 10), 0.2)
    a._aware = True
    hero = Hero(11, 10)
    morale.turn(a, hero, [a], rng=Dice(10))
    assert a._flee_timer > 0
    x0 = a.x
    assert a.take_turn(hero, open_room(), [a]) is False
    assert a.x < x0                                     # away from the hero, not a shot


# ---------------------------------------------------------------- D10
def test_d10_the_rot_ablation_leaves_the_prayer_as_it_was():
    import sim_ai1

    class Run:
        knobs = dict(sim_ai1.KNOBS, ai_rot=0)
        p = Hero()
    Run.p.status_effects['diseased'] = 20
    sim_ai1.prayed(Run, 5)
    assert Run.p.status_effects.get('diseased') == 20
    Run.knobs['ai_rot'] = 1
    sim_ai1.prayed(Run, 5)
    assert 'diseased' not in Run.p.status_effects


# ---------------------------------------------------------------- D9
def test_d9_the_disease_text_says_what_the_code_does():
    import status_effects
    label = status_effects.EFFECT_INFO['diseased'][2]
    assert 'Slowly drains' not in label and 'rest' in label.lower()
    page = open(os.path.join(ROOT, 'data', 'ui', 'monster_ways.json'), encoding='utf-8').read()
    hints = open(os.path.join(ROOT, 'data', 'hints.json'), encoding='utf-8').read()
    assert 'every heal does half' not in page and 'every heal does half' not in hints


# ---------------------------------------------------------------- slice M's kinds
def test_the_mandrakes_death_cry_rouses_what_hears_it_through_stone():
    import alarm
    w, h = 21, 10
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, 9):
        for x in range(1, 9):
            tiles[y][x] = FLOOR
        for x in range(12, 20):
            tiles[y][x] = FLOOR
    mand = make('mandrake', 5, 5)
    near = make('goblin', 14, 5)                       # beyond the wall, 9 tiles off
    far = make('goblin', 19, 8)
    far.x = 18
    for o in (near, far):
        o._aware = False
    radius = int(mand.__dict__.get('death_throes', MONS['mandrake']['death_throes'])['alarm_radius'])
    assert radius == 12
    assert alarm.cry(mand, [mand, near], Hero(3, 5), radius) == 1
    assert near._aware


def test_slice_m_kinds_carry_their_lore_on_this_engine():
    import kind_data
    assert kind_data.field(make('ponaturi'), 'turns_to_stone_in_light')
    assert any(a.get('shove') for a in MONS['reem']['attacks'])
    assert any(a.get('shove') for a in MONS['khalkotauros']['attacks'])
    assert morale.style(make('myrmekes')) == 'never'
    assert morale.style(make('taniwha')) == 'never'
