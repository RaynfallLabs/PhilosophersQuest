"""Bug bash 3.3.1, equipment A3: the Tyet of Isis gave a life on every attune.

Its life-save comes from its tier bonuses (status_life_save from tier 2).
When the ward saved a life, the flat sources (the Amulet of Life Saving,
Excalibur) were spent on the item, but the Tyet's tier bonus was not: take
it off, attune again, and the life was back. Unlimited lives.

From tier 4 the Tyet renews the ward on every new floor
(passive_life_save_resets_per_floor); that stays.

Real headless Game: the attune quiz callback, the unequip, the killing blow
and the floor change are the game's own. A deep unique; not play-testable in
a sitting.
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
    g = Game(pygame.display.set_mode((1, 1)), player_name='__bb331_tyet__', secret_build=None)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def _attune(g, item, tier):
    """Put a chain-equip accessory on through the game's own attune quiz."""
    if item not in g.player.inventory:
        g.player.inventory.append(item)
    g._equip_accessory(item)
    cb, g.quiz_engine.callback = g.quiz_engine.callback, None
    cb(QuizResult(success=True, score=tier, correct=tier, asked=tier))
    assert g.player.amulet_slot is item


def _die(g):
    g.player.hp = 0
    g._answer_a_killing_blow()
    return g.player.hp > 0


def test_a_spent_tyet_gives_no_second_life_when_attuned_again(game):
    p = game.player
    tyet = items.make_item_by_id('accessory', 'tyet_of_isis')
    _attune(game, tyet, 2)
    assert p.has_effect('life_save')
    assert _die(game)                                   # the one life it gives
    assert not p.has_effect('life_save')
    for _ in range(3):
        game._unequip_slot('amulet', tyet)
        _attune(game, tyet, 2)
        assert not p.has_effect('life_save')
        assert not _die(game)                           # no second life
        p.hp = 10


def test_a_spent_tier_four_tyet_waits_for_a_new_floor(game):
    p = game.player
    tyet = items.make_item_by_id('accessory', 'tyet_of_isis')
    _attune(game, tyet, 4)
    assert _die(game)
    game._unequip_slot('amulet', tyet)
    _attune(game, tyet, 4)
    assert not p.has_effect('life_save')                # not again on this floor
    game._change_level(2, True)
    assert p.has_effect('life_save')                    # its floor renewal still works
    game._unequip_slot('amulet', tyet)
    _attune(game, tyet, 4)
    assert p.has_effect('life_save')                    # and attuning there keeps it
    assert _die(game)


def test_an_unspent_tyet_still_comes_off_with_its_ward(game):
    p = game.player
    tyet = items.make_item_by_id('accessory', 'tyet_of_isis')
    _attune(game, tyet, 2)
    game._unequip_slot('amulet', tyet)
    assert not p.has_effect('life_save')
    _attune(game, tyet, 2)
    assert p.has_effect('life_save')                    # never used: still there


def test_the_amulet_of_life_saving_stays_spent(game):
    """The flat life-saver was already right; kept that way."""
    p = game.player
    amu = items.make_item_by_id('accessory', 'amulet_life_saving')
    p.inventory.append(amu)
    p._apply_equip(amu)
    p.remove_from_inventory(amu)
    assert _die(game)
    game._unequip_slot('amulet', amu)
    p._apply_equip(amu)
    assert not p.has_effect('life_save')
    assert not _die(game)
