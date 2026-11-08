"""Bug bash 3.3.1, fountains and thrones: a longer chain never gives less.

Both are escalator chains to 5. The fountain's chain 5 gave a stat and full
health but not chain 4's full stamina and cure; the throne's rewards were a
menu, one per chain, so once the run's fortune stats were spent chain 5
gave only a heal while chain 4 gave +5-15 max HP, and chain 4 gave no gold,
heal or insight. Each chain now gives at least everything the chain below
it does. (Thrones and fountains are rare room features: logic tests.)
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


@pytest.fixture(autouse=True)
def _no_saves(monkeypatch, tmp_path):
    import save_system
    import bones
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    yield


def _game():
    import items
    from main import Game
    items.bind_unique_registry(set())
    return Game(pygame.display.set_mode((1, 1)), player_name='__bb331_ft__')


def _gains(kind: str, chain: int, fortune_spent: bool, seed: int) -> set:
    """What one sit or drink at ``chain`` gave, by kind of gain."""
    import items
    random.seed(seed)
    g = _game()
    p = g.player
    p.max_hp = 60
    p.hp = 10
    p.sp = 1
    p.status_effects['poisoned'] = 9
    if fortune_spent:
        p.fortune_stat_gained = 10 ** 6
    ring = copy.copy(next(a for a in items.load_items('accessory')
                          if not getattr(a, 'is_unique', False) and hasattr(a, 'id_level')))
    ring.identified = False
    p.inventory.append(ring)
    before = dict(hp=p.hp, sp=p.sp, max_hp=p.max_hp, gold=int(g.player_gold),
                  stats=sum(int(getattr(p, s)) for s in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')))
    (g._resolve_fountain if kind == 'fountain' else g._resolve_throne)(chain)
    out = set()
    if p.hp > before['hp']:
        out.add('heal')
    if p.hp >= p.max_hp:
        out.add('full health')
    if p.sp > before['sp']:
        out.add('stamina')
    if p.sp >= p.max_sp:
        out.add('full stamina')
    if 'poisoned' not in p.status_effects:
        out.add('cure')
    if p.max_hp > before['max_hp']:
        out.add('max hp')
    if int(g.player_gold) > before['gold']:
        out.add('gold')
    if not g._needs_identify(ring):
        out.add('insight')
    if sum(int(getattr(p, s)) for s in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')) > before['stats']:
        out.add('stat')
    return out


@pytest.mark.parametrize('kind', ['fountain', 'throne'])
@pytest.mark.parametrize('fortune_spent', [False, True])
def test_each_chain_gives_everything_the_chain_below_gives(kind, fortune_spent):
    for chain in range(1, 5):
        for seed in range(3):
            lower = _gains(kind, chain, fortune_spent, seed)
            higher = _gains(kind, chain + 1, fortune_spent, seed)
            missing = lower - higher
            assert not missing, f"{kind} chain {chain + 1} lacks {missing} that chain {chain} gives"


# ---------------------------------------------------------------- bug bash 3.3.2
def _on_fountain(g):
    from dungeon import FOUNTAIN, FLOOR
    d = g.dungeon
    x, y = g.player.x, g.player.y
    d.tiles[y][x] = FOUNTAIN
    return x, y, FOUNTAIN, FLOOR


def test_a_fountain_gives_one_drink():
    """Brandon, 2026-11-07: "Fountains seem to allow TWO drinks... but really
    should just be one chance." It dried up one time in three."""
    from game_states import STATE_QUIZ
    for seed in range(6):
        random.seed(seed)
        g = _game()
        x, y, FOUNTAIN, FLOOR = _on_fountain(g)
        g.dungeon.ariadne_shrine_door = None
        g._resolve_fountain(2)
        assert g.dungeon.tiles[y][x] == FLOOR, seed          # always dry after a drink
        g.dungeon.tiles[y][x] = FOUNTAIN                     # even put back by hand,
        g.state = 'player'
        g._drink_fountain()                                  # it will not pour again
        assert g.state != STATE_QUIZ, seed


def test_ariadnes_fountain_keeps_its_basin_but_not_a_second_drink():
    from game_states import STATE_QUIZ
    random.seed(1)
    g = _game()
    x, y, FOUNTAIN, FLOOR = _on_fountain(g)
    g.dungeon.ariadne_fountain_pos = (x, y)
    g.dungeon.ariadne_shrine_door = (x + 5, y)               # still sealed
    g._resolve_fountain(1)
    assert g.dungeon.tiles[y][x] == FOUNTAIN                 # the Bull can still be offered
    g.state = 'player'
    g._drink_fountain()
    assert g.state != STATE_QUIZ


def test_another_fountain_on_ariadnes_floor_still_dries():
    random.seed(4)
    g = _game()
    x, y, FOUNTAIN, FLOOR = _on_fountain(g)
    g.dungeon.ariadne_fountain_pos = (x + 9, y + 9)
    g.dungeon.ariadne_shrine_door = (x + 5, y)
    g._resolve_fountain(1)
    assert g.dungeon.tiles[y][x] == FLOOR
