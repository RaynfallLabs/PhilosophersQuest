"""Tests for the hero's speed: haste, Speed boots and the world's clock.

Bug once prevented: the original haste auto-fired a second `_do_move(dx,
dy)` inside the move handler, so one arrow-key press moved the hero TWO
tiles. User intent: the hero moves twice as fast as the *monsters*, not
twice per keystroke.

Today (2026-11-12, Brandon: "Monsters have a speed rating, yes? that
changes how often they act in relation to the player? that's what this
power should do"): the hero has a speed rating on the monsters' scale
(Player.get_speed: 10 is ordinary, haste doubles it, Speed boots add a
share). Each action moves the world's clock on 10/speed of a turn; the
world (`_do_monster_turns`, `_do_pet_turns`, `_maybe_wander_spawn`) acts
each time it passes a whole turn. No dice. Player-side ticks happen on
every action. Haste no longer lengthens the quiz clock ("Wisdom increases
timer, not how fast you are").
"""
from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()


# ---------------------------------------------------------------------------
# Source-level regression tests
# ---------------------------------------------------------------------------

def test_do_move_no_auto_second_step():
    """Regression: `_do_move` must not auto-fire a second `_do_move` when
    the hero is hasted (one keystroke moved two tiles)."""
    import main
    src = inspect.getsource(main.Game._do_move)
    assert "_haste_active" not in src, (
        "regression: `_haste_active` re-entry flag is back in _do_move, "
        "which means the auto-second-step bug has been reintroduced"
    )


def test_advance_turn_gates_the_world_on_the_clock():
    """The world-tick methods sit inside the loop over the world's turns
    (defence.world_turns: none, one or, for a slow hero, two), and the
    clock is read from the hero's speed before them."""
    import main
    src = inspect.getsource(main.Game._advance_turn)
    gate = "for _wt in range(_n_world):"
    assert "get_speed(" in src and "world_turns(" in src
    assert src.find("get_speed(") < src.find("self._do_monster_turns()")
    assert gate in src, f"expected gate line '{gate}' in _advance_turn"
    after_gate = src[src.index(gate):]
    for call in ("self._do_monster_turns()", "self._do_pet_turns()",
                 "self._maybe_wander_spawn()"):
        assert call in after_gate, f"{call} must be gated by the world's clock"
    assert "_haste_skip_world" not in src           # the old toggle is gone


# ---------------------------------------------------------------------------
# The clock, by itself (defence.world_turns: _advance_turn's own arithmetic)
# ---------------------------------------------------------------------------

def _clock_step(state: dict, speed: float) -> int:
    """The world's turns this action (0: it waits)."""
    import defence
    n, state['clock'] = defence.world_turns(state.get('clock', 0.0), speed)
    return n


def _ticks(speed, actions):
    state: dict = {}
    return sum(_clock_step(state, speed) for _ in range(actions))


def test_haste_is_two_actions_to_a_world_turn():
    assert _ticks(20, 6) == 3
    state: dict = {}
    assert [_clock_step(state, 20) for _ in range(4)] == [0, 1, 0, 1]


def test_ordinary_speed_never_waits_and_a_slow_hero_gives_the_world_more():
    assert _ticks(10, 10) == 10
    # Since 2026-11-16 a speed under 10 counts (armour too heavy for the
    # hero's Strength, or his load): the world takes two turns on some
    # actions. The Slowed status still costs him his own turn in _do_move.
    assert _ticks(7, 7) == 10
    assert _ticks(5, 10) == 20


def test_a_fresh_haste_begins_by_waiting():
    state: dict = {}
    assert _clock_step(state, 20) == 0              # one hasted action, then it ends
    assert _clock_step(state, 10) == 1
    assert _clock_step(state, 20) == 0              # the next haste starts the same way


def test_speed_boots_save_one_world_turn_in_twenty_one():
    assert _ticks(10.5, 21) == 20
    assert _ticks(10.8, 108) == 100


# ---------------------------------------------------------------------------
# The real game
# ---------------------------------------------------------------------------

@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__haste_clock__', secret_build=None)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def _world_turns(g, actions):
    n = [0]
    g._do_monster_turns = lambda: n.__setitem__(0, n[0] + 1)
    for _ in range(actions):
        g._advance_turn()
    return n[0]


def test_a_hasted_hero_gets_two_actions_to_the_monsters_one(game):
    game.player.status_effects['hasted'] = 99
    assert _world_turns(game, 6) == 3


def test_an_ordinary_hero_gets_one(game):
    assert _world_turns(game, 6) == 6


def test_boots_of_speed_quicken_the_hero_a_little(game):
    import items
    p = game.player
    boots = items.instantiate_armor('leather_boots', 'leather', level=7, ench_id='speed')
    p.inventory.append(boots)
    p._apply_equip(boots)
    p.remove_from_inventory(boots)
    assert not p.has_effect('hasted')               # no haste: a speed rating
    assert p.get_speed() == 10.5
    assert _world_turns(game, 21) == 20


def test_status_effect_description_updated():
    """The tooltip says what haste does (the monsters' cadence), not the
    old wrong text ('Extra action each turn')."""
    from status_effects import EFFECT_INFO
    label, _color, desc = EFFECT_INFO["hasted"]
    assert label == "Hasted"
    assert "Extra action" not in desc
    assert "monster" in desc.lower() or "half" in desc.lower()


def test_haste_does_not_lengthen_the_clock():
    from player import Player
    p = Player()
    before = p.get_quiz_timer_modifier()
    p.status_effects['hasted'] = 10
    assert p.get_quiz_timer_modifier() == before
