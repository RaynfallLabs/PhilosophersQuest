"""Armour, meals, the gates and the wanderer taper (2026-11-12).

ARMOUR_MEALS_GATES_REPORT_2026_11_12.md. Logic tests: the wanderer rate, the
armour spawn bells and the gate fights are deep or random, so they are held
here as rules on the data and the pure functions.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import floor_curve  # noqa: E402
import food_system  # noqa: E402
import gear  # noqa: E402
import items  # noqa: E402


# ------------------------------------------------------------ the wanderers

def test_wanderers_come_no_oftener_with_depth_and_taper_past_fifty():
    """Brandon: "Taper them". The old rule (22 - floor // 4) sent one every
    10 turns from floor 48: 60% of every deep fight."""
    iv = [floor_curve.wander_interval(f) for f in range(1, 101)]
    assert iv[0] == iv[49] == floor_curve.WANDER_EVERY == 22
    assert iv[99] == floor_curve.WANDER_EVERY_DEEP == 40
    assert all(b >= a for a, b in zip(iv, iv[1:]))


# ------------------------------------------------------------------ armour

def _templates_found(slot_or_shield: str, floor: int, n: int = 400) -> set:
    rng = random.Random(floor)
    out = set()
    for _ in range(n):
        if slot_or_shield == 'shield':
            it = items.pick_random_shield_for_floor(floor, rng)
        else:
            it = items.pick_random_armor_for_floor(floor, rng, slot=slot_or_shield)
        if it is not None:
            out.add(it.id[len(it.material) + 1:])     # id: "<material>_<template>"
    return out


def test_body_armour_and_shields_arrive_in_their_turn_down_the_run():
    """Brandon: "did we mess it up by making early armor too easy to get?"
    By weight class alone any heavy find from floor 12 could be full plate."""
    for tid in ('full_plate', 'plate', 'banded', 'splint', 'chainmail', 'breastplate', 'scale'):
        assert items.get_template('armor', tid).get('spawn_bell'), tid
    first = {t: items.get_template('armor', t)['spawn_bell'][2] for t in ('plate', 'full_plate')}
    assert _templates_found('body', first['plate'] - 1).isdisjoint({'plate', 'full_plate'})
    assert 'full_plate' not in _templates_found('body', first['full_plate'] - 1)
    assert 'full_plate' in _templates_found('body', 90)
    tower = items.get_template('shields', 'tower_shield')['spawn_bell'][2]
    assert 'tower_shield' not in _templates_found('shield', tower - 1)
    # a template with no bell of its own goes by its weight class
    helm = items.get_template('armor', 'plate_helm')
    assert 'spawn_bell' not in helm
    assert gear.template_weight(helm, 30) == gear.weight_class_weight(gear.weight_class(helm), 30)


def test_monster_to_hit_is_aimed_at_the_hero_the_game_makes():
    """The plain hero starts with a shortsword and no armour: AC 10, not the
    leather and shield (AC 7) the line once assumed."""
    import rebake_thac0
    assert rebake_thac0.START_AC == 10
    from player import Player
    p = Player()
    assert p.armor_slots[items.ARMOR_SLOTS.index('body')] is None and p.shield is None


def test_the_named_armour_floor_climbs_with_depth():
    for kind, top in (('body', 13), ('shield', 8)):
        assert gear.named_ac_floor(kind, 1) <= gear.named_ac_floor(kind, 50) \
            <= gear.named_ac_floor(kind, 100) <= top + 2


# ------------------------------------------------------------------- meals

def test_a_meal_heals_a_real_share_of_the_health_bar():
    """Brandon: "meals need to restore more health than they do now". A
    snack about a tenth, a feast about a third (it was 2% and 12%)."""
    snack, plain, feast = (food_system.meal_mend_share(h) for h in (3, 8, 22))
    assert 0.08 <= snack <= 0.12
    assert 0.14 <= plain <= 0.18
    assert 0.30 <= feast <= food_system.MEAL_SHARE_CAP <= 0.40
    assert food_system.meal_mend_share(100) == food_system.MEAL_SHARE_CAP


def test_a_cooked_meal_heals_at_least_its_share():
    """Any dish heals at least meal_mend_share of its written heal (a tier-5
    dish: 20 written, a third of the bar), and an HP dish its own share."""
    import kitchen
    from player import Player
    deep = next(r for r in kitchen.book() if kitchen.dish_tier(r) == 5
                and kitchen.dish_tab(r) == 'sp' and len(r['ingredients']) == 1)
    p = Player()
    p.max_hp = 300
    p.hp = 30
    food_system._apply_recipe_outcome(p, deep)
    assert p.hp - 30 >= int(round(food_system.meal_mend_share(20) * 300))
    hp_dish = kitchen.recipe('cook_titan')       # Titan Haunch Roast: HP, tier 4
    q = Player()
    q.max_hp = 300
    q.hp = 30
    food_system._apply_recipe_outcome(q, hp_dish)
    assert q.hp - 30 >= int(round(kitchen.dish_outcome(hp_dish)['heal_share'] * 300))


# ------------------------------------------------------------------- gates

def test_the_gate_bosses_hit_harder_down_the_run():
    """Asterion an accomplishment, Fafnir about right, Fenrir harder,
    Abaddon brutal without Michael: each gate's hardest blow is above the
    one before it (Fenrir's bite the hardest of all), and the data's HP is
    what respawn_by_hp says it should be."""
    import respawn_by_hp as R
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        d = json.load(f)
    top = {k: max(R.dice_avg(a['damage']) for a in d[k]['attacks'])
           for k in ('asterion_minotaur', 'fafnir_dragon', 'fenrir_wolf', 'abaddon_destroyer')}
    assert top['asterion_minotaur'] >= 15
    assert top['asterion_minotaur'] < top['fafnir_dragon'] < top['fenrir_wolf']
    assert top['abaddon_destroyer'] > top['fafnir_dragon']
    for k, hp in R.GATE_BOSS_HP.items():
        assert abs(R.dice_avg(d[k]['hp']) - hp) <= 0.03 * hp, k
