"""Bug bash 3.6.0, the lead's pass over the three merged sets of fixes.

Text that still said what the game does not do: the Detect Magic family's
descriptions, a dropped or readied stack's name, and the potion menus' turns
where the status cap cuts them short.

Headless: how it reads at the keys is Brandon's play-test.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import items  # noqa: E402
from spells import LEARNABLE_SPELLS  # noqa: E402

with open(os.path.join(ROOT, 'data', 'items', 'potion.json'), encoding='utf-8') as _f:
    LONG_POTIONS = sorted(k for k, v in json.load(_f).items()
                          if int(v.get('duration', 0) or 0) > 60)


@pytest.fixture
def g(monkeypatch):
    import main
    monkeypatch.setenv('PQ_NO_BONES', '1')
    random.seed(11)
    items.bind_unique_registry(set())
    game = main.Game(pygame.display.set_mode((1280, 720)), player_name='__bugbash_360_lead__')
    game.player.inventory = []
    game.player.status_effects.clear()
    game.said = []
    game.add_message = lambda text, *a, **k: game.said.append(str(text))
    return game


@pytest.mark.parametrize('sid', ['detect_magic_spell', 'identify_spell', 'omnisight_spell'])
def test_detect_magic_says_what_it_shows_in_plain_words(sid):
    desc = LEARNABLE_SPELLS[sid]['desc']
    assert 'BUC' not in desc and 'every magical item' not in desc
    assert desc.startswith('Shows blessed or cursed')
    if sid == 'omnisight_spell':
        assert 'every item on the floor' in desc      # ruling C15: not only the magical
    else:
        assert 'wands, scrolls and books' in desc
    assert len(desc) <= 92


@pytest.mark.parametrize('cat,iid', [('light', 'torch'), ('potion', 'potion_of_healing')])
def test_a_dropped_stack_is_named_as_the_pack_names_it(g, cat, iid):
    it = items.make_item_by_id(cat, iid)
    it.count = 5
    g.player.inventory.append(it)
    g._finish_drop(it, 4)
    line = next(t for t in g.said if t.startswith('You drop'))
    assert 'x4' in line and not line.endswith('s.'), line


def test_readying_a_bundle_names_one_kind_of_light(g):
    it = items.make_item_by_id('light', 'torch')
    it.count = 6
    g.player.inventory.append(it)
    g._ready_light(it)
    assert 'x6' not in g.said[-1], g.said[-1]
    assert it.count == 6


@pytest.mark.parametrize('pid', LONG_POTIONS)
def test_the_quaff_menu_shows_the_turns_a_drink_lays(g, pid, monkeypatch):
    import food_system
    pot = items.make_item_by_id('potion', pid)
    pot.buc, pot.cursed = 'uncursed', False
    shown = {}
    g.quaff_menu_items = [pot]
    monkeypatch.setattr(g, '_item_is_known', lambda _it: True, raising=False)
    monkeypatch.setattr(g, '_draw_fast_picker', lambda **k: shown.update(k), raising=False)
    g._quaff_mode = 'quaff'
    g._draw_quaff_menu()
    g.player.status_effects.clear()
    food_system.drink_potion(g.player, pot)
    laid = max(v for v in g.player.status_effects.values())
    assert f'({laid} turns)' in shown['entries'][0]['detail']
