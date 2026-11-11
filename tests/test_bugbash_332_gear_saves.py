"""Armour 7/7 (bug bash 3.3.2): an old save meets the armour ladder.

src/gear_saves.py, run on load after the composite recompose: enchanted
common pieces keep their names, a pre-ladder minor piece gets its
enchantment, named pieces and rings take today's data, and what the hero
wears lends what it lends now. Running it twice changes nothing.
"""
import copy
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import gear_saves  # noqa: E402
import items  # noqa: E402
from player import Player  # noqa: E402


def _armour(iid):
    return items.make_item_by_id('armor', iid)


def _acc(iid):
    return items.make_item_by_id('accessory', iid)


def _wear_armour(p, piece):
    p.armor_slots[items.ARMOR_SLOTS.index(piece.slot)] = piece


def _migrate(p, extra=()):
    gear_saves.migrate(p, list(gear_saves._worn(p)) + list(p.inventory) + list(extra))


def test_an_old_named_helm_takes_its_enchantment_and_its_status():
    p = Player()
    helm = _armour('helm_of_hades')
    # As a pre-3.3.2 save held it: AC on the helm, no enchantment.
    helm.ac_bonus, helm.ench_id, helm.ench_level, helm.ench_line = 5, '', 0, ''
    helm.on_equip_status = ''
    _wear_armour(p, helm)
    _migrate(p)
    assert helm.ac_bonus == 0 and helm.ench_id == 'night_eyes' and helm.ench_level == 10
    assert helm.ench_line.startswith('Night Eyes V')
    assert p.has_effect('dark_vision')
    _migrate(p)                                                    # a second load
    assert helm.ench_id == 'night_eyes' and helm.name == _armour('helm_of_hades').name


def test_megingjord_loses_the_haste_it_no_longer_grants_and_keeps_its_strength():
    p = Player()
    belt = _acc('megingjord')
    belt.effects = {'stat': 'STR', 'amount': 6, 'status': 'hasted', 'duration': -1}
    p.inventory.append(belt)
    p._apply_equip(belt)
    assert p.has_effect('hasted')
    str_worn = p.STR
    _migrate(p)
    assert not p.has_effect('hasted')
    assert p.STR == str_worn and belt.effects == {'stat': 'STR', 'amount': 6}


def test_draupnir_gives_back_the_strength_it_no_longer_lends():
    p = Player()
    str0 = p.STR
    ring = _acc('draupnir')
    ring.effects = {'stat': 'STR', 'amount': 4, 'duration': -1}
    p.inventory.append(ring)
    p._apply_equip(ring)
    assert p.STR == str0 + 4
    _migrate(p)
    assert p.STR == str0 and not ring.effects


def test_a_pre_ladder_minor_piece_gets_one_enchantment_for_good():
    p = Player()
    helm = items.instantiate_armor('steel_helm', 'damascus_steel', level=4)
    assert not helm.ench_id
    p.inventory.append(helm)
    _migrate(p)
    first = (helm.ench_id, helm.name)
    assert helm.ench_id and helm.name.endswith(' II')
    _migrate(p)
    assert (helm.ench_id, helm.name) == first                       # same roll, no doubled name


def test_an_enchanted_common_keeps_its_name_after_the_recompose():
    p = Player()
    helm = items.instantiate_armor('steel_helm', 'damascus_steel', level=5, ench_id='iron_will')
    named = helm.name
    helm.name = named.rsplit(' of ', 1)[0]                        # what the recompose writes
    p.inventory.append(helm)
    _migrate(p)
    assert helm.name == named


def test_an_old_named_body_armour_is_base_plus_tier_and_keeps_a_higher_scroll_plus():
    p = Player()
    hide = _armour('hide_of_nemean_lion')
    fresh_plus = hide.enchant_bonus
    hide.ac_bonus, hide.enchant_bonus, hide.ench_level = 7, 0, 0  # pre-ladder
    p.inventory.append(hide)
    _migrate(p)
    assert hide.ac_bonus == 3 and hide.enchant_bonus == fresh_plus
    _migrate(p)
    assert hide.enchant_bonus == fresh_plus                         # idempotent
    shield = items.make_item_by_id('shield', 'pridwen')
    shield.enchant_bonus = 5                                        # scrolled to the cap
    p.inventory.append(shield)
    _migrate(p)
    assert shield.enchant_bonus == 5


def test_an_old_named_amulet_loses_its_ac():
    p = Player()
    pall = _acc('talisman_of_troy')
    pall.effects = dict(pall.effects, stat2='AC', amount2=2)
    pall.surrounded_ac_bonus = 2
    p.inventory.append(pall)
    _migrate(p)
    assert 'stat2' not in pall.effects and not hasattr(pall, 'surrounded_ac_bonus')
    assert pall.save_bonus == {'cat': 'all', 'amount': 2}


def test_the_load_runs_it(monkeypatch):
    import main
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    i = src.index('self._migrate_recompose_composite_items(state)\n')
    assert 'gear_saves.migrate(self.player, _all_items_in_save(self.player, state))' in src[i:i + 600]
    assert hasattr(main, '_all_items_in_save')
