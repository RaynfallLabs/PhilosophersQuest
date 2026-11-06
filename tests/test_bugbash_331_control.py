"""Bug bash 3.3.1, control effects (B1 charm, B2 fear).

The charm wand set the target's ai_pattern to 'sessile' for good: a
sessile monster skips the mind-affecting statuses, so the charmed creature
still struck when the hero stood next to it, and it stayed rooted after the
charm ran out. The fear wand, the panic wave and the fear spell set
'cowardly' for good: the creature fled for the rest of the floor, not the N
turns the message promised. The statuses alone carry the behaviour
(Monster.take_turn honours 'feared' and 'charmed' for every AI pattern).

Behaviour tests on a real headless Game. The feel in play is a play-test
question: Claude cannot drive Pygame.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import items  # noqa: E402

_SCREEN = None
_DEFS = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=5):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name='__test_bugbash_331_control__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _mdef(kind):
    global _DEFS
    if _DEFS is None:
        with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
            _DEFS = json.load(f)
    d = dict(_DEFS[kind])
    d.setdefault('id', kind)
    return d


def _open_floor(g, r=5):
    from dungeon import FLOOR
    for yy in range(g.player.y - r, g.player.y + r + 1):
        for xx in range(g.player.x - r, g.player.x + r + 1):
            if g.dungeon.in_bounds(xx, yy):
                g.dungeon.tiles[yy][xx] = FLOOR


def _spawn(g, kind, dx=1, dy=0):
    from monster import Monster
    m = Monster(_mdef(kind), g.player.x + dx, g.player.y + dy)
    m._aware = True
    m.speed = 10                     # no skipped turns in the measurement
    g.monsters.append(m)
    return m


def _zap(g, wand_id, target):
    w = items.make_item_by_id('wand', wand_id)
    w.charges = 5
    g._wand_override_target = target
    try:
        g._apply_wand_effect(w)
    finally:
        g._wand_override_target = None


def _turn(g, m):
    """One monster turn plus the per-turn status tick, as the game runs it."""
    attacked = m.take_turn(g.player, g.dungeon, g.monsters)
    m.tick_effects()
    return attacked


# ---------------------------------------------------------------------------
# B1: charm
# ---------------------------------------------------------------------------

def test_b1_charmed_monster_does_not_attack_and_charm_wears_off():
    g = _game(seed=11)
    _open_floor(g)
    rat = _spawn(g, 'giant_rat')
    pattern = rat.ai_pattern
    _zap(g, 'wand_of_charm', rat)
    dur = rat.status_effects.get('charmed', 0)
    assert 0 < dur < 1000, "the charm wand promises a number of turns"
    attacks = 0
    for _ in range(dur):
        # Keep it next to the hero, so a blow is always possible.
        rat.x, rat.y = g.player.x + 1, g.player.y
        attacks += 1 if _turn(g, rat) else 0
    assert attacks == 0, f"a charmed creature struck the hero {attacks} times"
    assert not rat.has_effect('charmed')
    assert rat.ai_pattern == pattern, "charm must not re-pattern the creature for good"
    rat.x, rat.y = g.player.x + 1, g.player.y
    assert _turn(g, rat) is True, "once the charm is over it fights again"


def test_b1_charm_wand_tells_the_truth_about_the_undead():
    """The undead feel no affection (Monster.resists_control): the wand used
    to say 'gazes at you with adoration' and root it instead."""
    g = _game(seed=12)
    _open_floor(g)
    sk = _spawn(g, 'skeleton')
    assert sk.resists_control('charmed')
    _zap(g, 'wand_of_charm', sk)
    texts = [str(e[0]) for e in g.msg_log.entries[-3:]]
    assert not any('adoration' in t for t in texts), texts
    assert sk.ai_pattern != 'sessile'




def test_b1_a_rooted_creature_charmed_holds_its_blow():
    """A creature that is sessile by nature (a roper) cannot wander off when
    charmed, but it does not strike the hero either."""
    g = _game(seed=13)
    _open_floor(g)
    roper = _spawn(g, 'roper')
    assert roper.ai_pattern == 'sessile' and not roper.resists_control('charmed')
    assert roper.take_turn(g.player, g.dungeon, g.monsters) is True    # it strikes
    roper.add_effect('charmed', 5)
    assert roper.take_turn(g.player, g.dungeon, g.monsters) is False
    assert (roper.x, roper.y) == (g.player.x + 1, g.player.y)
