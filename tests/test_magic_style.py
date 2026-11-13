"""Magic as a style (winning-build plan 3.6, slice 7, Brandon's decision 5,
2026-11-13).

Maths stays the backbone and magic becomes a style: the best single-target
spell of each tier is about one weapon chain (tests/test_magic_role.py holds
the bands), so the right element on a x2 weakness is a two-chain blow. A
caster's Intelligence deepens the quiet he meditates in each floor (half of
max MP, a point more per point of INT over 10, never past 80%), and light
body armour is his natural kit: metal taxes every cast (slice 4), mithril
does not.

Logic tests on the floor curve, the Player and a real headless Game. Whether
casting FEELS like a style is Brandon's play-test (plan section 6).
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

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import floor_curve  # noqa: E402
import items  # noqa: E402
import magic_audit  # noqa: E402
from player import Player  # noqa: E402
from spells import LEARNABLE_SPELLS  # noqa: E402

_DEFS = None


# ------------------------------------------------------------- the quiet

def test_intelligence_deepens_the_floors_quiet():
    share = floor_curve.meditation_share
    assert share(10) == floor_curve.MEDITATE_FLOOR_SHARE == 0.5     # a plain hero: half
    assert share(11) == 0.51 and share(20) == 0.60 and share(34) == 0.74
    assert share(3) == 0.5                                           # never under half
    assert floor_curve.meditation_allowance(30) == 15                # INT left out: INT 10
    assert floor_curve.meditation_allowance(30, 20) == 18
    assert floor_curve.meditation_allowance(56, 46) == 45            # tier-5 build: capped


def test_the_quiet_never_passes_eighty_percent():
    assert floor_curve.MEDITATE_SHARE_CAP == 0.80
    assert floor_curve.meditation_share(40) == 0.80
    for intelligence in (41, 46, 60, 100, 500):
        assert floor_curve.meditation_share(intelligence) == 0.80
    assert floor_curve.meditation_allowance(100, 999) == 80


def test_a_keener_mind_meditates_more_on_a_floor():
    plain, sage = Player(), Player()
    sage.INT = 30
    for p in (plain, sage):
        p.max_mp, p.mp = 40, 0
    assert plain.meditation_left(5) == 20
    assert sage.meditation_left(5) == 28                       # 70% of 40
    got = sum(sage.meditate(1, 5) for _ in range(60))
    assert got == 28 and sage.meditation_left(5) == 0          # and it is still drawn once
    assert sage.meditation_left(6) == 28                       # another floor has its own


# ------------------------------------------------------------ the real game

def _mdef(kind):
    global _DEFS
    if _DEFS is None:
        with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
            _DEFS = json.load(f)
    d = dict(_DEFS[kind])
    d.setdefault('id', kind)
    return d


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import quiz_engine
    import save_system
    from dungeon import FLOOR
    from game_states import STATE_PLAYER
    from main import Game
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path',
                        lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(7)
    g = Game(pygame.display.set_mode((1280, 720)), player_name='__test_magic_style__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    p = g.player
    g.visible = set()
    for yy in range(p.y - 6, p.y + 7):
        for xx in range(p.x - 6, p.x + 7):
            if g.dungeon.in_bounds(xx, yy):
                g.dungeon.tiles[yy][xx] = FLOOR
                g.visible.add((xx, yy))
    p.max_mp = p.mp = 80
    return g


def _spawn(g, kind, dx=2, dy=0):
    from monster import Monster
    m = Monster(_mdef(kind), g.player.x + dx, g.player.y + dy)
    m.max_hp = m.hp = 3000            # plenty of health: nothing dies
    m._aware = True
    g.monsters.append(m)
    return m


def _hurt(g, spell_id, kind, monkeypatch, roll=None):
    """What one cast of `spell_id` takes off a fresh `kind`, its dice held
    at their mean (or `roll`)."""
    import dice
    spell = LEARNABLE_SPELLS[spell_id]
    value = roll if roll is not None else int(magic_audit.dice_mean(spell['power']))
    monkeypatch.setattr(dice, 'roll', lambda _n: value)
    for m in g.monsters:
        m.alive = False
    g.monsters = []
    m = _spawn(g, kind)
    before = m.hp
    g._apply_spell_effect(spell, m)
    return before - m.hp


def test_the_kinds_carry_the_fire_their_lore_gives():
    """The mummy's wrappings burn; an iron golem is forged in fire; a fire
    elemental is fire; a goblin is nothing special (data/family_affinity.json)."""
    assert 'fire' in _mdef('mummy')['weaknesses']
    assert 'fire' in _mdef('iron_golem')['resistances']
    assert 'fire' in _mdef('fire_elemental')['shrugs_off']
    g = _mdef('goblin')
    assert not any('fire' in (g.get(f) or ()) for f in ('weaknesses', 'resistances', 'shrugs_off'))
    assert 'lightning' in _mdef('animated_armor')['weaknesses']


def test_a_fire_bolt_on_a_fire_weak_kind_does_four_times_a_resisted_kinds(game, monkeypatch):
    plain = _hurt(game, 'fire_bolt_spell', 'goblin', monkeypatch, roll=10)
    weak = _hurt(game, 'fire_bolt_spell', 'mummy', monkeypatch, roll=10)
    resisted = _hurt(game, 'fire_bolt_spell', 'iron_golem', monkeypatch, roll=10)
    shrugged = _hurt(game, 'fire_bolt_spell', 'fire_elemental', monkeypatch, roll=10)
    assert plain == int(10 * 7.5 * 2.0) == 150                 # T2 x7.5, INT 10 x2
    assert weak == 2 * plain                                   # weak x2
    assert resisted == plain // 2                              # resisted x0.5
    assert weak == 4 * resisted
    assert shrugged == int(plain * 0.25)                       # shrugs off x0.25


def test_the_right_element_on_a_weakness_is_a_two_chain_blow(game, monkeypatch):
    """Lightning Bolt, tier 2's best bolt, at its mean on a floor-30 foe:
    about one weapon chain, and about two on a kind weak to lightning."""
    one = floor_curve.one_attack(30)
    plain = _hurt(game, 'lightning_bolt_spell', 'goblin', monkeypatch)
    weak = _hurt(game, 'lightning_bolt_spell', 'animated_armor', monkeypatch)
    assert 0.95 <= plain / one <= 1.05, plain / one
    assert 1.9 <= weak / one <= 2.1, weak / one


def test_metal_armour_taxes_an_aimed_spell_and_mithril_does_not(game):
    """Slice 4's tax on every cast path: the aimed spell is charged in plate
    and given back exactly on a cancel; mithril casts at full price."""
    from game_states import STATE_TARGET
    p = game.player
    p.known_spells['fire_bolt_spell'] = 6
    _spawn(game, 'goblin', dx=3)
    p._apply_equip(items.instantiate_armor('plate', 'chain_steel'))
    game._invoke_spell('fire_bolt_spell')
    assert game.state == STATE_TARGET
    assert p.mp == 80 - 12                                       # 6 MP, doubled in steel plate
    assert game._refund_pending_spell() and p.mp == 80           # and exactly that comes back
    p._apply_equip(items.instantiate_armor('plate', 'mithril'))
    assert p.spell_mp_cost(6) == 6
    game._invoke_spell('fire_bolt_spell')
    assert p.mp == 80 - 6                                        # mithril casts freely
    game._refund_pending_spell()
    leather = Player()
    leather._apply_equip(items.instantiate_armor('leather', 'leather'))
    assert leather.spell_mp_cost(22) == 22                       # the caster's natural kit


def test_the_wayside_heal_is_charged_like_any_cast():
    """The Cast Heal choice at an encounter pays what the spell menu would."""
    src = open(os.path.join(ROOT, 'src', 'game_encounters.py'), encoding='utf-8').read()
    assert src.count("spell_mp_cost(self.player.known_spells.get('heal_spell', 99))") == 1
    assert src.count("self.player.spell_mp_cost(\n                            "
                     "self.player.known_spells.get('heal_spell', 8))") == 1
    assert "mp_cost = self.player.known_spells.get('heal_spell'" not in src
