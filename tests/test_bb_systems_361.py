"""The 3.6.1 bug bash of the new systems and where they meet (bb-systems).

Each test is one finding (the findings file names them S01, S02...):

  S01  Hungry, Weak and Starving follow the belly whatever moved it
  S02  Weak's Strength is data/hunger.json weak_str
  S03  the venom still to come is what the ticks will really take
  S04  every dish's card says its heal; a lasting gift is not said as timed
"""
from __future__ import annotations

import copy
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PQ_NO_BONES', '1')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest  # noqa: E402

import hunger  # noqa: E402
import kitchen  # noqa: E402
import status_effects  # noqa: E402
import venom  # noqa: E402
from test_bugbash_360_monsters import _scene  # noqa: E402


@pytest.fixture(scope='module')
def game():
    return _scene()


def _hunger_statuses(p):
    return {k for k in hunger.ALL_STATUSES if p.status_effects.get(k)}


# ---------------------------------------------------------------------------
# S01, S02: hunger
# ---------------------------------------------------------------------------

def test_s01_a_full_belly_set_by_a_prayer_ends_starving_on_the_next_turn(game):
    g, p = game, game.player
    p.status_effects.clear()
    strength = p.STR
    p.sp = 0
    hunger.sync(p)
    assert _hunger_statuses(p) == {'starving', 'weak_from_hunger'}
    p.sp = p.max_sp                       # a prayer's or a wish's full SP, set straight in
    g._advance_turn()                     # a blow, a cast: no step, so no hunger tick
    assert _hunger_statuses(p) == set()
    assert p.STR == strength


def test_s01_a_belly_drained_straight_to_nothing_is_starving_at_once(game):
    g, p = game, game.player
    p.status_effects.clear()
    p.sp = p.max_sp
    hunger.sync(p)
    p.sp = 0                              # a famine demon's drain, an encounter's price
    g._advance_turn()
    assert 'starving' in _hunger_statuses(p)
    p.sp = p.max_sp
    g._advance_turn()


def test_s02_weak_takes_the_strength_its_data_names():
    want = int(hunger.rules()['weak_str'])
    assert status_effects.TIMED_STAT_GRANTS['weak_from_hunger'] == (('STR', want),)


# ---------------------------------------------------------------------------
# S03: the venom to come
# ---------------------------------------------------------------------------

def test_s03_the_venom_to_come_counts_armour_that_resists_poison(game):
    from items import ARMOR_SLOTS, make_item_by_id
    p = copy.deepcopy(game.player)
    p.max_hp = p.hp = 400
    p.status_effects.clear()
    p.armor_slots[ARMOR_SLOTS.index('body')] = make_item_by_id('armor', 'carapace_of_the_hydra')
    assert p.get_armor_resistance('poison') < 1.0
    p.status_effects['poisoned'] = 6
    venom.record(p).update(venom=20, dose=6)
    said = venom.to_come(p)
    hp = p.hp
    for _ in range(6):
        p.tick_effects()
    assert said == hp - p.hp


def test_s03_damage_after_changes_nothing_and_take_damage_still_lands():
    from player import Player
    p = Player()
    p.max_hp = p.hp = 100
    assert p.damage_after(30, 'fire') == 30 and p.hp == 100
    assert p.take_damage(30, 'fire') == 30 and p.hp == 70
    p.status_effects['invulnerable'] = 3
    assert p.damage_after(30) == 0 and p.take_damage(30) == 0 and p.hp == 70


# ---------------------------------------------------------------------------
# S04: the kitchen's cards
# ---------------------------------------------------------------------------

def _hurt(game):
    p = copy.deepcopy(game.player)
    p.status_effects.clear()
    p.max_hp, p.hp = 300, 60
    return p


def test_s04_every_dish_card_says_the_heal_the_meal_gives(game):
    """A dish of any tab heals (food is food); only the HP tab's card said so."""
    base = _hurt(game)
    for rec in kitchen.book():
        if kitchen.makes(rec) or kitchen.dish_tab(rec) == 'hp':
            continue
        p = copy.deepcopy(base)
        out = kitchen.dish_outcome(rec)
        want = kitchen.heal_amount(p, out)
        lines = kitchen.dish_effects(p, rec)
        sp_line = next(ln for ln in lines if ln.startswith('+') and ' SP' in ln)
        if want > 0:
            assert sp_line.endswith(f"SP, +{want} HP"), (rec["id"], lines)
        assert not any(ln.startswith('Also:') and ' HP' in ln for ln in lines), (rec['id'], lines)


def test_s04_a_power_this_meal_makes_lasting_is_not_said_as_timed(game):
    p = _hurt(game)
    rec = kitchen.recipe('feast_14')       # Serpent-King's Antidote Broth: its trophy's Poison Resist
    lines = kitchen.dish_effects(p, rec)
    assert 'poison_resist' in kitchen.made_lasting(p, rec)
    assert not any(ln.startswith('Poison Resist,') for ln in lines), lines
    msgs = kitchen.apply_dish(p, rec)
    assert p.status_effects.get('poison_resist') == -1
    assert not any('Poison Resist lingers' in m for m in msgs), msgs


def test_s04_a_side_this_meal_makes_lasting_is_not_said_as_timed(game):
    p = _hurt(game)
    rec = kitchen.recipe('feast_24')       # Flaming Sword Feast: a fire side, and Fire Resist for good
    assert 'fire_resist' in kitchen.made_lasting(p, rec)
    lines = kitchen.dish_effects(p, rec)
    assert not any('Fire Resist, ' in ln for ln in lines), lines
    msgs = kitchen.apply_dish(p, rec)
    assert p.status_effects.get('fire_resist') == -1
    assert not any('Fire Resist for' in m and 'turn' in m for m in msgs), msgs


def test_s04_a_big_sp_dish_does_not_promise_sustained_to_a_hero_already_sustained(game):
    p = _hurt(game)
    p.sp = 10
    rec = next(r for r in kitchen.book() if kitchen.dish_tab(r) == 'sp' and not kitchen.makes(r)
               and kitchen.dish_outcome(r)['sustained'] > 0)
    p.add_floor_effect('sustained', 1)     # Diogenes' lesson, for the floor
    lines = kitchen.dish_effects(p, rec)
    assert 'Sustained: already yours' in lines
    msgs = kitchen.apply_dish(p, rec)
    assert 'You are already Sustained.' in msgs
    assert p.status_effects['sustained'] == -1


# ---------------------------------------------------------------------------
# S08: the card says what this copy does
# ---------------------------------------------------------------------------

def _copy(cls, iid, buc):
    from items import make_item_by_id
    it = make_item_by_id(cls, iid)
    it.buc, it.id_level = buc, 5
    return it


@pytest.mark.parametrize('buc', ('blessed', 'cursed'))
def test_s08_a_kind_ring_says_the_level_it_works_at(game, monkeypatch, buc):
    import enchantments
    import rings
    it = _copy('accessory', 'amulet_life_saving', buc)
    kind = rings.kind_of(it)
    working = rings.describe(kind, enchantments.effective_level(it))
    own = rings.describe(kind, it.ench_level)
    assert working != own
    assert rings.life_saving_share(it) == rings.value(kind, enchantments.effective_level(it))
    monkeypatch.setattr(game, '_copy_buc_known', lambda item: True)
    assert working in game._item_power_lines(it) and own not in game._item_power_lines(it)
    monkeypatch.setattr(game, '_copy_buc_known', lambda item: False)
    assert own in game._item_power_lines(it)       # (an unknown curse is not given away)


def test_s08_a_stat_kind_lends_its_tier_whatever_its_blessing(game, monkeypatch):
    import rings
    it = _copy('accessory', 'amulet_of_wisdom', 'cursed')
    monkeypatch.setattr(game, '_copy_buc_known', lambda item: True)
    assert rings.card_text(it, True) == it.special


@pytest.mark.parametrize('buc', ('blessed', 'cursed'))
def test_s08_an_enchanted_piece_says_the_level_it_works_at(game, monkeypatch, buc):
    import enchantments
    it = _copy('armor', 'cloak_of_the_morrigan', buc)      # Displacement: a power, not a stat
    ench = enchantments.get(it.ench_id)
    working = enchantments.describe(ench, enchantments.working_level(it))
    assert working != enchantments.describe(ench, it.ench_level) or buc == 'blessed'
    monkeypatch.setattr(game, '_copy_buc_known', lambda item: True)
    assert any(working in ln for ln in game._item_power_lines(it))
