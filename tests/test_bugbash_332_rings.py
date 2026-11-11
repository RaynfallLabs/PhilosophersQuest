"""Armour 4/7 (bug bash 3.3.2): rings and amulets after the armour redesign.

docs/design/ARMOR_REDESIGN_PLAN.md section 8, data/ring_kinds.json,
src/rings.py, tools/content/ring_kinds_2026_11.py. The 89 common rings and
amulets are ten kinds, each tiered I-V by the level it is found at; no ring
gives AC; the powers armour now owns left the rings; the named ones keep a
moved power only where their lore makes it their own.
"""
import copy
import json
import os
import random
import statistics
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import gear  # noqa: E402
import guards  # noqa: E402
import items  # noqa: E402
import rings  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'items', 'accessory.json'), encoding='utf-8') as _f:
    RAW = json.load(_f)
ACCS = {a.id: a for a in items.load_items('accessory')}
LEFT_THE_RINGS = {'telepathy', 'truesight', 'dark_vision', 'warning', 'searching', 'hasted',
                  'levitating', 'displacement', 'fire_resist', 'cold_resist', 'shock_resist',
                  'poison_resist', 'sleep_resist', 'drain_resist', 'clairvoyant',
                  'magic_resist', 'reflecting'}


def _ring(kind_id, level, buc='uncursed'):
    tpl = next(a for a in ACCS.values() if getattr(a, 'kind', '') == kind_id)
    r = copy.copy(tpl)
    rings.relevel(r, level)
    r.buc = buc
    return r


def _named(e, k):
    return e.get('is_unique') or e.get('plot_locked') or k in ('ouroboros_pendant', 'ankh_of_ra')


# ---------------------------------------------------------------- the data

def test_ten_kinds_one_entry_each():
    kinds = rings.kinds()
    assert set(kinds) == {'protection', 'spell_turning', 'regeneration', 'invisibility',
                          'sustenance', 'wizardry', 'life_saving', 'wisdom', 'intellect',
                          'constitution'}
    by_kind = {}
    for k, e in RAW.items():
        if e.get('kind'):
            assert e['kind'] not in by_kind, e['kind']
            by_kind[e['kind']] = k
            assert e['slot'] == kinds[e['kind']]['slot'], k
    assert set(by_kind) == set(kinds)


def test_the_commons_are_kinds_and_curses_only():
    """Every random-loot ring or amulet is a kind or a cursed trap: the
    powers armour owns and every AC ring left."""
    for k, e in RAW.items():
        if _named(e, k) or e.get('slot') not in ('ring', 'amulet') or not items.is_random_loot(ACCS[k]):
            continue
        fx = e.get('effects') or {}
        assert e.get('kind') or k.startswith(('ring_curse_', 'amulet_curse_')), k
        assert fx.get('stat') not in ('AC', 'STR', 'DEX', 'PER'), k
        assert fx.get('status') not in LEFT_THE_RINGS, k


def test_no_ring_or_amulet_gives_ac():
    for k, e in RAW.items():
        fx = e.get('effects') or {}
        assert 'ac_bonus' not in e and 'surrounded_ac_bonus' not in e, k
        assert fx.get('stat') != 'AC' and fx.get('stat2') != 'AC', k


def test_the_model_ladders():
    """Protection and Spell Turning are the armour model's (section 8)."""
    assert rings.get('protection')['tiers'] == [0.16, 0.19, 0.24, 0.28, 0.28]
    assert rings.get('spell_turning')['tiers'] == [0.30, 0.46, 0.52, 0.52, 0.52]
    for kid, kind in rings.kinds().items():
        if not kind.get('tiers'):
            continue
        vals = [rings.value(kind, lv) for lv in range(rings.first_level(kind), 11)]
        assert vals == sorted(vals, reverse=kid == 'invisibility'), kid


def test_the_pass_is_idempotent():
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))
    import ring_kinds_2026_11 as rk
    assert rk.main(['--check']) == 0


# ------------------------------------------------------------ a found ring

def test_a_ring_found_deeper_is_stronger():
    rng = random.Random(7)
    tiers = {}
    for f in (5, 45, 90):
        ts = []
        for _ in range(300):
            r = copy.copy(ACCS['ring_of_protection'])
            import dungeon
            dungeon.dress_spawn(r, f, rng, buc=False)
            ts.append(r.quiz_tier)
            assert 1 <= r.ench_level <= 10 and r.quiz_tier == gear.tier_for_level(r.ench_level)
            assert r.equip_threshold == gear.accessory_threshold('ring', r.ench_level)
        tiers[f] = statistics.mean(ts)
    assert tiers[5] < tiers[45] < tiers[90]
    assert tiers[5] < 1.5 and tiers[90] > 4.0


def test_relevel_names_and_grants():
    a = _ring('wisdom', 6)
    assert a.name == 'Amulet of Greater Wisdom III'
    assert a.effects == {'stat': 'WIS', 'amount': 3}
    assert a.quiz_tier == 3 and a.equip_threshold == gear.accessory_threshold('amulet', 6)
    r = _ring('protection', 3)
    assert r.name == 'Ring of Protection II' and '19%' in r.special
    # Life Saving is only ever made from tier III.
    assert _ring('life_saving', 1).ench_level == 5
    # Every level of a kind is one learned type.
    assert items.type_class(_ring('protection', 1)) == items.type_class(r) == 'ring_of_protection'
    assert items.form_id(_ring('protection', 9)) == 'ring_of_protection'


def test_a_template_made_without_a_roll_is_its_first_level():
    a = items.make_item_by_id('accessory', 'amulet_of_intellect')
    assert a.ench_level == 1 and a.effects == {'stat': 'INT', 'amount': 1}


def test_thresholds_follow_slot_and_tier():
    for kid in rings.kinds():
        for lv in range(rings.first_level(rings.get(kid)), 11):
            r = _ring(kid, lv)
            slot = rings.get(kid)['slot']
            lo, hi = (1, 3) if slot == 'ring' else (2, 4)
            assert lo <= r.equip_threshold <= hi, (kid, lv)


# ------------------------------------------------------------------ in play

def _hero(*worn):
    p = Player()
    for r in worn:
        if r.slot == 'amulet':
            p.amulet_slot = r
        else:
            p.accessory_slots[p.accessory_slots.index(None)] = r
    return p


def test_protection_is_a_saving_throw_and_two_do_not_add():
    rider = {'delivery': 'bite', 'type': 'physical', 'effect': 'poisoned'}
    base = guards.guard_keep(_hero(), rider)[1]
    one = guards.guard_keep(_hero(_ring('protection', 5)), rider)
    two = guards.guard_keep(_hero(_ring('protection', 5), _ring('protection', 1)), rider)
    assert base == 1.0
    assert one[1] == pytest.approx(1 - 0.24) and one[2] is not None
    assert two[1] == pytest.approx(one[1])                 # the stronger counts
    # It saves; it does not turn the blow.
    assert one[0] == 1.0


def test_spell_turning_turns_magic_not_steel():
    p = _hero(_ring('spell_turning', 3))
    assert guards.guard_keep(p, {'delivery': 'gaze', 'type': 'psionic'})[0] == pytest.approx(1 - 0.46)
    assert guards.guard_keep(p, {'delivery': 'blow', 'type': 'physical'})[0] == 1.0


def test_no_ring_moves_ac_blessed_works_a_level_higher():
    ac = Player().get_ac()
    vals = {}
    for buc in ('cursed', 'uncursed', 'blessed'):
        p = _hero(_ring('protection', 5, buc))
        assert p.get_ac() == ac
        vals[buc] = rings.best(p, 'protection')[1]
    assert vals['cursed'] < vals['uncursed'] < vals['blessed']


def test_the_body_and_mind_kinds():
    p = _hero(_ring('regeneration', 9), _ring('sustenance', 9))
    assert rings.regen_share(p) == pytest.approx(0.01)
    assert rings.hunger_interval(p, 2) == 8                 # three quarters slower
    assert rings.hunger_interval(Player(), 2) == 2
    w = _hero(_ring('wizardry', 9))
    assert rings.spell_cost(w, 20) == 14 and rings.spell_cost(w, 1) == 1
    assert rings.life_saving_share(_ring('life_saving', 9)) == pytest.approx(0.75)
    assert rings.life_saving_share(ACCS['tyet_of_isis']) == 0.0


def test_the_veil_slips_when_you_strike():
    p = _hero(_ring('invisibility', 9))                    # tier V: 2 quiet turns
    assert rings.veil_turns(p) == 2
    assert rings.tick(p) == '' and not p.has_effect('invisible')
    assert rings.tick(p) and p.has_effect('invisible')
    assert rings.on_strike(p) and not p.has_effect('invisible')
    # The turn of the strike is not a quiet one (3.3.3 lore audit): then
    # two quiet turns, as the ring says.
    assert rings.tick(p) == ''
    assert rings.tick(p) == ''
    assert rings.tick(p) and p.has_effect('invisible')
    # Off the hand, the veil goes with it.
    p.accessory_slots[0] = None
    rings.tick(p)
    assert not p.has_effect('invisible')


def test_a_potions_invisibility_does_not_slip():
    p = _hero(_ring('invisibility', 3))
    p.status_effects['invisible'] = 40
    assert rings.on_strike(p) == ''
    assert p.status_effects['invisible'] == 40


# ------------------------------------------------------------------ uniques

def test_named_items_keep_their_lore_powers_only():
    fx = lambda k: RAW[k].get('effects') or {}  # noqa: E731
    assert fx('megingjord') == {'stat': 'STR', 'amount': 6}          # strength kept, haste gone
    assert 'stat' not in fx('draupnir') and RAW['draupnir']['gold_multiplier'] == 2.0
    assert fx('ring_of_gyges')['status'] == 'invisible'
    assert fx('dragonslayer_ring') == {'status': 'fire_resist', 'duration': -1}
    assert RAW['talisman_of_troy']['save_bonus'] == {'cat': 'all', 'amount': 2}
    for tb in RAW['ring_of_gawain']['tier_bonuses'].values():
        assert 'status_hasted' not in tb
    for tb in RAW['kavacha_kundala']['tier_bonuses'].values():
        assert 'status_fire_resist' not in tb and 'resistance_fire' not in tb


def test_named_tiers_and_thresholds_follow_the_rule():
    for k, e in RAW.items():
        if not _named(e, k) or e.get('slot') == 'none':
            continue
        t = e['quiz_tier']
        fx = e.get('effects') or {}
        amt = max([abs(int(fx.get(a, 0) or 0)) for a in ('amount', 'amount2')] + [1])
        assert t >= min(5, amt), k                      # never under its own stat
        assert e['equip_threshold'] == gear.accessory_threshold(
            e['slot'], gear.level_for_tier(t), unique=True), k


# ------------------------------------------------------------ wiring, saves

def test_an_old_save_ring_heals_into_its_kind_at_its_strength():
    from main import Game
    old = items.Accessory({'id': 'ring_protection_gold', 'name': 'gold ring of protection',
                           'symbol': '=', 'color': [200, 200, 200], 'weight': 0.1,
                           'slot': 'ring', 'effects': {'stat': 'AC', 'amount': 2},
                           'quiz_tier': 3, 'item_class': 'accessory'})
    Game._heal_accessory_id(old)
    assert old.id == 'ring_of_protection' and old.kind == 'protection'
    assert old.quiz_tier == 3 and old.ench_level == 5 and 'stat' not in old.effects


def test_secret_build_kits_use_living_items():
    import welcome_screen
    for name, b in welcome_screen.SECRET_BUILDS.items():
        acc = b.get('_start_accessory')
        if acc:
            assert acc in RAW, (name, acc)
    nz = welcome_screen.SECRET_BUILDS['friedrich nietzsche']
    assert '_start_accessory' not in nz
    gloves = items.instantiate_armor(*nz['_start_armor'][:2], level=1, ench_id=nz['_start_armor'][2])
    assert gloves.effects == {'stat': 'STR', 'amount': 1}


def test_the_bonnacon_drops_its_own_fireproof_hide():
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        spec = json.load(f)['bonnacon']['treasure']['unique_drop_id']
    _, tpl, mat, ench, lv = spec.split(':')
    cloak = items.instantiate_armor(tpl, mat, level=int(lv), ench_id=ench)
    assert cloak.ench_id == 'elementward' and cloak.quiz_tier == 2
