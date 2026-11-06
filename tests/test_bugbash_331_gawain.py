"""Bug bash 3.3.1, equipment A6: the Ring of Gawain's tier 5 took Strength
for good.

Tier 5 carries passive_three_oclock. Malory's Gawain: his strength grew
every morning until noon, "and then ebbed away" (the ring's lore). The tick
in Game._refresh_fov took one point of STR every 30 turns (never below 8)
straight off the stat: never given back, not on rest (resting only reset the
counter, though the code said "resets on rest"), not when the ring came off,
and without the stamina that goes with a point of Strength.

Now the ebb is counted and comes back when the hero rests (the wait key) or
the ring is off. The rate and the floor of 8 are unchanged.

Real headless Game: the attune quiz callback, the per-turn tick and the
wait key are the game's own.
"""
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


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__bb331_gawain__', secret_build=None)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def _attune(g, item, tier):
    g.player.inventory.append(item)
    g._equip_accessory(item)
    cb, g.quiz_engine.callback = g.quiz_engine.callback, None
    cb(QuizResult(success=True, score=tier, correct=tier, asked=tier))
    assert item in g.player.accessory_slots


def _ebb(g, turns):
    for _ in range(turns):
        g._refresh_fov()


def test_tier_five_strength_ebbs_and_the_ring_coming_off_gives_it_back(game):
    p = game.player
    p.STR = 16
    ring = items.make_item_by_id('accessory', 'ring_of_gawain')
    _attune(game, ring, 5)
    worn_str, worn_sp = p.STR, p.max_sp
    _ebb(game, 90)
    assert p.STR == worn_str - 3                      # it ebbs, as the lore says
    assert p.max_sp == worn_sp - 3                    # a point of Strength is stamina too
    game._unequip_slot(f'accessory_{p.accessory_slots.index(ring)}', ring)
    _ebb(game, 1)
    assert (p.STR, p.max_sp) == (16, worn_sp - (worn_str - 16))   # nothing lost for good


def test_rest_gives_the_ebbed_strength_back(game):
    p = game.player
    p.STR = 16
    ring = items.make_item_by_id('accessory', 'ring_of_gawain')
    _attune(game, ring, 5)
    worn_str = p.STR
    _ebb(game, 60)
    assert p.STR == worn_str - 2
    assert p.recover_ebbed_strength() == 2
    assert p.STR == worn_str


def test_the_wait_key_is_the_rest(game):
    p = game.player
    p.STR = 16
    ring = items.make_item_by_id('accessory', 'ring_of_gawain')
    _attune(game, ring, 5)
    worn_str = p.STR
    _ebb(game, 60)
    assert p.STR == worn_str - 2
    game._player_input(pygame.K_PERIOD)                # wait a turn
    assert p.STR == worn_str
    assert any('strength comes back' in text.lower() for text, _k in game.msg_log.entries)


def test_the_ebb_never_goes_below_eight(game):
    p = game.player
    p.STR = 9
    ring = items.make_item_by_id('accessory', 'ring_of_gawain')
    _attune(game, ring, 5)
    _ebb(game, 30 * 20)
    assert p.STR == 8
