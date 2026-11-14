"""Legendary items do not rust (round 3, 2026-11-14; Brandon's Q12):
"Legendary weapons don't need to rust, unless lore says so; they are
magical."

No unique or legendary piece (weapon, shield, armour, accessory) rusts,
whatever it is made of, unless its data says so with ``"rusts": true``
backed by its lore. Every rust path asks the one check
(status_effects._can_rust): the rust trap's water, the rust monster's
feelers, the Bloomleaf Cloak's ward and the card's "rusts".
"""
import json
import os
import random
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import gear  # noqa: E402
import items  # noqa: E402
import status_effects as se  # noqa: E402

_CATS = ('weapon', 'armor', 'shield', 'accessory', 'artifact')


def _named(cat, iid):
    return next(i for i in items.load_items(cat) if i.id == iid)


def _raw(cat):
    with open(os.path.join(ROOT, 'data', 'items', f'{cat}.json'), encoding='utf-8') as f:
        return json.load(f)


def _hero_wearing(weapon=None, body=None):
    from player import Player
    from items import ARMOR_SLOTS
    p = Player()
    p.weapon = weapon
    p.ranged_weapon = None
    p.shield = None
    p.armor_slots = [None] * len(ARMOR_SLOTS)
    if body is not None:
        p.armor_slots[ARMOR_SLOTS.index('body')] = body
    return p


def test_a_steel_unique_does_not_rust_and_a_plain_steel_longsword_still_does():
    zireael = _named('weapon', 'zireael')
    assert zireael.material == 'steel' and zireael.is_unique
    assert not se._can_rust(zireael)
    plain = items.instantiate_weapon('longsword', 'steel')
    assert not plain.is_unique and se._can_rust(plain)


def test_no_unique_rusts_but_those_whose_lore_says_so():
    lore_rusts = items.lore_rust_ids()
    for cat in _CATS:
        for it in items.load_items(cat):
            if not getattr(it, 'is_unique', False):
                continue
            assert se._can_rust(it) == (it.id in lore_rusts), (cat, it.id)


def test_every_rusts_field_is_backed_by_its_lore():
    """``"rusts": true`` is set only where the piece's own story speaks of
    its rust: Achilles's spear, whose rust healed King Telephus."""
    found = {}
    for cat in _CATS:
        for iid, d in _raw(cat).items():
            if isinstance(d, dict) and 'rusts' in d:
                assert d['rusts'] is True, (cat, iid)
                assert re.search(r'\brust', str(d.get('lore', '')), re.I), (cat, iid)
                found[iid] = cat
    assert found == {'achilles_spear': 'weapon'}
    assert se._can_rust(_named('weapon', 'achilles_spear'))


def test_the_cards_say_never_rusts_for_a_metal_legend():
    joan = _named('armor', 'breastplate_of_joan')       # "legendary", metal: rusted until now
    assert not se._can_rust(joan)
    assert 'never rusts' in gear.wear_words(joan)
    assert 'never rusts' in gear.weight_line(joan)
    plain = items.instantiate_armor('breastplate', 'chain_steel')
    assert 'rusts' in gear.wear_words(plain)


def test_the_rust_monster_and_the_trap_pass_over_a_steel_legend():
    zireael = _named('weapon', 'zireael')
    zireael.enchant_bonus = 2
    p = _hero_wearing(weapon=zireael)
    assert se.rust_worn_gear(p, None, rng=random.Random(1)) is None       # the trap's water
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = json.load(f)
    rm = Monster({**mons['rust_monster'], 'id': 'rust_monster'}, 1, 1)
    assert se.rust_worn_gear(p, rm, rng=random.Random(1)) is None         # its feelers
    assert zireael.enchant_bonus == 2


def test_beside_a_plain_blade_only_the_plain_blade_rusts():
    zireael = _named('weapon', 'zireael')
    zireael.enchant_bonus = 2
    plate = items.instantiate_armor('plate', 'chain_steel', level=6)
    p = _hero_wearing(weapon=zireael, body=plate)
    before = plate.enchant_bonus
    for seed in range(6):
        se.rust_worn_gear(p, None, rng=random.Random(seed))
    assert zireael.enchant_bonus == 2 and plate.enchant_bonus < before


def test_the_bloomleaf_ward_speaks_only_when_something_could_rust():
    """The ward asks the same check: over a legend alone there is nothing
    to keep the rust from, so it says nothing."""
    cloak = _named('armor', 'bloomleaf_cloak')
    from items import ARMOR_SLOTS
    p = _hero_wearing(weapon=_named('weapon', 'zireael'))
    p.armor_slots[ARMOR_SLOTS.index('cloak')] = cloak
    assert p.is_rustproof()
    assert se.rust_worn_gear(p, None) is None
    p.weapon = items.instantiate_weapon('longsword', 'steel')
    msg, kind = se.rust_worn_gear(p, None)
    assert kind == 'success' and 'keeps the rust' in msg
