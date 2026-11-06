"""Bug bash 3.3.1, B9: Solomon's command over demons.

Solomon's Authority (passive_pacify_demon_chance) rolled for each demon
"newly seen this floor", kept in a set that is emptied on every floor
entry (and never saved), so a stair trip or a reload rolled every demon
again; and it put bosses and seal demons to sleep for 15 turns, past the
named-foe cap. The Robes of Solomon's once-a-floor demon command took the
first demon in sight, a named one too: the charm never holds on a named
foe, so the floor's charge was spent on a lie ("compels the ... to your
service").

Behaviour tests on a real headless Game.
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
    g = Game(_screen(), player_name='__test_bugbash_331_divine__')
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


def _open_floor(g, r=4):
    from dungeon import FLOOR
    for yy in range(g.player.y - r, g.player.y + r + 1):
        for xx in range(g.player.x - r, g.player.x + r + 1):
            if g.dungeon.in_bounds(xx, yy):
                g.dungeon.tiles[yy][xx] = FLOOR


def _spawn(g, kind, dx=2, **attrs):
    from monster import Monster
    m = Monster(_mdef(kind), g.player.x + dx, g.player.y)
    for k, v in attrs.items():
        setattr(m, k, v)
    g.monsters.append(m)
    return m


def _ring(monkeypatch, chance=1.0):
    import chain_passives
    monkeypatch.setattr(chain_passives, 'get_pacify_demon_chance', lambda player: chance)


def _texts(g, n=10):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def test_b9_solomons_authority_rolls_once_per_demon(monkeypatch):
    g = _game(seed=91)
    _open_floor(g)
    imp = _spawn(g, 'imp')
    _ring(monkeypatch, 1.0)
    g._refresh_fov()
    assert imp.has_effect('sleeping'), "the ring pacifies a demon it sees"
    imp.status_effects.pop('sleeping', None)
    # Going down and back up the stair empties the floor's bookkeeping
    # (_change_level does this); a reload does the same.
    g._chain_pacify_seen = set()
    g._refresh_fov()
    assert not imp.has_effect('sleeping'), "the same demon was rolled a second time"


def test_b9_solomons_authority_never_pacifies_a_named_foe(monkeypatch):
    g = _game(seed=92)
    _open_floor(g)
    boss = _spawn(g, 'imp', is_boss=True)
    seal = _spawn(g, 'imp', dx=-2, is_seal_demon=True)
    _ring(monkeypatch, 1.0)
    g._refresh_fov()
    assert not boss.has_effect('sleeping')
    assert not seal.has_effect('sleeping')
    assert not any('pacifies' in t for t in _texts(g))


def test_b9_robes_of_solomon_do_not_spend_the_command_on_a_named_demon(monkeypatch):
    import chain_passives
    spent = []
    monkeypatch.setattr(chain_passives, 'player_has_passive',
                        lambda player, flag: flag == 'demon_command_one_per_floor')
    monkeypatch.setattr(chain_passives, 'consume_passive_charge',
                        lambda player, flag: spent.append(flag) or True)
    g = _game(seed=93)
    _open_floor(g)
    boss = _spawn(g, 'imp', is_boss=True)
    g._refresh_fov()
    assert not spent, "the floor's command was spent on a demon it cannot hold"
    assert not any('compels' in t for t in _texts(g))
    # An ordinary demon in sight takes it.
    imp = _spawn(g, 'imp', dx=-2)
    g._refresh_fov()
    assert spent == ['demon_command_one_per_floor']
    assert imp.has_effect('charmed') and not boss.has_effect('charmed')
