"""Bug bash 3.3.2: spells reach as far as their lore says (Brandon,
2026-11-07): "spells like Frost Touch are obviously supposed to be TOUCH,
but they have range... Geralt's runes don't have high range but do have
stronger power, and touch spells have a higher risk/reward because you have
to lay hands on."

Spells had no range at all: anything seen in a clear line could be struck.
Now a spell may carry a reach (spells.SPELL_REACH): touch (1) for Frost
Touch, Drain Life and Soul Drain, short (3) for the Witcher signs, Spark,
Acid Dart and Smite, sight for the rest. It is enforced where the aim is
taken (the target list, the cursor, the confirm). On the way: area spells
need a clear line (they struck through walls the Crown of Brahma or
tremor sense showed), and the aim overlay judges a spell by its own reach.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import spells  # noqa: E402
from spells import LEARNABLE_SPELLS, REACH_SHORT, REACH_TOUCH, spell_reach  # noqa: E402

_DEFS = None


# ---------------------------------------------------------------- data layer

def test_every_aimed_spell_says_how_far_it_reaches():
    for sid, sp in LEARNABLE_SPELLS.items():
        if sp.get('needs_target'):
            assert 'reach' in sp, sid
        assert sid not in spells.SPELL_REACH or sp.get('needs_target'), sid


def test_touch_spells_are_touch_and_signs_are_short():
    for sid in ('frost_touch_spell', 'drain_life_spell', 'soul_drain_spell'):
        assert spell_reach(LEARNABLE_SPELLS[sid]) == REACH_TOUCH, sid
    for sid in ('sign_aard', 'sign_igni', 'sign_yrden', 'sign_axii'):
        assert spell_reach(LEARNABLE_SPELLS[sid]) == REACH_SHORT, sid
    for sid in ('fire_bolt_spell', 'cold_bolt_spell', 'magic_missile_spell',
                'lightning_bolt_spell', 'sleep_spell'):
        assert spell_reach(LEARNABLE_SPELLS[sid]) is None, sid


def test_cold_bolt_keeps_its_range_though_it_shares_frost_touchs_effect():
    """The reach is the spell's, not the effect's."""
    assert LEARNABLE_SPELLS['cold_bolt_spell']['effect'] == 'frost_touch'
    assert spell_reach(LEARNABLE_SPELLS['cold_bolt_spell']) is None


def test_the_signs_hit_harder_than_they_did():
    assert LEARNABLE_SPELLS['sign_igni']['power'] == '1d4+2'
    assert LEARNABLE_SPELLS['sign_aard']['power'] == '1d4+2'
    assert LEARNABLE_SPELLS['sign_yrden']['duration'] > 8
    assert LEARNABLE_SPELLS['sign_axii']['duration'] > 10


# ---------------------------------------------------------- the real game

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
    import quiz_engine
    import save_system
    import bones
    from main import Game
    from game_states import STATE_PLAYER
    from dungeon import FLOOR
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path',
                        lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(4)
    g = Game(pygame.display.set_mode((1280, 720)),
             player_name='__test_bugbash_332_spell_reach__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    p = g.player
    # A clear 13 x 13 floor around the hero, all of it in sight.
    g.visible = set()
    for yy in range(p.y - 6, p.y + 7):
        for xx in range(p.x - 6, p.x + 7):
            if g.dungeon.in_bounds(xx, yy):
                g.dungeon.tiles[yy][xx] = FLOOR
                g.visible.add((xx, yy))
    p.max_mp = p.mp = 80
    return g


def _spawn(g, dx, dy=0, kind='giant_rat'):
    from monster import Monster
    m = Monster(_mdef(kind), g.player.x + dx, g.player.y + dy)
    # (Plain health: a rat given thousands counts as a big foe, and big foes
    # shrug off half of every hold.)
    m._aware = True
    g.monsters.append(m)
    return m


def test_frost_touch_will_not_aim_at_a_foe_two_tiles_off(game):
    from game_states import STATE_PLAYER
    _spawn(game, 2)
    mp = game.player.mp
    game._invoke_spell('frost_touch_spell')
    assert game.state == STATE_PLAYER
    assert game.player.mp == mp                         # nothing was spent


def test_frost_touch_aims_at_the_foe_beside_you(game):
    from game_states import STATE_TARGET
    near = _spawn(game, 1)
    _spawn(game, 3)
    game._invoke_spell('frost_touch_spell')
    assert game.state == STATE_TARGET
    assert game._target_candidates == [near]


def test_a_bolt_still_reaches_across_the_room(game):
    from game_states import STATE_TARGET
    far = _spawn(game, 5)
    game._invoke_spell('fire_bolt_spell')
    assert game.state == STATE_TARGET
    assert game._target_candidates == [far]


def test_a_sign_reaches_three_tiles_and_no_further(game):
    from game_states import STATE_TARGET
    three = _spawn(game, 3)
    _spawn(game, -4)
    game._invoke_spell('sign_igni')
    assert game.state == STATE_TARGET
    assert game._target_candidates == [three]


def test_the_cursor_stops_at_the_spells_reach(game):
    _spawn(game, 1)
    game._invoke_spell('frost_touch_spell')
    x0 = game.target_cursor_x
    game._target_input(pygame.K_RIGHT)                  # two tiles off: refused
    assert game.target_cursor_x == x0


def test_the_confirm_refuses_an_out_of_reach_target_and_refunds(game):
    from game_states import STATE_PLAYER
    _spawn(game, 1)
    far = _spawn(game, 2)
    mp = game.player.mp
    game._invoke_spell('frost_touch_spell')
    assert game.player.mp < mp
    game.target_cursor_x, game.target_cursor_y = far.x, far.y   # set by hand
    game._confirm_power_target()
    assert game.state == STATE_PLAYER
    assert game.player.mp == mp                         # the cost came back


def test_an_area_spell_no_longer_strikes_through_a_wall(game):
    """A tile shown through a wall (Crown of Brahma, tremor sense) is in
    sight, but nothing stands between the hero and it."""
    from dungeon import WALL
    p = game.player
    open_ = _spawn(game, 2)
    hidden = _spawn(game, 0, 3)
    game.dungeon.tiles[p.y + 1][p.x] = WALL
    game.dungeon.tiles[p.y + 2][p.x] = WALL
    assert (hidden.x, hidden.y) in game.visible
    game._apply_spell_effect(LEARNABLE_SPELLS['mass_sleep_spell'])
    assert open_.has_effect('sleeping')
    assert not hidden.has_effect('sleeping')


def test_yrden_holds_longer_than_it_did(game):
    m = _spawn(game, 2)
    game.player.INT = 10
    game._apply_spell_effect(LEARNABLE_SPELLS['sign_yrden'], m)
    assert m.status_effects.get('slowed', 0) >= 14
