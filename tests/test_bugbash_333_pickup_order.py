"""3.3.3 play (Brandon): a pile on one tile is picked up in a sensible order.

Gold, then treasure, potions, scrolls (and books), then identified things
lightest first, then unidentified things lightest first, then corpses; a chest
is opened where it stands, never carried, so it comes last. The tile's "You
see ... here" line names them in the same order, so the first named is the
next one taken (items.in_pickup_order, Game._pickup).
"""
import copy
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

import items  # noqa: E402


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import quiz_engine
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(4)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_pickup_order__')
    g.monsters = []
    g.state = STATE_PLAYER
    g.ground_items[:] = []
    g.player.STR = 30                         # carry it all
    return g


def _first(cls_name):
    return copy.copy(items.load_items(cls_name)[0])


def _pile(g):
    """A scrambled pile on the hero's tile, labelled for the assertions."""
    p = g.player
    heavy_unknown = items.instantiate_armor('plate', 'damascus_steel')
    heavy_unknown.id_level = 0
    light_known = items.instantiate_weapon('dagger', 'iron')
    light_known.id_level = 5
    heavy_known = items.instantiate_weapon('longsword', 'iron')
    heavy_known.id_level = 5
    corpse = items.Corpse('giant rat', 'giant_rat', p.x, p.y)
    pile = {
        'chest': _first('container'),
        'unknown': heavy_unknown,
        'heavy_known': heavy_known,
        'scroll': _first('scroll'),
        'potion': _first('potion'),
        'treasure': _first('treasure'),
        'light_known': light_known,
        'corpse': corpse,
    }
    for it in pile.values():
        it.x, it.y = p.x, p.y
        g.ground_items.append(it)
    items.add_gold_to_tile(g.ground_items, 50, p.x, p.y)
    gold = next(i for i in g.ground_items if isinstance(i, items.GoldPile))
    pile['gold'] = gold
    return pile


def test_the_rule_orders_a_pile():
    known = {}

    def is_known(it):
        return known.get(id(it), True)
    gold = items.GoldPile(10, 0, 0)
    scroll, potion = _first('scroll'), _first('potion')
    treasure = _first('treasure')
    heavy = items.instantiate_armor('plate', 'damascus_steel')
    light = items.instantiate_weapon('dagger', 'iron')
    unknown_light = items.instantiate_weapon('dagger', 'iron')
    known[id(unknown_light)] = False
    chest = _first('container')
    pile = [chest, unknown_light, heavy, scroll, light, potion, treasure]
    order = items.in_pickup_order(pile, is_known)
    assert order == [treasure, potion, scroll, light, heavy, unknown_light, chest]
    assert items.in_pickup_order([chest, gold, potion], is_known)[0] is gold


def test_pickup_takes_the_pile_in_order(game):
    pile = _pile(game)
    taken = []
    for _ in range(len(pile) + 2):
        before = list(game.ground_items)
        game._pickup()
        gone = [i for i in before if i not in game.ground_items]
        if not gone:
            break
        taken.append(next(k for k, v in pile.items() if v is gone[0]))
    want = ['gold', 'treasure', 'potion', 'scroll', 'light_known', 'heavy_known', 'unknown', 'corpse']
    assert taken == want
    assert pile['chest'] in game.ground_items          # opened where it stands


def test_the_tile_line_names_them_in_the_same_order(game):
    _pile(game)
    seen = []
    game.add_message = lambda text, kind='info', *a, **k: seen.append(str(text))
    game._notify_ground(game.player.x, game.player.y)
    line = next(t for t in seen if t.startswith('You see '))
    # Gold first, then the treasure: the next two a pickup takes.
    assert line.index('Gold') < line.index(game._display_name(_first('treasure')).split()[0])
    assert 'Gold' in line.split(':', 1)[1].split(',')[0]
