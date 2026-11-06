"""Bug bash 3.3.1, equipment A6: the Ring of Gawain's tier 5.

Tier 5 carries passive_three_oclock. Malory's Gawain: his strength grew
every morning from nine until noon, "and then ebbed away" (the ring's lore).
The tick in Game._refresh_fov took one point of STR every 30 turns (never
below 8) straight off the stat, for good and without its stamina, so tier 5
(+3 STR) was weaker than tier 4 (+5).

Ruling (Brandon, 2026-11-06, "rested surge"): a rest (the wait key) raises
the hero 3 Strength above the ring's own; it ebbs a point every 30 turns
back to the ring's base, never below. Taking the ring off ends the surge.

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


def test_a_rest_raises_the_surge_and_it_ebbs_back_to_base_never_below(game):
    p = game.player
    p.STR = 16
    ring = items.make_item_by_id('accessory', 'ring_of_gawain')
    _attune(game, ring, 5)
    base, base_sp = p.STR, p.max_sp
    _ebb(game, 90)
    assert p.STR == base                              # no surge yet: nothing ebbs
    game._player_input(pygame.K_PERIOD)                # rest
    assert (p.STR, p.max_sp) == (base + 3, base_sp + 3)
    assert any("gawain's strength rises" in text.lower() for text, _k in game.msg_log.entries)
    _ebb(game, 30)
    assert p.STR == base + 2
    _ebb(game, 30 * 10)
    assert (p.STR, p.max_sp) == (base, base_sp)       # back to the ring's own, never below


def test_tier_five_at_its_peak_beats_tier_four(game):
    p = game.player
    p.STR = 16
    ring = items.make_item_by_id('accessory', 'ring_of_gawain')
    _attune(game, ring, 5)
    game._player_input(pygame.K_PERIOD)
    t5 = p.STR
    g4 = items.make_item_by_id('accessory', 'ring_of_gawain')
    assert t5 - 16 > int(g4.tier_bonuses['4']['stat_bonus_STR'])


def test_the_ring_coming_off_ends_the_surge(game):
    p = game.player
    p.STR = 16
    ring = items.make_item_by_id('accessory', 'ring_of_gawain')
    _attune(game, ring, 5)
    game._player_input(pygame.K_PERIOD)
    game._unequip_slot(f'accessory_{p.accessory_slots.index(ring)}', ring)
    _ebb(game, 1)
    assert p.STR == 16
    assert getattr(p, '_gawain_surge', 0) == 0


def test_a_rest_without_the_ring_gives_nothing(game):
    p = game.player
    p.STR = 16
    game._player_input(pygame.K_PERIOD)
    assert p.STR == 16


def test_an_old_saves_ebbed_strength_comes_back(game):
    p = game.player
    p.STR = 13
    p._three_oclock_lost = 3                          # taken by the old ebb
    _ebb(game, 1)                                      # no ring worn
    assert p.STR == 16
    assert p._three_oclock_lost == 0
