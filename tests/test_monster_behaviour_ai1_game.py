"""Monster behaviour, first wave (AI-1): the Game's side, on a real Game.

The behaviours are pure modules (tests/test_monster_behaviour_ai1.py);
these are the few things the Game does for them (game_behaviour.py): the
lines said as the hero sees or hears them, the burst of a dying creature
(and the one it kills, after it), the shove that moves the hero, the purse a
yielding bandit throws down, the summoned marked as the summoner's own, and
the help page that tells of them.
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

pygame.init()
_SCREEN = None

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=7):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name='__test_ai1__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _open_spot(g, half=4):
    from dungeon import FLOOR
    x = min(max(g.player.x, half + 1), g.dungeon.width - half - 2)
    y = min(max(g.player.y, half + 1), g.dungeon.height - half - 2)
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            g.dungeon.tiles[y + j][x + i] = FLOOR
    return x, y


def _monster(mid, x=0, y=0):
    from monster import Monster
    return Monster({**MONS[mid], 'id': mid}, x, y)


def _scene(*placed, seed=7):
    """A game with the hero in an open spot and ``placed`` = (kind, dx, dy)."""
    g = _game(seed)
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    g.monsters = [_monster(k, x + dx, y + dy) for k, dx, dy in placed]
    g._refresh_fov()
    g.visible |= {(x + i, y + j) for i in range(-4, 5) for j in range(-4, 5)}
    return g


def _messages(g, n=20):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def test_a_fire_beetle_bursts_on_the_hero_and_a_neighbour_bursts_after_it():
    # (a second fire beetle would shrug off the fire: a gas spore does not)
    g = _scene(('fire_beetle', 1, 0), ('gas_spore', 2, 0))
    first, second = g.monsters
    second.hp = 1
    hp0 = g.player.hp
    first.hp = 0
    first.alive = False
    g._on_monster_killed(first)
    assert g.player.hp < hp0
    assert not second.alive and second.__dict__.get('_throes_done')
    text = ' '.join(_messages(g))
    assert 'spray of fire' in text and 'blast catches you' in text


def test_a_banished_creature_does_not_burst():
    g = _scene(('fire_beetle', 1, 0))
    b = g.monsters[0]
    b._banished = True
    b.hp = 0
    b.alive = False
    hp0 = g.player.hp
    g._on_monster_killed(b)
    assert g.player.hp == hp0


def test_a_shove_throws_the_hero_one_tile_back():
    g = _scene(('hill_giant', -1, 0))
    x0, y0 = g.player.x, g.player.y
    g.player._pending_shove = {'from': (x0 - 1, y0), 'aim': False,
                               'line': 'Thrown!', 'aimed': 'Thrown hard!'}
    g._ai_resolve_shove()
    assert (g.player.x, g.player.y) == (x0 + 1, y0)
    assert 'Thrown!' in _messages(g)


def test_a_shove_never_throws_the_hero_into_water():
    from dungeon import WATER
    g = _scene(('hill_giant', -1, 0))
    x0, y0 = g.player.x, g.player.y
    for dy in (-1, 0, 1):
        g.dungeon.tiles[y0 + dy][x0 + 1] = WATER
    g.player._pending_shove = {'from': (x0 - 1, y0), 'aim': True, 'line': 'x', 'aimed': 'y'}
    g._ai_resolve_shove()
    assert (g.player.x, g.player.y) == (x0, y0)


def test_a_yielding_bandit_throws_down_his_purse_once():
    g = _scene(('bandit_thug', 1, 0))
    b = g.monsters[0]
    b.treasure = {'gold': [20, 20], 'item_chance': 0.0, 'item_tier': 1}
    import morale
    morale.give_up(b)
    g._ai_turn_after(b)
    assert b.treasure['gold'] == [0, 0]
    from items import GoldPile
    gold = sum(it.amount for it in g.ground_items
               if isinstance(it, GoldPile) and (it.x, it.y) == (b.x, b.y))
    assert gold == 20
    assert any('begs for' in t for t in _messages(g))


def test_lines_are_said_as_seen_or_heard():
    import ai_lines
    g = _scene(('kobold', 2, 0))
    k = g.monsters[0]
    ai_lines.say(k, 'The Kobold yaps a warning!', 'Somewhere ahead, a shrill yapping.')
    g._ai_turn_after(k)
    assert 'The Kobold yaps a warning!' in _messages(g)
    g.visible = set()
    ai_lines.say(k, 'The Kobold yaps a warning!', 'Somewhere ahead, a shrill yapping.')
    g._ai_turn_after(k)
    assert _messages(g)[-1] == 'Somewhere ahead, a shrill yapping.'


def test_a_summoners_minion_is_marked_his():
    g = _scene(('skeleton_necromancer', 3, 0))
    s = g.monsters[0]
    g._spawn_summoner_minion(s)
    minions = [m for m in g.monsters if m is not s]
    assert minions and all(m.__dict__.get('_summoned_by') is s for m in minions)


def test_the_monster_ways_help_page_draws():
    g = _game()
    g.screen = _screen()
    assert g.help_page_count() == 4
    assert g._help_page_title(3) == 'Monsters and Their Ways'
    g._help_page = 3
    g._draw_help_screen()
