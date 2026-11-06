"""Bug bash 3.3.1, equipment A7: Joyeuse's dazzle.

Joyeuse (combat_start_aoe_confuse_chance 0.5): "It dazzles before it cuts."
At the start of a melee attack, half the time, the foes near the hero reel.
What was wrong with it:

1. It set confused for 1 turn, and every monster's statuses tick down in
   _advance_turn BEFORE the monsters move: the dazzle had always worn off by
   the time anyone acted. The codebase writes "stunned for 1 turn" as 2 (the
   mace's stun_at_max); the dazzle now does the same.
2. The log line named the sword by its true name, so an unidentified
   "radiant blade" announced itself as Joyeuse.
3. It reached through walls and onto invisible creatures, and counted
   creatures with no mind to confuse, so "nearby foes reel" told the hero
   about foes he could not see. A flash has to be seen: only foes the hero
   can see, with minds, reel now.

Real headless Game: _start_combat, the attack's quiz callback and the turn
are the game's own. A floor-61 unique; not play-testable in a sitting.
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import items  # noqa: E402
from quiz_engine import QuizResult  # noqa: E402

pygame.init()

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    _DEFS = json.load(_f)


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__bb331_joyeuse__', secret_build=None)
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    from dungeon import FLOOR
    for yy in range(g.player.y - 4, g.player.y + 5):
        for xx in range(g.player.x - 4, g.player.x + 5):
            if g.dungeon.in_bounds(xx, yy):
                g.dungeon.tiles[yy][xx] = FLOOR
    return g


def _spawn(g, kind, dx, dy):
    from monster import Monster
    m = Monster(dict(_DEFS[kind], id=kind), g.player.x + dx, g.player.y + dy)
    m.hp = m.max_hp = 10 ** 6
    m._aware = True
    g.monsters.append(m)
    return m


def _wield_joyeuse(g):
    joy = next(w for w in items.load_items('weapon') if w.id == 'joyeuse')
    g.player.inventory.append(joy)
    g.player._apply_equip(joy)
    g.player.remove_from_inventory(joy)
    return joy


def _dazzle(g, target):
    """Start a melee attack with the dazzle's roll forced to succeed (the
    quiz is now up; nothing has moved yet)."""
    import game_combat
    real_random = game_combat.random.random
    game_combat.random.random = lambda: 0.0
    try:
        g._refresh_fov()
        g._start_combat(target)
    finally:
        game_combat.random.random = real_random


def _swing(g, target):
    """The dazzle, then the attack finished with a wrong answer (a miss) so
    the turn runs."""
    _dazzle(g, target)
    cb, g.quiz_engine.callback = g.quiz_engine.callback, None
    cb(QuizResult(success=True, score=0, correct=0, asked=1))


def _log(g):
    return [t for t, _k in g.msg_log.entries]


def test_the_dazzle_lasts_until_the_dazzled_foe_acts(game, monkeypatch):
    _wield_joyeuse(game)
    gob = _spawn(game, 'goblin', 1, 0)
    seen = []
    real = type(gob).take_turn

    def spy(self, *a, **k):
        seen.append(self.has_effect('confused'))
        return real(self, *a, **k)
    monkeypatch.setattr(type(gob), 'take_turn', spy)
    _swing(game, gob)
    assert seen and seen[0] is True                  # confused on its own turn


def test_the_dazzle_line_does_not_name_an_unknown_joyeuse(game, monkeypatch):
    joy = _wield_joyeuse(game)
    assert 'Joyeuse' not in game._bare_name(joy)     # still unidentified
    gob = _spawn(game, 'goblin', 1, 0)
    _swing(game, gob)
    lines = [t for t in _log(game) if 'flashes' in t]
    assert lines and not any('Joyeuse' in t for t in lines)


def test_the_dazzle_needs_to_be_seen(game, monkeypatch):
    _wield_joyeuse(game)
    gob = _spawn(game, 'goblin', 1, 0)
    hidden = _spawn(game, 'goblin', 0, 2)
    hidden.invisible = True                          # unseen.is_invisible
    golem = _spawn(game, 'iron_golem' if 'iron_golem' in _DEFS else 'clay_golem', -1, 0)
    assert golem.resists_control('confused')         # no mind to confuse
    _dazzle(game, gob)
    assert gob.status_effects.get('confused', 0) > 0
    assert hidden.status_effects.get('confused', 0) == 0
    assert golem.status_effects.get('confused', 0) == 0


def test_no_line_when_only_hidden_foes_are_near(game, monkeypatch):
    _wield_joyeuse(game)
    gob = _spawn(game, 'goblin', 1, 0)
    gob.invisible = True                              # the target itself unseen
    _swing(game, gob)
    assert not any('flashes' in t for t in _log(game))
