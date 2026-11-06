"""Bug bash 3.3.1, floor changes: what a stair gives back.

Arrival effects that are spent "once a floor" (the Anklet of Atalanta's
freeze, the Heart of Ahriman's double-damage charge, the Cloak of Odin's
ravens) fired on every crossing of a staircase, so one stair walked up and
down was an endless freeze and an endless scouting flight. They belong to a
floor reached for the first time, as every held charge in _change_level does.
"""
import os
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


def _game(name='__bb331_floors__'):
    from main import Game
    import items
    items.bind_unique_registry(set())
    screen = pygame.display.set_mode((1, 1))
    return Game(screen, player_name=name)


def _said(g):
    out = []
    real = g.add_message

    def add(text, kind='info'):
        out.append(str(text))
        return real(text, kind)
    g.add_message = add
    return out


_ARRIVAL = {
    'atalantas_choice': "Atalanta's choice",
    'anti_being': 'Heart of Ahriman trembles',
    'huginn_muninn': 'Huginn and Muninn take flight',
}


@pytest.mark.parametrize('flag', sorted(_ARRIVAL))
def test_arrival_passive_fires_on_new_depth_only(monkeypatch, flag):
    import chain_passives
    real = chain_passives.player_has_passive
    monkeypatch.setattr(chain_passives, 'player_has_passive',
                        lambda p, f: f == flag or real(p, f))
    g = _game()
    said = _said(g)

    def low_hp():
        g.player.hp = max(1, int(g.player.max_hp * 0.2))
        g.player._anti_being_charged = False

    def fired():
        n = sum(1 for s in said if _ARRIVAL[flag] in s)
        said.clear()
        return n

    low_hp()
    g._change_level(2, True)                 # new depth: it fires
    assert fired() == 1
    for lv, down in ((1, False), (2, True), (1, False), (2, True)):
        low_hp()
        g._change_level(lv, down)            # floors already walked
        assert fired() == 0, f"{flag} fired again on a revisit of floor {lv}"
        if flag == 'anti_being':
            assert not g.player._anti_being_charged
        if flag == 'huginn_muninn':
            assert g.player._huginn_muninn_remaining == 0
    low_hp()
    g._change_level(3, True)                 # new depth again: it fires again
    assert fired() == 1


def test_sharur_floor_start_reveal_is_a_first_arrival_only():
    """Sharur's floor-start glimpse rerolled (and mapped more) on every
    stair crossing."""
    g = _game()
    said = _said(g)

    class _Blade:
        floor_start_reveal_chance = 1.0
    g.player.weapon = _Blade()
    g._change_level(2, True)
    assert sum('Sharur whispers' in s for s in said) == 1
    said.clear()
    g._change_level(1, False)
    g._change_level(2, True)
    assert sum('Sharur whispers' in s for s in said) == 0


def test_ring_of_solomon_rolls_each_demon_once(monkeypatch):
    """Pacify-on-sight kept its 'already rolled' set on the Game and wiped it
    on every stair: each revisit put every demon back to sleep."""
    import json
    import chain_passives
    from monster import Monster
    monkeypatch.setattr(chain_passives, 'get_pacify_demon_chance', lambda p: 1.0)
    g = _game()
    g._change_level(2, True)
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        defs = json.load(f)
    p = g.player
    spot = next((x, y) for x, y in ((p.x + 1, p.y), (p.x - 1, p.y), (p.x, p.y + 1), (p.x, p.y - 1))
                if g.dungeon.is_walkable(x, y))
    demon = Monster({**defs['greater_demon'], 'id': 'greater_demon'}, *spot)
    g.monsters.append(demon)
    g._refresh_fov()
    assert demon.status_effects.get('sleeping', 0) > 0      # the first sight rolls
    demon.status_effects.pop('sleeping', None)
    g._change_level(1, False)
    g._change_level(2, True)
    back = next(m for m in g.monsters
                if m.kind == 'greater_demon' and (m.x, m.y) == spot)
    assert back.status_effects.get('sleeping', 0) == 0      # no second roll on return
    g._refresh_fov()
    assert back.status_effects.get('sleeping', 0) == 0
