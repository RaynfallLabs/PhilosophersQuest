"""Slice M's kinds under AI-1's monster behaviour (MONSTERS AND MAGIC,
2026-11-19).

The new kinds carry AI-1's fields in AI-1's shapes
(_mm_2026_11_19/AI1/FIELDS.md). Each test here is seeded and shows the field
taking effect in AI-1's own code (death_throes, relurk, light_shy, alarm,
breath, life_drain, morale), not only that the data is there.
"""
import json
import os
import random
import sys
from types import SimpleNamespace

import pytest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))

import ai_blow  # noqa: E402
import ai_lines  # noqa: E402
import alarm  # noqa: E402
import breath  # noqa: E402
import counters  # noqa: E402
import death_throes  # noqa: E402
import life_drain  # noqa: E402
import light_shy  # noqa: E402
import morale  # noqa: E402
import relurk  # noqa: E402
import senses  # noqa: E402
import tells  # noqa: E402
from dungeon import Dungeon, Room, WALL, FLOOR  # noqa: E402
from mm_kinds_data import NEW  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))


class Hero:
    """Enough of a hero for the monster's side of a fight (AI-1's test hero)."""
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
        self.inventory = []

    def has_effect(self, name):
        return self.status_effects.get(name, 0) > 0

    def is_burdened(self):
        return False

    def get_ac(self):
        return 10

    def get_sight_radius(self):
        return 8

    def take_damage(self, amount, damage_type='physical'):
        actual = max(0, int(amount))
        self.hp = max(0, self.hp - actual)
        return actual

    def save_bonus_for(self, _stat):
        return 0

    def add_effect(self, name, duration):
        self.status_effects[name] = duration
        return True


class Torch:
    item_class = 'light'

    def __init__(self):
        self.id = 'torch'
        self.lit = True
        self.burn = self.fuel = 400
        self.sight = 2
        self.noun = 'torch'
        self.power = ''


class Dice:
    """An rng whose every d10 shows ``face`` (morale's 2d10)."""
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


def make(kind, x=5, y=5):
    return Monster({**MONS[kind], 'id': kind}, x, y)


def setup_function(_):
    random.seed(7)
    senses.begin_turn(moved=True, guilty=False, floor=5)
    for mod in (alarm, breath, death_throes, life_drain, light_shy, morale, relurk):
        mod.ENABLED = True


# --------------------------------------------- death_throes: the Mandrake

def test_the_mandrake_keens_then_shrieks_as_it_dies_and_wax_stops_the_stun():
    m = make('mandrake', 5, 5)
    m.hp = 1
    death_throes.warn(m)
    assert any('keening' in t for t, _u, _c in ai_lines.take(m))
    assert death_throes.should_burst(m)
    assert death_throes.blast(m, 200) == 10                 # a twentieth of his own health
    dun = open_room()
    assert death_throes.in_blast(m, 7, 5, dun) and not death_throes.in_blast(m, 8, 5, dun)
    # The shriek is a voice: wax in the ears stops its stun, as
    # game_behaviour._ai_burst asks counters.blocks_rider.
    t = death_throes.spec(m)
    cry = {'name': 'Death Throes', 'delivery': t['delivery']}
    deaf = SimpleNamespace(ears_stopped=True, inventory=[SimpleNamespace(counters=['voice'])])
    hearing = SimpleNamespace(ears_stopped=False, inventory=[])
    assert counters.blocks_rider(deaf, m, cry, t['effect']) is not None
    assert counters.blocks_rider(hearing, m, cry, t['effect']) is None


# ------------------------------------- relurks: back into hiding, once

@pytest.mark.parametrize('kind', ['asanbosam', 'ahuizotl', 'tsuchigumo'])
def test_a_hurt_new_ambusher_out_of_sight_goes_back_into_hiding_once(kind):
    s = make(kind)
    assert s.ai_pattern == 'ambush'
    s.ai_pattern = 'aggressive'                              # sprung (Monster.take_turn)
    s._aware = True
    s.hp = int(s.max_hp * 0.5)
    s._lost_turns = 3
    assert relurk.consider(s, Hero(8, 5))
    assert s.ai_pattern == 'ambush' and not s._aware
    s.ai_pattern = 'aggressive'
    s._aware = True
    assert not relurk.consider(s)                            # once a life
    assert 'relurks' in tells.abilities(s)


# ------------------------------------------- light_shy: they flinch

@pytest.mark.parametrize('kind', ['ponaturi', 'star_jelly'])
def test_a_light_shy_new_kind_strikes_worse_in_the_hero_s_light(kind):
    m = make(kind, 5, 5)
    hero = Hero(6, 5)
    atk = m.attacks[0]
    assert ai_blow.to_hit_shift(m, hero, atk) == 0           # in the dark
    hero.shield = Torch()
    assert ai_blow.to_hit_shift(m, hero, atk) == 2           # the hook Monster._resolve_blow adds
    hero.status_effects['light'] = 10
    assert light_shy.flinch(m, hero) == 4                    # the Light spell, capped
    assert 'light_shy' in tells.abilities(m)


# ------------------------------------- alarm: the Waq-Waq Tree cries out

def test_the_waq_waq_cry_brings_what_lives_near_once_a_floor():
    dun = open_room(30, 10)
    tree = make('waq_waq_tree', 5, 5)
    near_beast = make('wolf', 12, 5)
    near_man = make('goblin', 10, 3)
    far = make('wolf', 22, 5)
    for o in (near_beast, near_man, far):
        o._tracking = False
        o._aware = False
    others = [tree, near_beast, near_man, far]
    assert alarm.shout(tree, others, Hero(3, 5), dun) == 2
    assert near_beast._aware and near_man._aware and not far._aware
    assert alarm.shout(tree, others, Hero(3, 5), dun) == 0           # once a floor
    assert any('Waq' in t for t, _u, _c in ai_lines.take(tree))
    assert 'raises_alarm' in tells.abilities(tree)


def test_a_silenced_waq_waq_tree_cannot_cry_out():
    dun = open_room(30, 10)
    tree = make('waq_waq_tree', 5, 5)
    wolf = make('wolf', 9, 5)
    wolf._tracking = wolf._aware = False
    tree.status_effects['silenced'] = 5
    assert alarm.shout(tree, [tree, wolf], Hero(3, 5), dun) == 0 and not wolf._aware


# ------------------------------- snuffs_light: the Bakunawa swallows it

def test_the_bakunawa_swallows_the_light_about_half_the_time():
    m = make('bakunawa', 5, 5)
    jaws = next(a for a in m.attacks if a.get('snuffs_light'))
    assert jaws['snuffs_light'] == 'dark' and jaws['snuff_chance'] == 0.5
    random.seed(3)
    out = 0
    for _ in range(200):
        hero = Hero(6, 5)
        hero.shield = Torch()
        light_shy.after_blow(m, hero, jaws, 10, '')
        out += not hero.shield.lit
    assert 70 <= out <= 130
    # The dark it brings ends the Light spell too.
    hero = Hero(6, 5)
    hero.shield = Torch()
    hero.status_effects['light'] = 5
    light_shy.snuff(hero, jaws['snuffs_light'])
    assert 'light' not in hero.status_effects and not hero.shield.lit
    assert 'snuffs_light' in tells.abilities(m)


# --------------------------- recharge: the Catoblepas lifts its head again

def test_the_catoblepas_must_lift_its_head_again_before_the_next_gaze():
    c = make('catoblepas', 5, 5)
    gaze = next(a for a in c.attacks if a['name'] == 'Death Gaze')
    assert breath.recharge_of(c, gaze) == 4
    breath.spend(c, gaze)
    for _ in range(3):
        c.tick_effects()
        assert not breath.ready(c, gaze)
    c.tick_effects()
    assert breath.ready(c, gaze)
    assert 'breath_recharge' in tells.abilities(c)


BREATHERS = sorted(k for k in NEW
                   if any(a.get('delivery') == 'breath' for a in MONS[k]['attacks']))


@pytest.mark.parametrize('kind', BREATHERS)
def test_each_new_breath_must_be_drawn_again(kind):
    m = make(kind)
    b = next(a for a in m.attacks if a.get('delivery') == 'breath')
    assert breath.recharge_of(m, b) == 3                     # the default for a breath
    breath.spend(m, b)
    assert not breath.ready(m, b)
    for _ in range(3):
        m.tick_effects()
    assert breath.ready(m, b)


def test_the_breathers_are_the_ones_the_lore_gives_a_breath():
    assert BREATHERS == ['blue_men_of_the_minch', 'khalkotauros', 'mandrake', 'myrmekes',
                         'nuckelavee', 'yacumama', 'yuki_onna']


# ------------------------------------ life_drain: what rest will not give back

DRAINERS = sorted(k for k in list(NEW) + ['nosferatu']
                  if any(life_drain.drains_life(a) for a in MONS[k]['attacks']))


@pytest.mark.parametrize('kind', DRAINERS)
def test_each_new_drainer_takes_life_that_rest_will_not_give_back(kind, monkeypatch):
    p = Player()
    p.max_hp = p.hp = 200
    m = make(kind)
    atk = next(a for a in m.attacks if life_drain.drains_life(a))
    monkeypatch.setattr(life_drain, 'save_holds', lambda mm, pl, rng=None: False)
    msg = life_drain.after_blow(m, p, atk, 12, 'hit.')
    assert p.max_hp == 194 and life_drain.drained(p) == 6 and 'Max HP -6' in msg
    assert 'life_drain' in tells.abilities(m)


def test_the_drainers_are_the_blood_drinkers_and_the_life_takers():
    assert DRAINERS == ['asanbosam', 'impundulu', 'nosferatu', 'preta', 'yuki_onna']


# ------------------------------------------------- morale by family

# Each kind's nerve from its family (data/monster_ai.json 'morale'); a kind
# immune to fear never breaks (the centaur, the Vetala, the nuckelavee, the
# re'em).
NERVE = {
    'mandrake': 'never', 'kappa': 'bolt', 'eloko': 'withdraw', 'asanbosam': 'withdraw',
    'ahuizotl': 'bolt', 'khalkotauros': 'never', 'cu_sith': 'withdraw', 'bulgasari': 'never',
    'vetala': 'never', 'nahual': 'bolt', 'likho': 'withdraw', 'centaur': 'never',
    'blue_men_of_the_minch': 'withdraw', 'vila': 'withdraw', 'myrmekes': 'bolt',
    'ponaturi': 'regroup', 'taniwha': 'bolt', 'impundulu': 'bolt', 'mapinguari': 'bolt',
    'preta': 'never', 'upas_tree': 'never', 'nuckelavee': 'never', 'star_jelly': 'never',
    'psoglav': 'regroup', 'waq_waq_tree': 'never', 'yuki_onna': 'withdraw', 'yacumama': 'bolt',
    'tsuchigumo': 'bolt', 'bhuta_vahana_yanta': 'never', 'reem': 'never', 'eitr': 'never',
    'bakunawa': 'bolt',
}


def test_every_new_kind_has_its_nerve_written_here():
    assert sorted(NERVE) == sorted(NEW)


@pytest.mark.parametrize('kind', sorted(NEW))
def test_each_new_kind_keeps_its_family_s_nerve(kind):
    m = make(kind)
    assert morale.style(m) == NERVE[kind]
    if not morale.ruled(m):
        # Morale is the aggressive hunter's (morale.ruled): an ambusher, an
        # archer, a hit-and-run kind or a rooted one keeps its own way.
        assert m.ai_pattern != 'aggressive'
        return
    m.hp = max(1, int(m.max_hp * 0.2))
    morale.turn(m, Hero(6, 5), [m], rng=Dice(10))           # 2d10 = 20: it breaks if it can
    if NERVE[kind] == 'never':
        assert m._flee_timer == 0
    else:
        assert m._flee_timer > 0
        if NERVE[kind] == 'bolt':
            assert m.__dict__.get('_bolting')
