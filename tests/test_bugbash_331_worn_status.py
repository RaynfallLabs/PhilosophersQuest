"""Bug bash 3.3.1, equipment A5: taking one item off stripped a status that
other worn gear still grants.

Several paths popped the status outright: an attuned item's tier statuses
(chain_equip.revert_tier_bonuses), a weapon or amulet pushed out by a swap
(Player._apply_equip), Rand's Heart spent on death, an item handed to an NPC
(game_encounters), and the game-level helper, which only looked at rings and
amulets (so Greaves of Hermes did not count as a source of haste). Rand's
Heart took Warning away while a Ring of Warning was still on the hand.

Every path now asks one question, Player.drop_worn_status: does anything
else worn (or a trait, or a floor effect) still grant it?

Real headless Game for the game-level paths.
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
    g = Game(pygame.display.set_mode((1, 1)), player_name='__bb331_status__', secret_build=None)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def _wear(p, item):
    p.inventory.append(item)
    p._apply_equip(item)
    p.remove_from_inventory(item)


def _attune(g, item, tier):
    g.player.inventory.append(item)
    g._equip_accessory(item)
    cb, g.quiz_engine.callback = g.quiz_engine.callback, None
    cb(QuizResult(success=True, score=tier, correct=tier, asked=tier))


def _acc(i):
    return items.make_item_by_id('accessory', i)


def _ring_slot(p, item):
    return f'accessory_{p.accessory_slots.index(item)}'


# The common Rings of Warning and Haste left the rings in bug bash 3.3.2
# (armour plan 8): a warning ring is now a named one (Lynceus's Ring of Far
# Sight keeps it by lore), and haste comes from Boots of Speed.
WARNING_RING = 'ring_of_far_sight'


def _boots_of_speed():
    return items.instantiate_armor('leather_boots', 'leather', level=7, ench_id='speed')


def test_rands_heart_spent_leaves_the_ring_of_warning_its_warning(game):
    p = game.player
    _wear(p, _acc(WARNING_RING))
    _wear(p, _acc('rands_heart'))
    assert p.has_effect('warning')
    p.hp = 0
    assert not p.is_dead()
    assert p.amulet_slot is None                         # the Heart is spent
    assert p.has_effect('warning')                       # the ring still warns


def test_rands_heart_alone_takes_its_warning_with_it(game):
    p = game.player
    _wear(p, _acc('rands_heart'))
    p.hp = 0
    assert not p.is_dead()
    assert not p.has_effect('warning')


def test_boots_of_speed_off_leave_a_hasted_blades_haste(game):
    p = game.player
    blade = items.instantiate_weapon('longsword', 'iron')
    blade.on_equip_status = 'hasted'
    _wear(p, blade)
    boots = _boots_of_speed()
    assert boots.on_equip_status == 'hasted'
    _wear(p, boots)
    game._unequip_slot(boots.slot, boots)
    assert p.has_effect('hasted')


def test_an_attuned_tyet_off_leaves_another_source_of_life_save(game):
    """An attuned item's tier status (the Tyet of Isis's life at tier 2+;
    Gawain's haste left with the ring review, bug bash 3.3.2)."""
    p = game.player
    exc = next(w for w in items.load_items('weapon') if w.id == 'excalibur')
    _wear(p, exc)
    tyet = _acc('tyet_of_isis')
    _attune(game, tyet, 5)
    assert p.amulet_slot is tyet
    game._unequip_slot('amulet', tyet)
    assert p.has_effect('life_save')
    game._unequip_slot('weapon', exc)
    assert not p.has_effect('life_save')                 # the last source gone


def test_an_amulet_swap_leaves_a_ring_its_warning(game):
    p = game.player
    _wear(p, _acc(WARNING_RING))
    _wear(p, _acc('rands_heart'))
    _wear(p, _acc('amulet_of_wisdom'))                    # pushes the old amulet out
    assert p.has_effect('warning')


def test_a_weapon_swap_leaves_armour_its_status(game):
    p = game.player
    _wear(p, items.make_item_by_id('armor', 'greaves_of_hermes'))
    a = items.instantiate_weapon('longsword', 'iron')
    a.on_equip_status = 'hasted'
    _wear(p, a)
    _wear(p, items.instantiate_weapon('longsword', 'iron'))     # swaps a out
    assert p.has_effect('hasted')


def test_handing_a_worn_ring_to_someone_leaves_the_amulets_warning(game):
    p = game.player
    _wear(p, _acc('rands_heart'))
    _wear(p, _acc(WARNING_RING))
    assert game._npc_remove_item_by_id(WARNING_RING)
    assert p.has_effect('warning')
    assert game._npc_remove_item_by_id('rands_heart')
    assert not p.has_effect('warning')


def test_a_spent_tyet_does_not_keep_excaliburs_ward_alive(game):
    """A spent life-save stays listed on the Tyet (so it comes off with it)
    but no longer counts as granted: taking Excalibur off must take its
    ward, or equip / unequip / die would be a free life every time."""
    p = game.player
    tyet = _acc('tyet_of_isis')
    _attune(game, tyet, 2)
    p.hp = 0
    game._answer_a_killing_blow()
    assert p.hp == 1 and not p.has_effect('life_save')
    exc = next(w for w in items.load_items('weapon') if w.id == 'excalibur')
    assert exc.on_equip_status == 'life_save'
    _wear(p, exc)
    assert p.has_effect('life_save')
    game._unequip_slot('weapon', exc)
    assert not p.has_effect('life_save')


def test_a_trait_status_survives_its_item(game):
    """A status the hero has from a trait is his own (kept as before)."""
    p = game.player
    p.quirk_progress.setdefault('quirk_statuses', []).append('warning')
    ring = _acc(WARNING_RING)
    _wear(p, ring)
    game._unequip_slot(_ring_slot(p, ring), ring)
    assert p.status_effects.get('warning') == -1
