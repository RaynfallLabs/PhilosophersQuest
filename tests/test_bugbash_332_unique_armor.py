"""Armour 5/7 (bug bash 3.3.2): the named armour and shields on the ladder.

tools/content/unique_armor_ladder_2026_11.py. Only body armour and shields
give AC: a named one's is its template's base plus its tier's plus. A named
minor piece gives none and carries one enchantment of its slot, chosen by
its lore, at its tier's greater level; its own name, card and powers stay.
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import enchantments  # noqa: E402
import gear  # noqa: E402
import guards  # noqa: E402
import items  # noqa: E402


def _raw(name):
    with open(os.path.join(ROOT, 'data', 'items', f'{name}.json'), encoding='utf-8') as f:
        return json.load(f)


ARMOR, SHIELD = _raw('armor'), _raw('shield')
BUILT = {a.id: a for a in items.load_items('armor')}


def test_the_pass_is_idempotent():
    import unique_armor_ladder_2026_11 as ua
    assert ua.main(['--check']) == 0


def test_every_named_minor_piece_carries_one_enchantment_of_its_slot():
    import unique_armor_ladder_2026_11 as ua
    for k, e in ARMOR.items():
        if e['slot'] not in gear.MINOR_SLOTS:
            continue
        if ua.PICKS[k][0] is None:
            # The Duck of Doom gives nothing (Brandon 2026-11-16).
            assert 'ench_id' not in e and e['ac_bonus'] == 0, k
            continue
        ench = enchantments.get(e.get('ench_id'))
        assert ench and ench['slot'] == e['slot'], k
        assert e['ench_id'] == ua.PICKS[k][0], k
        assert e['ench_level'] == 2 * e['tier'], k
        assert e['ac_bonus'] == 0 and e['enchant_bonus'] == 0, k
        for tb in (e.get('tier_bonuses') or {}).values():
            assert 'ac_bonus' not in tb and tb, k


def test_a_named_piece_keeps_its_name_card_and_powers():
    for k, e in ARMOR.items():
        if e['slot'] not in gear.MINOR_SLOTS:
            continue
        a = BUILT[k]
        assert a.name.lower() == e['name'].lower(), k        # (capitalised by naming.py)
        assert a.special == str(e.get('special', '') or ''), k
        if not e.get('ench_id'):
            continue                                         # the Duck of Doom: nothing
        assert a.ench_line.startswith(enchantments.get(e['ench_id'])['name']), k
    assert BUILT['blindfold'].on_equip_status == 'blinded'          # not replaced
    assert BUILT['greaves_of_hermes'].on_equip_status == 'hasted'   # folded into Speed
    assert BUILT['jarngreipr_gauntlets'].effects == {'stat': 'STR', 'amount': 5}
    assert BUILT['cloak_of_sun_wukong'].ench_id == 'displacement'


def test_a_starting_piece_built_from_the_data_has_its_enchantment():
    cap = items.make_item_by_id('armor', 'trainers_cap')
    assert cap.ench_id == 'the_eagle' and cap.effects == {'stat': 'PER', 'amount': 1}


def test_body_armour_and_shields_are_base_plus_tier():
    # ...their template's base, raised to the named-armour floor of their
    # depth (gear.named_ac_floor) when that base would leave them under it.
    import unique_armor_ladder_2026_11 as ua
    for cat, data, tpl_cat in (('armor', ARMOR, 'armor'), ('shield', SHIELD, 'shields')):
        kind = 'body' if cat == 'armor' else 'shield'
        for k, e in data.items():
            if not e.get('is_unique') or e.get('slot', 'shield') in gear.MINOR_SLOTS \
                    or e.get('equip_chain_mode'):
                continue
            tpl = items.get_template(tpl_cat, e['template_basis'])
            plus = min(gear.core_enchant_cap(), e['tier'])
            base = tpl['base_ac_value']
            if ua.found_by_depth(e, k):
                base = max(base, gear.named_ac_floor(kind, e['peak_floor']) - plus)
            assert e['ac_bonus'] == base, (cat, k)
            assert e['enchant_bonus'] == plus, (cat, k)
            lv = 2 * e['tier']
            assert e['equip_threshold'] == gear.equip_threshold(
                gear.weight_class(tpl), lv, unique=True), (cat, k)


def test_a_legend_found_by_depth_is_better_armour_than_the_commons_there():
    """Brandon, 2026-11-12: "full plate, uniques, etc. should all be driving
    better survivability later." Every named body armour and shield found by
    depth (a chain-equip one at its top tier) gives at least the common par
    of its peak floor plus a margin, and that floor climbs with depth."""
    import unique_armor_ladder_2026_11 as ua
    for cat, data in (('armor', ARMOR), ('shield', SHIELD)):
        kind = 'body' if cat == 'armor' else 'shield'
        for k, e in data.items():
            if not e.get('is_unique') or e.get('slot', 'shield') in gear.MINOR_SLOTS \
                    or not ua.found_by_depth(e, k):
                continue
            top = e['ac_bonus'] + e['enchant_bonus']
            assert top >= gear.named_ac_floor(kind, e['peak_floor']), (cat, k, top)
            tiers = e.get('tier_bonuses') or {}
            if tiers:
                assert max(int(t.get('ac_bonus', 0)) for t in tiers.values()) + e['enchant_bonus'] \
                    >= gear.named_ac_floor(kind, e['peak_floor']), (cat, k)
    t = gear.rules()['named_ac']
    for kind in ('body', 'shield'):
        par = t['par_' + kind]
        assert len(par) == 100 and all(b >= a for a, b in zip(par, par[1:])), kind
        assert gear.named_ac_floor(kind, 90) > gear.named_ac_floor(kind, 30), kind


def test_a_named_helm_guards_like_an_enchanted_one():
    class P:
        armor_slots = [None] * len(items.ARMOR_SLOTS)
    p = P()
    helm = BUILT['helm_of_achilles']                     # Iron Will V
    p.armor_slots = list(p.armor_slots)
    p.armor_slots[items.ARMOR_SLOTS.index('head')] = helm
    keep = guards.guard_keep(p, {'delivery': 'gaze', 'type': 'psionic', 'effect': 'feared'})
    base = guards.rules()['base_by_weight_class'][helm.weight_class]['rider']
    want = 1 - (base + enchantments.level_value(enchantments.get('iron_will'), 10))
    assert keep[1] == pytest.approx(max(1 - guards.rules()['cap']['rider'], want))


def test_guard_ladders_never_pass_the_cap():
    for k, v in enchantments.data()['enchantments'].items():
        if v.get('lane') == 'guard' and v.get('tiers'):
            assert enchantments.level_value(v, 10) <= enchantments.GUARD_CAP + 1e-9, k


def test_craft_lines_read_as_english():
    kneel = enchantments.get('the_kneeler')
    assert 'every 3rd prayer' in enchantments.describe(kneel, 9)
    assert 'every 6th prayer' in enchantments.describe(kneel, 1)
