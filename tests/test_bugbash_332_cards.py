"""Armour 7/7 (bug bash 3.3.2): the Kit, the character sheet and the
comparisons say what armour and rings do now.

Body armour and shields show their AC as base plus plus (the card showed
only the base); a helm, gloves or cloak shows what it guards and its
enchantment instead of "AC +0"; a ring kind shows its kind and tier.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import gear  # noqa: E402
import guards  # noqa: E402
import items  # noqa: E402
import main  # noqa: E402
from player import Player  # noqa: E402


class _Fake:
    """The real Game card helpers on a bare object."""
    def __init__(self, player):
        self.player = player
        self.messages = []

    def __getattr__(self, name):
        method = getattr(main.Game, name)
        return method.__get__(self, type(self)) if callable(method) else method

    def add_message(self, text, kind='info'):
        self.messages.append(text)

    def _item_is_known(self, item):
        return True

    def _kit_visible_level(self, item):
        return 5

    def _bare_name(self, item):
        return item.name


def _helm(ench='iron_will', level=5):
    return items.instantiate_armor('steel_helm', 'damascus_steel', level=level, ench_id=ench)


def test_a_body_armours_card_shows_base_plus_plus():
    plate = items.instantiate_armor('plate', 'damascus_steel', level=5)
    rows = dict(_Fake(Player())._kit_armour_rows(plate))
    assert rows['AC'] == f"+{plate.ac_bonus + plate.enchant_bonus}" and plate.enchant_bonus == 3
    assert gear.ac_value(plate) == plate.ac_bonus + plate.enchant_bonus


def test_a_helms_card_says_what_it_guards_and_its_enchantment_not_ac():
    rows = dict(_Fake(Player())._kit_armour_rows(_helm()))
    assert 'AC' not in rows
    assert rows['Guards'].startswith('Gazes and voices')
    assert rows['Enchant'] == 'Iron Will III'
    assert gear.ac_value(_helm()) == 0


def test_a_ring_kind_shows_its_kind_and_tier():
    r = items.make_item_by_id('accessory', 'ring_of_protection')
    r.relevel(6)
    f = _Fake(Player())
    assert dict(f._kit_armour_rows(r)) == {'Tier': 'III'}
    assert f._kit_accessory_effect(r) == 'Protection III'


def test_the_equip_delta_weighs_a_minor_piece_by_its_enchantment():
    p = Player()
    p.armor_slots[items.ARMOR_SLOTS.index('head')] = _helm('iron_will', 3)
    f = _Fake(p)
    assert 'lvl' in f._equip_delta_str(_helm('iron_will', 7))
    assert f._equip_delta_str(_helm('telepathy', 6)) == 'Greater Telepathy III'
    # Body armour: base plus plus on both sides.
    p.armor_slots[items.ARMOR_SLOTS.index('body')] = items.instantiate_armor('padded', 'linen', level=1)
    assert 'AC' in f._equip_delta_str(items.instantiate_armor('plate', 'damascus_steel', level=5))


def test_stepping_over_a_helm_names_both_enchantments():
    p = Player()
    p.armor_slots[items.ARMOR_SLOTS.index('head')] = _helm('iron_will', 3)
    f = _Fake(p)
    f._enchant_shown = lambda it: True
    f._show_item_comparison(_helm('telepathy', 6))
    assert f.messages and 'Greater Telepathy III' in f.messages[0] and 'Iron Will II' in f.messages[0]


def test_the_guard_line_reads_as_english():
    # Plain words (Brandon: "We speak english in this game").
    line = guards.guard_text(_helm())
    assert line.startswith('Guards against gazes, screams and other attacks on the mind: takes ')
    assert 'stops' in line and 'fear' in line
    for slot in ('head', 'hands', 'arms', 'legs', 'feet', 'cloak', 'shirt'):
        fam = guards.family(slot)
        assert fam['name'] and fam['long'] and fam['stops'], slot
        assert 'washes' not in fam['name'] and 'rider' not in fam['stops'], slot
    assert guards.guard_text(items.instantiate_armor('plate', 'damascus_steel')) == ''
