"""Bug bash 3.3.1, equipment A4: a two-handed weapon pushed the shield off
without its teardown.

Player._apply_equip moved the worn shield to the pack and emptied the slot,
but never ran shed_worn_grants: an attuned shield's tier bonuses (its
resistances, its passives) stayed on the hero, and attuning it again added
them a second time. The Aegis of Athena's magic resistance went 2, 4, 6.

Real headless Game: the attune quiz callback and the weapon equip are the
game's own.
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
    g = Game(pygame.display.set_mode((1, 1)), player_name='__bb331_2h__', secret_build=None)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def _attune_shield(g, shield, tier=5):
    if shield not in g.player.inventory:
        g.player.inventory.append(shield)
    g._equip_item(shield)
    cb, g.quiz_engine.callback = g.quiz_engine.callback, None
    cb(QuizResult(success=True, score=tier, correct=tier, asked=tier))
    assert g.player.shield is shield


def _wield(g, weapon):
    g.player.inventory.append(weapon)
    g._equip_item(weapon)
    assert g.player.weapon is weapon


def test_a_two_hander_takes_the_attuned_shield_off_with_its_bonuses(game):
    p = game.player
    aegis = items.make_item_by_id('shield', 'aegis_of_athena')
    base_magic = p.damage_resistances.get('magic', 0)
    _attune_shield(game, aegis)
    assert p.damage_resistances.get('magic', 0) == base_magic + 2
    _wield(game, items.instantiate_weapon('greatsword', 'iron'))
    assert p.shield is None and aegis in p.inventory
    assert p.damage_resistances.get('magic', 0) == base_magic
    assert not (getattr(aegis, '_chain_passives', None) or {})
    assert int(getattr(aegis, 'achieved_tier', 0) or 0) == 0


def test_attuning_the_shield_again_after_a_two_hander_does_not_stack(game):
    p = game.player
    aegis = items.make_item_by_id('shield', 'aegis_of_athena')
    base = dict(p.damage_resistances)
    for _ in range(3):
        _attune_shield(game, aegis)
        assert p.damage_resistances.get('magic', 0) == base.get('magic', 0) + 2
        assert p.damage_resistances.get('fear', 0) == base.get('fear', 0) + 2
        _wield(game, items.instantiate_weapon('greatsword', 'iron'))
        game._unequip_slot('weapon', p.weapon)
    assert p.damage_resistances == base


def test_a_shield_status_comes_off_when_a_two_hander_pushes_it_out(game):
    """A shield's on-equip status goes the same way (shed_worn_grants). No
    shield in the data has one today; the path is the one armour uses."""
    p = game.player
    sh = items.instantiate_shield('buckler', 'iron')
    sh.on_equip_status = 'fire_resist'
    p.inventory.append(sh)
    p._apply_equip(sh)
    p.remove_from_inventory(sh)
    assert p.has_effect('fire_resist')
    _wield(game, items.instantiate_weapon('greatsword', 'iron'))
    assert not p.has_effect('fire_resist')
